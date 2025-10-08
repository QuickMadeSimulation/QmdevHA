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
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:  # 仅类型检查时导入，运行时避免依赖
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_ZMQ_SUB_ENDPOINT,
)

PLATFORMS: list[str] = []

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: Any, config: dict[str, Any]) -> bool:
    return True


async def _run_zmq_bridge_task(hass: Any, entry: Any) -> None:
    from .bridge import ZmqBridge

    bridge = ZmqBridge(
        hass=hass,
        zmq_sub_endpoint=entry.data[CONF_ZMQ_SUB_ENDPOINT],
    )
    try:
        await bridge.run(hass)
    except asyncio.CancelledError:
        _LOGGER.debug("ZMQ bridge task cancelled")
        raise
    except Exception:  # noqa: BLE001
        _LOGGER.exception("ZMQ bridge task crashed")


async def async_setup_entry(hass: Any, entry: Any) -> bool:
    hass.data.setdefault(DOMAIN, {})
    task = hass.loop.create_task(_run_zmq_bridge_task(hass, entry))
    hass.data[DOMAIN][entry.entry_id] = task
    return True


async def async_unload_entry(hass: Any, entry: Any) -> bool:
    task: asyncio.Task | None = hass.data[DOMAIN].pop(entry.entry_id, None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    return True


