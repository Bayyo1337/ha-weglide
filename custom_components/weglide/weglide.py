"""Pure aiohttp API client for WeGlide — no HA imports."""

from __future__ import annotations

import logging
import time
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://api.weglide.org"
_CLIENT_ID = "hhUwyOpRS1SXlPryZTc7sLE2"
_SCOPE = "declare upload"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Origin": "https://weglide.org",
    "Referer": "https://weglide.org/",
}


def _multipart(fields: dict[str, str]) -> aiohttp.FormData:
    form = aiohttp.FormData()
    for key, value in fields.items():
        form.add_field(key, value)
    return form


class WeGlideAuthError(Exception):
    """Raised when authentication fails."""


class WeGlideClient:
    """Async WeGlide API client."""

    def __init__(self, email: str, password: str) -> None:
        self._email = email
        self._password = password
        self._token: str | None = None
        self._token_expiry: float = 0.0

    async def _get_token(self, session: aiohttp.ClientSession) -> str:
        """Return cached token or fetch a new one."""
        if self._token and time.monotonic() < self._token_expiry:
            return self._token

        form = _multipart({
            "grant_type": "password",
            "username": self._email,
            "password": self._password,
            "client_id": _CLIENT_ID,
            "scope": _SCOPE,
        })
        async with session.post(
            f"{BASE_URL}/v1/auth/token", data=form, headers=_HEADERS
        ) as resp:
            if resp.status == 403:
                body = await resp.text()
                _LOGGER.warning(
                    "WeGlide auth blocked (403) — server rejected the request. "
                    "Body: %s", body[:500]
                )
                raise WeGlideAuthError("Request blocked (403)")
            if resp.status in (400, 401):
                body = await resp.text()
                _LOGGER.warning(
                    "WeGlide auth failed (HTTP %s). Body: %s", resp.status, body[:500]
                )
                raise WeGlideAuthError(f"Invalid credentials (HTTP {resp.status})")
            if not resp.ok:
                body = await resp.text()
                _LOGGER.warning(
                    "WeGlide auth unexpected error (HTTP %s). Body: %s",
                    resp.status, body[:500]
                )
                resp.raise_for_status()
            data = await resp.json()

        token: str = data["access_token"]
        self._token = token
        self._token_expiry = time.monotonic() + data["expires_in"] - 60
        return token

    async def _get(
        self, session: aiohttp.ClientSession, path: str
    ) -> Any:
        token = await self._get_token(session)
        headers = {**_HEADERS, "Authorization": f"Bearer {token}"}
        async with session.get(f"{BASE_URL}{path}", headers=headers) as resp:
            if resp.status == 401:
                # Token may have been revoked — force re-auth once
                self._token = None
                token = await self._get_token(session)
                headers = {**_HEADERS, "Authorization": f"Bearer {token}"}
                async with session.get(
                    f"{BASE_URL}{path}", headers=headers
                ) as resp2:
                    resp2.raise_for_status()
                    return await resp2.json()
            resp.raise_for_status()
            return await resp.json()

    async def validate(self, session: aiohttp.ClientSession) -> bool:
        """Return True if credentials are valid."""
        try:
            await self._get_token(session)
            return True
        except WeGlideAuthError as err:
            _LOGGER.warning("WeGlide credential validation failed: %s", err)
            return False
        except aiohttp.ClientError as err:
            _LOGGER.warning("WeGlide connection error during validation: %s", err)
            return False

    async def get_me(self, session: aiohttp.ClientSession) -> dict:
        """Return the authenticated user's profile."""
        return await self._get(session, "/v1/user/me")

    async def get_user(self, session: aiohttp.ClientSession, user_id: int) -> dict:
        """Return a public user profile."""
        return await self._get(session, f"/v1/user/{user_id}")

    async def get_last_flight(
        self, session: aiohttp.ClientSession, user_id: int
    ) -> dict | None:
        """Return the most recent flightdetail for a user, or None."""
        flights = await self._get(
            session,
            f"/v1/flight?user_id_in={user_id}&order_by=-scoring_date&limit=1",
        )
        if not isinstance(flights, list) or not flights:
            return None

        flight_id = flights[0]["id"]
        return await self._get(session, f"/v1/flightdetail/{flight_id}")

    async def get_active_flight(
        self, session: aiohttp.ClientSession, user_id: int
    ) -> dict | None:
        """Return the in-progress flight list entry for today, or None.

        Active flights have no scoring_date yet, so scoring_date filters would
        exclude them entirely. Query by takeoff_time instead and confirm the
        flight started today before returning it.
        Returns the raw flight list entry — NOT flightdetail — because flightdetail
        may return 404 for flights that are still in progress.
        """
        from datetime import date as _date
        today = _date.today().isoformat()
        flights = await self._get(
            session,
            f"/v1/flight?user_id_in={user_id}&order_by=-takeoff_time&limit=5",
        )
        if not isinstance(flights, list):
            return None
        for flight in flights:
            takeoff = flight.get("takeoff_time") or ""
            if flight.get("landing_time") is None and takeoff.startswith(today):
                return flight
        return None
