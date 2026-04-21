# weglide — Claude Code guidance

Bindet die WeGlide-Plattform (Gleitschirm- und Segelflug-Logbuch & Wertung) in Home Assistant ein.

## Dateistruktur

| Datei | Rolle |
|---|---|
| `weglide.py` | Purer aiohttp API-Client, keine HA-Imports |
| `coordinator.py` | `DataUpdateCoordinator` — ein Coordinator pro getracktem User |
| `sensor.py` | 18 Sensoren pro Device (Profil + letzter Flug) |
| `config_flow.py` | 2-Step Setup + OptionsFlow |
| `const.py` | Konstanten und Defaults |
| `API.md` | Vollständige Endpoint-Referenz (verifiziert) |
| `weglide-api.json` | Originale OpenAPI 3.1.0 Spezifikation |

## Architektur

- **1 Config Entry** = 1 WeGlide-Account (Email + Passwort)
- **1 Device pro getracktem User** — User-IDs kommagetrennt in `tracked_user_ids`
- **1 Coordinator pro User** — pollt `GET /v1/user/{id}` + letzten Flug
- `hass.data[DOMAIN][entry_id]` = `{user_id: WeGlideCoordinator, ...}`

## Auth

- `POST /v1/auth/token` — multipart/form-data
- `client_id`: `hhUwyOpRS1SXlPryZTc7sLE2`
- Token läuft nach 10 Tagen ab, wird im Client gecacht
- **User-Agent muss Browser-String sein** — WeGlide-Server blockt sonst mit 403

## Releases und Versioning

- Jede Änderung die in HACS-Instanzen ankommen soll, braucht ein **GitHub Release** mit einem Versions-Tag (z.B. `v1.0.1`)
- Die Version im Release-Tag muss mit `manifest.json` → `version` übereinstimmen
- **Vor jedem Release `manifest.json` aktualisieren**

### Breaking Changes

Breaking Changes sind Änderungen, die eine manuelle Aktion vom Nutzer erfordern:

| Art | Beispiele | Was tun |
|---|---|---|
| Config-Schema-Änderung | Neues Pflichtfeld, umbenanntes Feld | Config Flow `VERSION` erhöhen + Migration schreiben (`async_migrate_entry`) |
| Neue `unique_id`-Struktur | Sensor-IDs ändern sich | Alle bestehenden Entitäten werden als neu angelegt — in Release-Notes dokumentieren |
| Entität entfernt/umbenannt | Sensor gelöscht oder key geändert | In Release-Notes: "Entität X entfernt, bitte Automationen anpassen" |
| Neue Pflicht-Abhängigkeit | Neues `requirements`-Eintrag | Neuinstallation/Reload nötig — in Release-Notes vermerken |

### Release-Checkliste

1. `manifest.json` → `version` erhöhen (SemVer: `MAJOR.MINOR.PATCH`)
2. Bei Breaking Changes: `config_flow.py` → `VERSION` erhöhen + `async_migrate_entry` in `__init__.py`
3. GitHub Release erstellen mit Tag `v<version>`
4. Release-Notes schreiben — Breaking Changes **fett** markieren, nötige Nutzeraktionen explizit nennen

### Wann ist ein Reload nötig?

- Neue Sensoren hinzugefügt → Reload der Integration reicht
- Config-Schema geändert → Neu einrichten (oder Migration)
- `requirements` geändert → HA-Neustart nötig

## Siehe auch

- `API.md` — Endpoint-Referenz mit verifizierten Parametern und Einheiten
