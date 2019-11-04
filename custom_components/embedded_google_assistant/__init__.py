"""Embedded Google Assistant component"""

from .const import DOMAIN, DATA_ASSISTANT
from .assistant import Assistant
from . import config_flow, http, services, sensor

async def async_setup(hass, config):
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][DATA_ASSISTANT] = Assistant()
    return await http.async_setup(hass, config)

async def async_setup_entry(hass, entry):
    hass.async_add_job(hass.config_entries.async_forward_entry_setup(
            entry, 'sensor'))
    return await services.async_setup_entry(hass, entry)

async def async_remove_entry(hass, entry) -> None:
    return await config_flow.async_step_remove(hass, entry)