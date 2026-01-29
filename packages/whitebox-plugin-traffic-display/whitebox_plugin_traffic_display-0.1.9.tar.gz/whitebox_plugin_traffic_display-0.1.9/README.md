# Whitebox Plugin - Traffic Display

This is a plugin for [whitebox](https://gitlab.com/whitebox-aero) that displays traffic on the map.

## Installation

Install the plugin to whitebox:

```
poetry add whitebox-plugin-traffic-display
```

## API

### Aircraft Lookup

Lookup aircraft information by ICAO24 address. Returns registration, aircraft type, operator, and more from OpenSky and OpenAircraftType databases.

**Direct endpoint:**
```
GET /plugin-views/whitebox_plugin_traffic_display/aircraft/lookup/?icao_addr=<icao_addr>
```

**Using helper (frontend):**
```javascript
const url = Whitebox.api.getPluginProvidedPath("traffic.aircraft-lookup");
const response = await Whitebox.api.client.get(url, { params: { icao_addr: "5055096" } });
```

**Parameters:**
- `icao_addr` - ICAO24 address in decimal (e.g., `5055096`) or hex (e.g., `4d2278`)

**Response:**
```json
{
  "found": true,
  "icao24": "4d2278",
  "aircraft": {
    "registration": "9H-TJD",
    "model": "Boeing 737-800",
    "operator": "Corendon Airlines",
    "typecode": "B738",
    ...
  },
  "type_info": {
    "manufacturer_name": "BOEING",
    "model": "737-800",
    ...
  }
}
```

## Additional Instructions

- [Plugin Development Guide](https://docs.whitebox.aero/plugin_guide/#plugin-development-workflow)
- [Plugin Testing Guide](https://docs.whitebox.aero/plugin_guide/#testing-plugins)
- [Contributing Guidelines](https://docs.whitebox.aero/development_guide/#contributing)
