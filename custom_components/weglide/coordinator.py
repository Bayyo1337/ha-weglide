"""DataUpdateCoordinator for a single WeGlide user."""

from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .weglide import WeGlideClient

_LOGGER = logging.getLogger(__name__)


class WeGlideCoordinator(DataUpdateCoordinator[dict]):
    """Fetch profile + last flight for one tracked user."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: WeGlideClient,
        user_id: int,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"weglide_{user_id}",
            update_interval=timedelta(minutes=scan_interval),
        )
        self.client = client
        self.user_id = user_id

    async def _async_update_data(self) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                user = await self.client.get_user(session, self.user_id)
                last_flight = await self.client.get_last_flight(session, self.user_id)
                active_flight = await self.client.get_active_flight(session, self.user_id)
        except Exception as err:
            raise UpdateFailed(f"WeGlide update failed for user {self.user_id}: {err}") from err

        return {"user": user, "last_flight": last_flight, "active_flight": active_flight}
