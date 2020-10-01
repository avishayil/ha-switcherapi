"""
Custom integration to integrate switcherapi with Home Assistant.

For more details about this integration, please refer to
https://github.com/custom-components/switcherapi
"""
import asyncio
from datetime import timedelta
import logging
import requests
import json

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.switcherapi.const import (
    CONF_API_BASE_URL,
    CONF_API_PORT,
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
)

SCAN_INTERVAL = timedelta(minutes=5)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    api_base_url = entry.data.get(CONF_API_BASE_URL)
    api_port = entry.data.get(CONF_API_PORT)

    coordinator = SwitcherApiDataUpdateCoordinator(
        hass, api_base_url=api_base_url, api_port=api_port
    )
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator

    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )

    entry.add_update_listener(async_reload_entry)
    return True


def convert_state_to_bool(state):
    _LOGGER.debug('State is: ', state)
    if state == 'on':
        return True
    else:
        return False


class SwitcherApiDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass, api_base_url, api_port):
        """Initialize."""
        self.api_base_url = api_base_url
        self.api_port = api_port
        self.platforms = []
        self._http_session = requests.Session()
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self):
        """Update data via library."""
        try:
            url = self.api_base_url + ':' + self.api_port + '/switcher/get_state'
            result = self._http_session.get(url)
            if result.status_code != 200:
                _LOGGER.error('Switcher Login failed! Please check your container status!')
                _LOGGER.error(result.content)
                return False
            _LOGGER.debug('Switcher Login Success')
            return True
        except Exception as exception:
            raise UpdateFailed(exception)

    async def turn_on(self):
        try:
            url = self.api_base_url + ':' + self.api_port + '/switcher/turn_on'
            result = self._http_session.post(url)
            if result.status_code != 200:
                _LOGGER.error('Switcher Turn on failed! Please check your container status!')
                _LOGGER.error(result.content)
                return False
            _LOGGER.debug('Switcher Turn on Success')
            return True
        except Exception as exception:
            raise UpdateFailed(exception)

    async def turn_off(self):
        try:
            url = self.api_base_url + ':' + self.api_port + '/switcher/turn_off'
            result = self._http_session.post(url)
            if result.status_code != 200:
                _LOGGER.error('Switcher Turn off failed! Please check your container status!')
                _LOGGER.error(result.content)
                return False
            _LOGGER.debug('Switcher Turn off Success')
            return True
        except Exception as exception:
            raise UpdateFailed(exception)

    def get_state(self):
        try:
            url = self.api_base_url + ':' + self.api_port + '/switcher/get_state'
            result = self._http_session.get(url)
            if result.status_code != 200:
                _LOGGER.error('Switcher state retrieval failed! Please check your container status!')
                _LOGGER.error(result.content)
                return False
            _LOGGER.debug('Switcher state retrieval Succeeded')
            return convert_state_to_bool(json.loads(result.content)['state'])
        except Exception as exception:
            raise UpdateFailed(exception)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle removal of an entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
