"""WeGlide integration."""

from __future__ import annotations

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_TRACKED_USER_IDS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import WeGlideCoordinator
from .weglide import WeGlideClient


def _opt(entry: ConfigEntry, key: str, default):
    return entry.options.get(key, entry.data.get(key, default))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = WeGlideClient(
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
    )

    raw_ids = _opt(entry, CONF_TRACKED_USER_IDS, "")
    user_ids = [int(s.strip()) for s in raw_ids.split(",") if s.strip().isdigit()]
    scan_interval = _opt(entry, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinators: dict[int, WeGlideCoordinator] = {}
    async with aiohttp.ClientSession() as session:
        # Warm up token once so all coordinators share the cached token
        await client.validate(session)

    for user_id in user_ids:
        coordinator = WeGlideCoordinator(hass, client, user_id, scan_interval)
        await coordinator.async_config_entry_first_refresh()
        coordinators[user_id] = coordinator

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinators
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
