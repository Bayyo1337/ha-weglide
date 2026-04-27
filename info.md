## WeGlide — Home Assistant Integration

Tracks gliding statistics and last flight details for one or more [WeGlide](https://weglide.org) users.

### Features

- Track one or multiple WeGlide users per config entry
- Each tracked user gets its own HA device with 18 sensors
- Profile stats: total flights, distance, flight time, average speed
- Last flight: date, distance, points, duration, aircraft, takeoff/landing airport, copilot, launch type

### Configuration

| Field | Description |
|---|---|
| E-Mail | Your WeGlide login email |
| Password | Your WeGlide password |
| User IDs | Comma-separated WeGlide user IDs to track (your own ID is pre-filled). Example: `33337, 1307` |
| Scan interval | Update interval in minutes (default: 30) |

Find any user's ID in their profile URL: `weglide.org/user/33337`
