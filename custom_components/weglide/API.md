# WeGlide API Reference

Source: `weglide-api.json` (OpenAPI 3.1.0, version 0.1.0, "Quantifying Airsports")

**Base URL**: `https://api.weglide.org`

---

## Authentifizierung

### Token ausstellen
```
POST /v1/auth/token
Content-Type: multipart/form-data
```

| Feld | Wert |
|---|---|
| `grant_type` | `password` |
| `username` | E-Mail-Adresse |
| `password` | Passwort |
| `client_id` | `hhUwyOpRS1SXlPryZTc7sLE2` |
| `scope` | `declare upload` |

Antwort:
```json
{
  "token_type": "Bearer",
  "access_token": "<token>",
  "expires_in": 864000,
  "refresh_token": "<refresh_token>",
  "scope": "declare upload"
}
```
Token-Gültigkeitsdauer: **10 Tage** (`864000` Sekunden). Refresh-Token vorhanden.

### Token widerrufen
```
POST /v1/auth/revoke
```
Kein Body, sendet vermutlich `Authorization: Bearer <token>`.

### Weitere Auth-Endpoints
| Endpoint | Beschreibung |
|---|---|
| `GET /v1/auth/authorize` | OAuth2 Authorization Code Flow |
| `POST /v1/auth/authorize` | OAuth2 Authorization Code Flow |
| `POST /v1/auth/logout` | Session beenden |
| `POST /v1/auth/recover-password/{email}` | Passwort-Reset anfordern |

---

## Benutzer

### Aktueller Nutzer
```
GET /v1/user/me
```
Vollständiges Profil des eingeloggten Nutzers. Wichtige Felder aus dem `UserInDB`-Schema:

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | int | Nutzer-ID |
| `name` | str | Anzeigename |
| `flight_count` | int | Gesamtanzahl Flüge |
| `story_count` | int | Anzahl Stories |
| `total_free_distance` | float | Gesamtdistanz (km) |
| `total_flight_duration` | float | Gesamtflugzeit (Einheit unklar — vermutlich Sekunden) |
| `avg_speed` | float | Durchschnittsgeschwindigkeit |
| `avg_glide_speed` | float | Gleitgeschwindigkeit |
| `avg_glide_detour` | float | Gleitweg-Umweg |
| `home_airport` | object | Heimatflugplatz |
| `club` | object | Verein |
| `date_joined` | datetime | Beitrittsdatum |

```
GET /v1/user/me/simple
```
Vereinfachtes Profil (für Live-Kommentare genutzt).

### Nutzer nach ID
```
GET /v1/user/{user_id}
```
Öffentliches Profil (Schema `User` — wie `UserInDB` aber ohne `date_of_birth`, `email` etc.).

---

## Flüge

### Flugliste
```
GET /v1/flight
```
Sehr flexibel filterbar. Für einen bestimmten Nutzer:
```
GET /v1/flight?user_id_in=<id>&order_by=-scoring_date&limit=25
```

Wichtige Query-Parameter:
| Parameter | Beschreibung |
|---|---|
| `user_id_in` | Kommagetrennte Nutzer-IDs |
| `scoring_date_start` | Von Datum (date) |
| `scoring_date_end` | Bis Datum (date) |
| `season_in` | Saison(en) |
| `order_by` | Sortierung (z.B. `-scoring_date`) |
| `skip` | Offset für Pagination |
| `limit` | Anzahl Ergebnisse |
| `include_story` | Boolean, Stories mitladen |
| `include_stats` | Boolean, Statistiken mitladen |

### Flugdetail
```
GET /v1/flightdetail/{flight_id}
```
Schema `FlightDetail`:

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | int | Flug-ID |
| `takeoff_time` | datetime | Startzeit |
| `landing_time` | datetime | Landezeit |
| `scoring_date` | date | Wertungsdatum |
| `aircraft` | object | Flugzeug |
| `sorted_contest` | array | Wertungsergebnisse (free, FAI, etc.) |
| `task_score` | array | Aufgaben-Wertungen |
| `achievement` | array | Errungenschaften dieses Flugs |
| `airspace_violation` | array | Luftraumverletzungen |
| `igc_file` | object | IGC-Datei-Info |
| `bbox` | array[float] | Bounding Box [lon_min, lat_min, lon_max, lat_max] |

`sorted_contest[0]` ist üblicherweise die Hauptwertung:
- `points`: Punktzahl
- `distance`: Distanz (km)
- `speed`: Geschwindigkeit (km/h)
- `edited_name`: Wertungsname (z.B. "free distance")

### Feed
```
GET /v1/flight/feed?skip=0
```
Soziale Timeline (Flüge von gefolgten Nutzern). Pagination per `skip` (Vielfaches von 25).

### Aktivität
```
GET /v1/flight/activity?season=<year>
```
Flugaktivität für eine Saison (Jahr).

### Flugtag
```
GET /v1/flightday?scoring_date=<YYYY-MM-DD>
```
Alle Flüge eines bestimmten Tages.

---

## Flugzeug
```
GET /v1/aircraft/{id}?season=<year>&contest=free
GET /v1/aircraft/simple/{id}
GET /v1/aircraft
```
Schema `Aircraft`: id, name, double_seater, kind, sc_class, vintage, manufacturer, valid_igc_index, valid_dmst_index

---

## Errungenschaften
```
GET /v1/achievement/user/{user_id}
```
Array von `AchievementWithBadge`:
- `badge_id`, `points`, `value`, `flight_id`, `created`
- `badge`: Badge-Objekt

---

## Benachrichtigungen
```
GET /v1/notification
```
Benachrichtigungen des eingeloggten Nutzers (Schema nicht spezifiziert).

---

## Task / Aufgaben
```
GET /v1/task/score/recent   — Letzte Aufgabenwertungen
GET /v1/task/score          — Aufgabenwertungen mit Filtern
GET /v1/task/competitions/today — Heutige Wettbewerbe
```

---

## Suche
```
POST /v1/search
```
Globale Suche (Nutzer, Flugplätze, Flugzeuge etc.).

---

## Ranking
```
POST /v1/ranking
```
Ranglisten-Abfragen.

---

## Verifizierte Abweichungen vom OpenAPI-Spec

| Spec sagt | Realität |
|---|---|
| `sorted_contest` (array) im flightdetail | Feld heißt `contest` (array) |
| `contest` nicht im Feed-Flug | Feed-Flug hat `contest` als **Objekt** (kein Array) |

## Einheiten (verifiziert)

| Feld | Einheit |
|---|---|
| `total_free_distance` | km |
| `total_flight_duration` | Sekunden |
| `avg_speed` | km/h |
| `total_seconds` (flightdetail) | Sekunden |
| `contest.distance` | km |
| `contest.speed` | km/h |

## Offene Fragen

- **Refresh-Token-Endpoint**: Vermutlich `POST /v1/auth/token` mit `grant_type=refresh_token`.
- **Live-Tracking**: Kein Live-Tracking-Endpoint sichtbar — vermutlich separater WebSocket-Service.
