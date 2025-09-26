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

import voluptuous as vol
from homeassistant import config_entries

from .const import (
    DOMAIN,
    CONF_ZMQ_SUB_ENDPOINT,
    DEFAULT_TITLE,
)


class QmdevHAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):  # type: ignore[override]
        if user_input is not None:
            return self.async_create_entry(title=DEFAULT_TITLE, data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ZMQ_SUB_ENDPOINT): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema)


