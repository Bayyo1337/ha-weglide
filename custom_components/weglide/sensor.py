"""Sensor platform for WeGlide integration."""

from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WeGlideCoordinator


def _parse_dt(raw: str | None) -> datetime | None:
    """Parse an ISO 8601 datetime string to a timezone-aware datetime."""
    if not raw:
        return None
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinators: dict[int, WeGlideCoordinator] = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []
    for coordinator in coordinators.values():
        entities += [
            # Profile sensors
            FlightCountSensor(coordinator),
            TotalDistanceSensor(coordinator),
            TotalFlightTimeSensor(coordinator),
            AvgSpeedSensor(coordinator),
            AvgGlideSpeedSensor(coordinator),
            ClubSensor(coordinator),
            # Last flight sensors
            LastFlightDateSensor(coordinator),
            LastFlightTakeoffTimeSensor(coordinator),
            LastFlightLandingTimeSensor(coordinator),
            LastFlightDistanceSensor(coordinator),
            LastFlightPointsSensor(coordinator),
            LastFlightContestTypeSensor(coordinator),
            LastFlightDurationSensor(coordinator),
            LastFlightSpeedSensor(coordinator),
            LastFlightAircraftSensor(coordinator),
            LastFlightTakeoffSensor(coordinator),
            LastFlightLandingSensor(coordinator),
            LastFlightCopilotSensor(coordinator),
            LastFlightLaunchKindSensor(coordinator),
            LastFlightMaxAltGainSensor(coordinator),
        ]
    async_add_entities(entities)


class _Base(CoordinatorEntity[WeGlideCoordinator], SensorEntity):
    def __init__(self, coordinator: WeGlideCoordinator) -> None:
        super().__init__(coordinator)
        self._user_id = coordinator.user_id

    @property
    def device_info(self) -> DeviceInfo:
        user = (self.coordinator.data or {}).get("user", {})
        return DeviceInfo(
            identifiers={(DOMAIN, str(self._user_id))},
            name=user.get("name", f"WeGlide User {self._user_id}"),
            manufacturer="WeGlide",
            configuration_url=f"https://weglide.org/user/{self._user_id}",
        )

    def _user(self) -> dict:
        return (self.coordinator.data or {}).get("user", {})

    def _flight(self) -> dict | None:
        return (self.coordinator.data or {}).get("last_flight")

    def _contest(self) -> dict:
        flight = self._flight()
        if not flight:
            return {}
        contest = flight.get("contest")
        if isinstance(contest, list):
            return contest[0] if contest else {}
        return contest or {}


# ── Profile sensors ────────────────────────────────────────────────────────────

class FlightCountSensor(_Base):
    _attr_icon = "mdi:airplane"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_flight_count"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Anzahl Flüge"

    @property
    def native_value(self) -> int | None:
        return self._user().get("flight_count")


class TotalDistanceSensor(_Base):
    _attr_icon = "mdi:map-marker-distance"
    _attr_native_unit_of_measurement = "km"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_total_distance"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Gesamtdistanz"

    @property
    def native_value(self) -> float | None:
        return self._user().get("total_free_distance")


class TotalFlightTimeSensor(_Base):
    _attr_icon = "mdi:clock-outline"
    _attr_native_unit_of_measurement = "h"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_total_flight_time"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Gesamtflugzeit"

    @property
    def native_value(self) -> float | None:
        secs = self._user().get("total_flight_duration")
        if secs is None:
            return None
        return round(secs / 3600, 2)


class AvgSpeedSensor(_Base):
    _attr_icon = "mdi:speedometer"
    _attr_native_unit_of_measurement = "km/h"

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_avg_speed"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Durchschnittsgeschwindigkeit"

    @property
    def native_value(self) -> float | None:
        return self._user().get("avg_speed")


class AvgGlideSpeedSensor(_Base):
    _attr_icon = "mdi:speedometer-slow"
    _attr_native_unit_of_measurement = "km/h"

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_avg_glide_speed"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Mittlere Gleitgeschwindigkeit"

    @property
    def native_value(self) -> float | None:
        return self._user().get("avg_glide_speed")


class ClubSensor(_Base):
    _attr_icon = "mdi:account-group"

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_club"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Verein"

    @property
    def native_value(self) -> str | None:
        club = self._user().get("club")
        return club.get("name") if club else None


# ── Last flight sensors ────────────────────────────────────────────────────────

class LastFlightDateSensor(_Base):
    _attr_icon = "mdi:calendar"
    _attr_device_class = SensorDeviceClass.DATE

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_last_flight_date"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Letzter Flug Datum"

    @property
    def native_value(self):
        flight = self._flight()
        if not flight:
            return None
        from datetime import date
        raw = flight.get("scoring_date")
        return date.fromisoformat(raw) if raw else None


class LastFlightTakeoffTimeSensor(_Base):
    _attr_icon = "mdi:airplane-takeoff"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_last_flight_takeoff_time"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Letzter Flug Startzeit"

    @property
    def native_value(self) -> datetime | None:
        flight = self._flight()
        return _parse_dt(flight.get("takeoff_time")) if flight else None


class LastFlightLandingTimeSensor(_Base):
    _attr_icon = "mdi:airplane-landing"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_last_flight_landing_time"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Letzter Flug Landezeit"

    @property
    def native_value(self) -> datetime | None:
        flight = self._flight()
        return _parse_dt(flight.get("landing_time")) if flight else None


class LastFlightDistanceSensor(_Base):
    _attr_icon = "mdi:ruler"
    _attr_native_unit_of_measurement = "km"

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_last_flight_distance"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Letzter Flug Distanz"

    @property
    def native_value(self) -> float | None:
        return self._contest().get("distance")


class LastFlightPointsSensor(_Base):
    _attr_icon = "mdi:trophy"

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_last_flight_points"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Letzter Flug Punkte"

    @property
    def native_value(self) -> float | None:
        return self._contest().get("points")


class LastFlightContestTypeSensor(_Base):
    _attr_icon = "mdi:format-list-bulleted"

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_last_flight_contest_type"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Letzter Flug Wertungstyp"

    @property
    def native_value(self) -> str | None:
        return self._contest().get("edited_name")


class LastFlightDurationSensor(_Base):
    _attr_icon = "mdi:timer"
    _attr_native_unit_of_measurement = "h"

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_last_flight_duration"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Letzter Flug Dauer"

    @property
    def native_value(self) -> float | None:
        flight = self._flight()
        if not flight:
            return None
        secs = flight.get("total_seconds")
        return round(secs / 3600, 2) if secs is not None else None


class LastFlightSpeedSensor(_Base):
    _attr_icon = "mdi:speedometer"
    _attr_native_unit_of_measurement = "km/h"

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_last_flight_speed"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Letzter Flug Geschwindigkeit"

    @property
    def native_value(self) -> float | None:
        return self._contest().get("speed")


class LastFlightAircraftSensor(_Base):
    _attr_icon = "mdi:airplane"

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_last_flight_aircraft"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Letzter Flug Flugzeug"

    @property
    def native_value(self) -> str | None:
        flight = self._flight()
        if not flight:
            return None
        aircraft = flight.get("aircraft")
        return aircraft.get("name") if aircraft else None


class LastFlightTakeoffSensor(_Base):
    _attr_icon = "mdi:airport"

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_last_flight_takeoff"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Letzter Flug Startplatz"

    @property
    def native_value(self) -> str | None:
        flight = self._flight()
        if not flight:
            return None
        ap = flight.get("takeoff_airport")
        if not ap:
            return None
        region = ap.get("region")
        return f"{ap['name']} ({region})" if region else ap["name"]


class LastFlightLandingSensor(_Base):
    _attr_icon = "mdi:airport"

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_last_flight_landing"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Letzter Flug Landeort"

    @property
    def native_value(self) -> str | None:
        flight = self._flight()
        if not flight:
            return None
        ap = flight.get("landing_airport")
        if not ap:
            return None
        region = ap.get("region")
        return f"{ap['name']} ({region})" if region else ap["name"]


class LastFlightCopilotSensor(_Base):
    _attr_icon = "mdi:account-multiple"

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_last_flight_copilot"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Letzter Flug Kopilot"

    @property
    def native_value(self) -> str | None:
        flight = self._flight()
        if not flight:
            return None
        co_user = flight.get("co_user")
        if co_user:
            return co_user.get("name")
        return flight.get("co_user_name")


class LastFlightLaunchKindSensor(_Base):
    _attr_icon = "mdi:rocket-launch"

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_last_flight_launch_kind"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Letzter Flug Startart"

    @property
    def native_value(self) -> str | None:
        flight = self._flight()
        return flight.get("launch_kind") if flight else None


class LastFlightMaxAltGainSensor(_Base):
    _attr_icon = "mdi:arrow-up-bold"
    _attr_native_unit_of_measurement = "m"

    @property
    def unique_id(self) -> str:
        return f"weglide_{self._user_id}_last_flight_max_alt_gain"

    @property
    def name(self) -> str:
        return f"{self._user().get('name', self._user_id)} Letzter Flug Max. Höhengewinn"

    @property
    def native_value(self) -> int | None:
        flight = self._flight()
        return flight.get("max_alt_gain") if flight else None
