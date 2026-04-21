# WeGlide — Home Assistant Integration

Tracks gliding statistics and last flight details for one or more [WeGlide](https://weglide.org) users.

## Installation via HACS

1. Open HACS → **Integrations**
2. Click ⋮ → **Custom repositories**
3. Add `https://github.com/Bayyo1337/ha-weglide`, category: **Integration**
4. Search for **WeGlide** and click **Download**
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Add Integration** → search for **WeGlide**

## Features

- Track one or multiple WeGlide users per config entry
- Each tracked user gets its own HA device with 18 sensors
- Profile stats: total flights, distance, flight time, average speed
- Last flight: date, distance, points, duration, aircraft, takeoff/landing airport, copilot, launch type

## Configuration

| Field | Description |
|---|---|
| E-Mail | Your WeGlide login email |
| Password | Your WeGlide password |
| User IDs | Comma-separated WeGlide user IDs to track (your own ID is pre-filled) |
| Scan interval | Update interval in minutes (default: 30) |
