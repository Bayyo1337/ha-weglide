"""Config flow for WeGlide integration."""

from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_TRACKED_USER_IDS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .weglide import WeGlideAuthError, WeGlideClient


def _parse_ids(raw: str) -> list[int]:
    return [int(s.strip()) for s in raw.split(",") if s.strip().isdigit()]


class WeGlideConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the setup UI."""

    VERSION = 1

    def __init__(self) -> None:
        self._email: str = ""
        self._password: str = ""
        self._own_user_id: int | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> WeGlideOptionsFlow:
        return WeGlideOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip()
            password = user_input[CONF_PASSWORD]

            try:
                async with aiohttp.ClientSession() as session:
                    client = WeGlideClient(email, password)
                    if not await client.validate(session):
                        errors["base"] = "invalid_auth"
                    else:
                        me = await client.get_me(session)
                        self._own_user_id = me["id"]
                        self._email = email
                        self._password = password
                        return await self.async_step_tracked_users()
            except WeGlideAuthError:
                errors["base"] = "invalid_auth"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_tracked_users(
        self, user_input: dict | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        default_ids = str(self._own_user_id) if self._own_user_id else ""

        if user_input is not None:
            ids = _parse_ids(user_input[CONF_TRACKED_USER_IDS])
            if not ids:
                errors[CONF_TRACKED_USER_IDS] = "invalid_user_id"
            else:
                names: list[str] = []
                try:
                    async with aiohttp.ClientSession() as session:
                        client = WeGlideClient(self._email, self._password)
                        for uid in ids:
                            user = await client.get_user(session, uid)
                            names.append(user["name"])
                except Exception:
                    errors["base"] = "invalid_user_id"

                if not errors:
                    title = ", ".join(names)
                    await self.async_set_unique_id(self._email.lower())
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"WeGlide — {title}",
                        data={
                            CONF_EMAIL: self._email,
                            CONF_PASSWORD: self._password,
                            CONF_TRACKED_USER_IDS: ",".join(str(i) for i in ids),
                            CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                        },
                    )

        return self.async_show_form(
            step_id="tracked_users",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TRACKED_USER_IDS, default=default_ids): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): vol.All(int, vol.Range(min=5, max=1440)),
                }
            ),
            errors=errors,
        )


class WeGlideOptionsFlow(config_entries.OptionsFlow):
    """Allow changing tracked users and scan interval."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    def _current(self, key: str, default):
        return self._entry.options.get(key, self._entry.data.get(key, default))

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            ids = _parse_ids(user_input[CONF_TRACKED_USER_IDS])
            if not ids:
                errors[CONF_TRACKED_USER_IDS] = "invalid_user_id"
            else:
                try:
                    async with aiohttp.ClientSession() as session:
                        client = WeGlideClient(
                            self._entry.data[CONF_EMAIL],
                            self._entry.data[CONF_PASSWORD],
                        )
                        for uid in ids:
                            await client.get_user(session, uid)
                except Exception:
                    errors["base"] = "invalid_user_id"

                if not errors:
                    return self.async_create_entry(
                        title="",
                        data={
                            CONF_TRACKED_USER_IDS: ",".join(str(i) for i in ids),
                            CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                        },
                    )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_TRACKED_USER_IDS,
                        default=self._current(CONF_TRACKED_USER_IDS, ""),
                    ): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self._current(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): vol.All(int, vol.Range(min=5, max=1440)),
                }
            ),
            errors=errors,
        )
