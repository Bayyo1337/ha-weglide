# weglide — Claude Code guidance

Bindet die WeGlide-Plattform (Gleitschirm- und Segelflug-Logbuch & Wertung) in Home Assistant ein. WeGlide ist eine REST-API (OpenAPI 3.1.0). Die vollständige API-Spezifikation liegt als `weglide-api.json` im gleichen Ordner.

## Status

Scaffold angelegt (`manifest.json`, `__init__.py`). API analysiert, Dokumentation in `API.md`. Implementierung noch nicht begonnen.

## Geplante Architektur (noch nicht umgesetzt)

Analog zu `../karlsruhe_termin`:

| Datei | Rolle |
|---|---|
| `weglide.py` | Purer aiohttp API-Client, keine HA-Imports |
| `coordinator.py` | `DataUpdateCoordinator` — pollt Nutzerdaten + letzten Flug |
| `sensor.py` | Sensoren (Gesamtflüge, Gesamtdistanz, letzter Flug, ...) |
| `config_flow.py` | Setup-UI (Email + Passwort, live Validierung) |
| `const.py` | Konstanten und Defaults |

## API-Zusammenfassung

- **Base URL**: `https://api.weglide.org` (noch zu verifizieren)
- **Auth**: `POST /v1/auth/token` → Bearer Token (genaues Body-Format noch ungeklärt)
- **Nutzer**: `GET /v1/user/me` — flight_count, total_free_distance, total_flight_duration, avg_speed
- **Flüge**: `GET /v1/flight?user_id_in=<id>&order_by=-scoring_date&limit=1` — letzter Flug
- **Flugdetail**: `GET /v1/flightdetail/{id}` — Punkte, Distanz, Zeit, Flugzeug

Vollständige Endpoint-Liste und Schema-Details → `API.md`

## Kandidaten für HA-Sensoren

| Sensor | Quelle | Einheit |
|---|---|---|
| Gesamtanzahl Flüge | `user.flight_count` | Flüge |
| Gesamtdistanz | `user.total_free_distance` | km |
| Gesamtflugzeit | `user.total_flight_duration` | h (Einheit prüfen) |
| Letzter Flug — Datum | `flight.scoring_date` | date |
| Letzter Flug — Punkte | `flight.sorted_contest[0].points` | Punkte |
| Letzter Flug — Distanz | `flight.sorted_contest[0].distance` | km |
| Letzter Flug — Flugzeug | `flight.aircraft.name` | — |

## Offene Fragen vor Implementierung

1. Auth-Body-Format für `/v1/auth/token` klären (Browser-DevTools)
2. Base URL verifizieren
3. Einheit von `total_flight_duration` klären
4. Token-Gültigkeitsdauer — re-auth bei 401 oder proaktiv?

## Siehe auch

- `API.md` — vollständige Endpoint-Referenz mit Parametern und Schemas
- `weglide-api.json` — originale OpenAPI 3.1.0 Spezifikation
