from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_TOKEN, CONF_URL

from .const import (
    DOMAIN,
    CONF_LIGHT_ENTITY_ID,
    CONF_AC_ENTITY_ID,
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
                vol.Required(CONF_URL): str,
                vol.Required(CONF_TOKEN): str,
                vol.Required(CONF_LIGHT_ENTITY_ID): str,
                vol.Required(CONF_AC_ENTITY_ID): str,
                vol.Required(CONF_ZMQ_SUB_ENDPOINT): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema)


