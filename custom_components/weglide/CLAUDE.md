# weglide — Claude Code guidance

Bindet die WeGlide-Plattform (Segelflug-Logbuch & Wertung) in Home Assistant ein.

## Dateistruktur

| Datei | Rolle |
|---|---|
| `weglide.py` | Purer aiohttp API-Client, keine HA-Imports |
| `coordinator.py` | `DataUpdateCoordinator` — ein Coordinator pro getracktem User |
| `sensor.py` | 20 Sensoren pro Device (Profil + letzter Flug) |
| `binary_sensor.py` | 1 Binary Sensor pro Device (`Am Fliegen`) |
| `config_flow.py` | 2-Step Setup + OptionsFlow |
| `const.py` | Konstanten, Defaults, `PLATFORMS = ["sensor", "binary_sensor"]` |
| `API.md` | Vollständige Endpoint-Referenz (verifiziert) |
| `weglide-api.json` | Originale OpenAPI 3.1.0 Spezifikation |

## Architektur

- **1 Config Entry** = 1 WeGlide-Account (Email + Passwort)
- **1 Device pro getracktem User** — User-IDs kommagetrennt in `tracked_user_ids`
- **1 Coordinator pro User** — pollt drei Dinge:
  - `GET /v1/user/{id}` → Profil
  - `GET /v1/flight?order_by=-scoring_date&limit=1` + `GET /v1/flightdetail/{id}` → letzter abgeschlossener Flug
  - `GET /v1/flight?order_by=-created&limit=5` → aktiver Flug (kein Flugdetail!)
- `hass.data[DOMAIN][entry_id]` = `{user_id: WeGlideCoordinator, ...}`
- `coordinator.data` = `{"user": {...}, "last_flight": {...}|None, "active_flight": {...}|None}`

## Sensoren

### Profil (6 Sensoren)
| Sensor | Feld | Einheit |
|---|---|---|
| Anzahl Flüge | `flight_count` | — |
| Gesamtdistanz | `total_free_distance` | km |
| Gesamtflugzeit | `total_flight_duration` / 3600 | h |
| Durchschnittsgeschwindigkeit | `avg_speed` | km/h |
| Mittlere Gleitgeschwindigkeit | `avg_glide_speed` | km/h |
| Verein | `club.name` | — |

### Letzter Flug (14 Sensoren)
| Sensor | Feld | Hinweis |
|---|---|---|
| Datum | `scoring_date` | `SensorDeviceClass.DATE` |
| Startzeit | `takeoff_time` | `SensorDeviceClass.TIMESTAMP` |
| Landezeit | `landing_time` | `SensorDeviceClass.TIMESTAMP`, None wenn aktiv |
| Distanz | `contest.distance` | km |
| Punkte | `contest.points` | — |
| Wertungstyp | `contest.edited_name` | **Feld heißt `edited_name`, nicht `name`!** |
| Dauer | `total_seconds` / 3600 | h |
| Geschwindigkeit | `contest.speed` | km/h |
| Flugzeug | `aircraft.name` | — |
| Startplatz | `takeoff_airport.name` + `region` | — |
| Landeort | `landing_airport.name` + `region` | — |
| Kopilot | `co_user.name` oder `co_user_name` | — |
| Startart | `launch_kind` | Codes: T→Schlepp, W→Winde, S→Eigenstart |
| Max. Höhengewinn | `max_alt_gain` | m |

### Binary Sensor (1)
| Sensor | Logik |
|---|---|
| Am Fliegen | `active_flight is not None` — nutzt dedizierte `order_by=-takeoff_time`-Abfrage |

## Auth

- `POST /v1/auth/token` — multipart/form-data
- `client_id`: `hhUwyOpRS1SXlPryZTc7sLE2`
- Token läuft nach 10 Tagen ab, wird im Client gecacht
- **User-Agent muss Browser-String sein** — WeGlide-Server blockt sonst mit 403

## Bekannte Fallstricke / Spec-Abweichungen

| Problem | Ursache | Fix |
|---|---|---|
| `Am Fliegen` immer `Aus` trotz aktivem Flug | Aktive Flüge haben noch keine `scoring_date` → `scoring_date`-Filter schließt sie aus | Abfrage `order_by=-created&limit=5` (kein Datumsfilter) + Check `landing_time is None` + `takeoff_time` beginnt mit heute |
| `order_by=-takeoff_time` → 422 | Kein gültiges Sortierfeld laut OpenAPI-Spec (`FlightOrder` kennt nur `scoring_date`, `created`) | `order_by=-created` verwenden |
| Wertungstyp immer `unavailable` | Spec-Feld heißt `edited_name`, nicht `name` | `contest.get("edited_name")` |
| `flightdetail` ggf. 404 für aktive Flüge | Flug noch nicht finalisiert | Aktiv-Check nutzt Flugliste, NICHT `flightdetail` |
| `contest` vs `sorted_contest` | Spec sagt `sorted_contest`, API liefert `contest` | `flight.get("contest")` |
| Feed liefert `contest` als Objekt | Spec sagt Array | `_contest()` prüft `isinstance(contest, list)` |

## Releases und Versioning

- Jede Änderung die in HACS-Instanzen ankommen soll, braucht ein **GitHub Release** mit einem Versions-Tag (z.B. `v1.1.2`)
- Die Version im Release-Tag muss mit `manifest.json` → `version` übereinstimmen
- **Vor jedem Release `manifest.json` aktualisieren**
- Aktuelle Version: `1.1.2`

### Breaking Changes

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
