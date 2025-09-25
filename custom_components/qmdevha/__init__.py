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
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_TOKEN, CONF_URL

from .const import (
    DOMAIN,
    CONF_LIGHT_ENTITY_ID,
    CONF_AC_ENTITY_ID,
    CONF_ZMQ_SUB_ENDPOINT,
)

PLATFORMS: list[str] = []

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    return True


async def _run_zmq_bridge_task(hass: HomeAssistant, entry: ConfigEntry) -> None:
    from .bridge import ZmqBridge

    bridge = ZmqBridge(
        ha_base_url=entry.data[CONF_URL],
        ha_token=entry.data[CONF_TOKEN],
        light_entity_id=entry.data[CONF_LIGHT_ENTITY_ID],
        ac_entity_id=entry.data[CONF_AC_ENTITY_ID],
        zmq_sub_endpoint=entry.data[CONF_ZMQ_SUB_ENDPOINT],
    )
    try:
        await bridge.run(hass)
    except asyncio.CancelledError:
        _LOGGER.debug("ZMQ bridge task cancelled")
        raise
    except Exception:  # noqa: BLE001
        _LOGGER.exception("ZMQ bridge task crashed")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    task = hass.loop.create_task(_run_zmq_bridge_task(hass, entry))
    hass.data[DOMAIN][entry.entry_id] = task
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    task: asyncio.Task | None = hass.data[DOMAIN].pop(entry.entry_id, None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    return True


