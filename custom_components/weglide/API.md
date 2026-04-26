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
Token-Gültigkeitsdauer: **10 Tage** (`864000` Sekunden).

---

## Benutzer

### Aktueller Nutzer
```
GET /v1/user/me
```

### Nutzer nach ID
```
GET /v1/user/{user_id}
```
Schema `User` — wichtige Felder:

| Feld | Typ | Einheit |
|---|---|---|
| `id` | int | — |
| `name` | str | — |
| `flight_count` | int | — |
| `total_free_distance` | float | km |
| `total_flight_duration` | float | Sekunden |
| `avg_speed` | float | km/h |
| `avg_glide_speed` | float | km/h |
| `club` | object | → `club.name` |

---

## Flüge

### Flugliste
```
GET /v1/flight
```
Gibt `FlightRankList`-Objekte zurück (nicht `FlightDetail`!).

Wichtige Query-Parameter:
| Parameter | Beschreibung |
|---|---|
| `user_id_in` | Kommagetrennte Nutzer-IDs |
| `order_by` | `-scoring_date`, `-created` (valide Werte lt. OpenAPI-Spec; `-takeoff_time` → 422!) |
| `scoring_date_start` / `_end` | Datumsfilter |
| `limit` | Anzahl Ergebnisse |

**Wichtig:** Aktive WeGlide-Connect-Flüge haben noch keine `scoring_date`. Für Live-Erkennung `order_by=-takeoff_time` verwenden.

`FlightRankList`-Felder (relevant):
- `id`, `takeoff_time`, `landing_time`, `scoring_date`
- `contest` — **Objekt** (nicht Array wie in FlightDetail!)
- `landing_time` ist `null` solange der Flug läuft

### Flugdetail
```
GET /v1/flightdetail/{flight_id}
```
**Achtung:** Kann 404 liefern für Flüge die noch aktiv sind.

Schema `FlightDetail` (wichtige Felder):

| Feld | Typ | Hinweis |
|---|---|---|
| `takeoff_time` | datetime | ISO 8601 |
| `landing_time` | datetime | ISO 8601, in der Praxis `null` bei aktivem Flug |
| `scoring_date` | date | `null` bei aktivem Flug |
| `contest` | array | **Heißt `contest`, nicht `sorted_contest` wie im Spec!** |
| `total_seconds` | int | Flugdauer in Sekunden |
| `launch_kind` | str\|null | Codes: `T`=Schlepp, `W`=Winde, `S`=Eigenstart |
| `max_alt_gain` | int\|null | m |
| `takeoff_airport` | object\|null | `{name, region}` |
| `landing_airport` | object\|null | `{name}` (kein `region`!) |
| `aircraft` | object\|null | `{name, ...}` |
| `co_user` | object\|null | `{name, ...}` |
| `co_user_name` | str\|null | Fallback wenn kein WeGlide-Account |

`contest[0]` ist die Hauptwertung:
- `points`: Punktzahl
- `distance`: Distanz (km)
- `speed`: km/h
- `edited_name`: Wertungsname — **Feld heißt `edited_name`, nicht `name`!**

### Aktiven Flug erkennen
```
GET /v1/flight?user_id_in={id}&order_by=-created&limit=5
```
Über die letzten 5 Einträge iterieren: `landing_time is None` + `takeoff_time` beginnt mit heutigem Datum → Flug ist aktiv. Kein `flightdetail`-Call nötig (und riskant für aktive Flüge).

**Achtung:** `order_by=-takeoff_time` ist kein valides Sortierfeld → API antwortet mit 422. Valide Werte: `scoring_date`, `-scoring_date`, `created`, `-created`.

---

## Live-Tracking

### GPS-Positionen (Replay Bucket)
```
GET /v1/fix/batch?time=<unix_timestamp>
```
Gibt GPS-Positionen aller aktuell getrackten Flugzeuge für einen Zeitstempel zurück. Schema ist unspezifiziert (`{}`). Dient dem WeGlide-Kartenoverlay.

### Verbundene Geräte (authentifiziert)
```
GET /v1/device/connected
```
Listet alle Geräte die mit dem eingeloggten Account verbunden sind.

### Alle Geräte (OGN-Datenbank)
```
GET /v1/device
```
Gibt alle Geräte aus der OGN-Datenbank zurück (Schema `LiveDevice`):
- `id`, `registration`, `competition_id`
- `tracked`, `identified`, `excluded`
- `aircraft` → `{id, name, sc_class, kind}`

---

## Weitere Endpoints

| Endpoint | Beschreibung |
|---|---|
| `GET /v1/flightday?scoring_date=YYYY-MM-DD` | Alle Flüge eines Tages |
| `GET /v1/flight/feed?skip=0` | Soziale Timeline |
| `POST /v1/search` | Globale Suche |
| `GET /v1/achievement/user/{user_id}` | Errungenschaften |
| `GET /v1/notification` | Benachrichtigungen (auth) |

---

## Verifizierte Abweichungen vom OpenAPI-Spec

| Spec sagt | Realität |
|---|---|
| `sorted_contest` (array) im FlightDetail | Feld heißt `contest` (array) |
| `contest` nicht im Feed-Flug | Feed-Flug hat `contest` als **Objekt** (kein Array) |
| `contest.name` | Feld heißt `edited_name` |
| `landing_time` non-nullable | Ist `null` für aktive Flüge |
| `landing_airport` hat `region` | `AirportFlight` hat nur `id` + `name`, kein `region` |

## Einheiten (verifiziert)

| Feld | Einheit |
|---|---|
| `total_free_distance` | km |
| `total_flight_duration` | Sekunden |
| `avg_speed` | km/h |
| `total_seconds` (flightdetail) | Sekunden |
| `contest.distance` | km |
| `contest.speed` | km/h |
| `max_alt_gain` | m |
