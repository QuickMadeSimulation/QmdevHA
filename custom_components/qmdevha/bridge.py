# Copyright (C) 2025 Wei Shuai <cpuwolf@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import asyncio
import logging
import struct
from typing import Any

import aiohttp
import zmq
import zmq.asyncio

_LOGGER = logging.getLogger(__name__)


class ZmqBridge:
    def __init__(
        self,
        *,
        ha_base_url: str,
        ha_token: str,
        light_entity_id: str,
        ac_entity_id: str,
        zmq_sub_endpoint: str,
    ) -> None:
        self._ha_base_url = ha_base_url.rstrip("/")
        self._ha_token = ha_token
        self._light_entity_id = light_entity_id
        self._ac_entity_id = ac_entity_id
        self._zmq_sub_endpoint = zmq_sub_endpoint

        self._aiohttp: aiohttp.ClientSession | None = None
        self._ctx: zmq.asyncio.Context | None = None
        self._sock: zmq.asyncio.Socket | None = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._aiohttp is None or self._aiohttp.closed:
            self._aiohttp = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self._ha_token}",
                    "Content-Type": "application/json",
                }
            )
        return self._aiohttp

    async def _post(self, path: str, json: dict[str, Any]) -> None:
        session = await self._ensure_session()
        url = f"{self._ha_base_url}{path}"
        async with session.post(url, json=json, timeout=10) as resp:
            if resp.status >= 400:
                text = await resp.text()
                _LOGGER.error("HA API error %s: %s", resp.status, text)
                raise RuntimeError(text)

    async def _turn_on_light(self) -> None:
        await self._post("/api/services/switch/turn_on", {"entity_id": self._light_entity_id})

    async def _turn_off_light(self) -> None:
        await self._post("/api/services/switch/turn_off", {"entity_id": self._light_entity_id})

    async def _turn_on_ac(self) -> None:
        await self._post("/api/services/climate/set_hvac_mode", {"entity_id": self._ac_entity_id, "hvac_mode": "cool"})

    async def _turn_off_ac(self) -> None:
        await self._post("/api/services/climate/set_hvac_mode", {"entity_id": self._ac_entity_id, "hvac_mode": "off"})

    async def _open_socket(self) -> None:
        if self._ctx is None:
            self._ctx = zmq.asyncio.Context()
        self._sock = self._ctx.socket(zmq.SUB)
        self._sock.connect(self._zmq_sub_endpoint)
        self._sock.setsockopt_string(zmq.SUBSCRIBE, "")

    async def _close_socket(self) -> None:
        if self._sock is not None:
            self._sock.close(0)
            self._sock = None
        if self._ctx is not None:
            self._ctx.term()
            self._ctx = None

    async def _handle_pack_event(self, payload_bytes: bytes) -> None:
        if len(payload_bytes) < 1:
            return
        try:
            onoff = struct.unpack("?", payload_bytes[:1])[0]
        except Exception:
            _LOGGER.debug("failed to unpack pack event")
            return
        if onoff:
            await self._turn_on_ac()
        else:
            await self._turn_off_ac()

    async def _handle_key_event(self, payload_bytes: bytes) -> None:
        if len(payload_bytes) < 12:
            return
        try:
            qid, key, isrelease = struct.unpack("<iii", payload_bytes[:12])
        except Exception:
            _LOGGER.debug("failed to unpack key event")
            return
        if qid == 9 and key == 0x13:
            if isrelease:
                await self._turn_on_light()
            else:
                await self._turn_off_light()

    async def run(self, hass) -> None:
        await self._open_socket()
        last_heartbeat = hass.loop.time()
        heartbeat_timeout = 6.0

        try:
            while True:
                assert self._sock is not None
                poller = zmq.asyncio.Poller()
                poller.register(self._sock, zmq.POLLIN)
                events = dict(await poller.poll(timeout=1000))
                if self._sock in events and events[self._sock] == zmq.POLLIN:
                    frames: list[bytes] = [await self._sock.recv()]
                    while self._sock.getsockopt(zmq.RCVMORE):
                        frames.append(await self._sock.recv())

                    if frames and len(frames[0]) >= 8:
                        msg_id, payload_len = struct.unpack("<ii", frames[0][:8])
                        ZMQQHeartBeat_ID = 0x07324D6D
                        ZMQQ_KEYEVENT_ID = 0x07324D6E
                        ZMQQ_PACKEVENT_ID = 0x07324D6F
                        if msg_id == ZMQQHeartBeat_ID:
                            last_heartbeat = hass.loop.time()
                            continue

                        remaining = frames[0][8:]
                        payload = remaining[:payload_len] if len(remaining) >= payload_len else (remaining + b"".join(frames[1:]))[:payload_len]
                        if msg_id == ZMQQ_PACKEVENT_ID:
                            await self._handle_pack_event(payload)
                        elif msg_id == ZMQQ_KEYEVENT_ID:
                            await self._handle_key_event(payload)
                else:
                    if hass.loop.time() - last_heartbeat > heartbeat_timeout:
                        await self._close_socket()
                        await asyncio.sleep(0.5)
                        await self._open_socket()
                        last_heartbeat = hass.loop.time()
        finally:
            await self._close_socket()


