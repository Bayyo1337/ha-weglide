"""Binary sensor platform for WeGlide integration."""

from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import WeGlideCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinators: dict[int, WeGlideCoordinator] = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        IsCurrentlyFlyingSensor(coordinator)
        for coordinator in coordinators.values()
    ])


class IsCurrentlyFlyingSensor(CoordinatorEntity[WeGlideCoordinator], BinarySensorEntity):
    """True while the user is currently airborne (WeGlide Connect live flight)."""

    _attr_icon = "mdi:airplane-takeoff"

    def __init__(self, coordinator: WeGlideCoordinator) -> None:
        super().__init__(coordinator)
        self._user_id = coordinator.user_id

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_is_flying"

    @property
    def name(self) -> str:
        user = (self.coordinator.data or {}).get("user", {})
        return f"{user.get('name', self._user_id)} Am Fliegen"

    @property
    def device_info(self) -> DeviceInfo:
        user = (self.coordinator.data or {}).get("user", {})
        return DeviceInfo(
            identifiers={(DOMAIN, str(self._user_id))},
            name=user.get("name", f"WeGlide User {self._user_id}"),
            manufacturer="WeGlide",
            configuration_url=f"https://weglide.org/user/{self._user_id}",
        )

    @property
    def is_on(self) -> bool:
        """Return True if the user's last flight is still in progress today."""
        flight = (self.coordinator.data or {}).get("last_flight")
        if not flight:
            return False
        # A finished flight always has landing_time set
        if flight.get("landing_time") is not None:
            return False
        takeoff_raw = flight.get("takeoff_time")
        if not takeoff_raw:
            return False
        try:
            dt = datetime.fromisoformat(takeoff_raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt_util.as_local(dt).date() == dt_util.now().date()
        except (ValueError, AttributeError):
            return False
