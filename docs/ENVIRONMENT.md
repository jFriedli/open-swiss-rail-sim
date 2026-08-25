# Environment system

Every route uses one `EnvironmentState`; railway physics and operational logic do not inspect rendering toggles. The state contains an absolute Swiss civil datetime, interpolated route latitude/longitude/elevation, solar state, weather, wind, wetness and snow cover. The journey/AI clock remains authoritative. Debug `timescale` accelerates environmental presentation without changing the 120 Hz train integrator.

The sun uses the NOAA fractional-year equations for equation of time and solar declination. Azimuth is clockwise from north and elevation is above the astronomical horizon. Route WGS84 samples are interpolated at current chainage. The model recalculates at 1 Hz; lighting and precipitation interpolate each frame. Stages are continuous: day above 6°, golden hour down to −1°, civil twilight to −6°, then night.

Three.js consumes shared uniforms. A procedural dome blends night, twilight and daylight, suppresses subtle stars under cloud, and follows the camera. The solar directional light changes direction, colour and intensity; hemisphere intensity, exposure and fog respond to the same state. Custom deterministic query examples are:

```text
?debug=1&datetime=2026-08-22T20:45:00+02:00&weather=clear
?debug=1&datetime=2026-11-15T07:30:00+01:00&weather=rain
?debug=1&datetime=2026-01-15T16:30:00+01:00&weather=snow
```

Camera-local particle buffers contain 2,400 rain or 1,500 snow points. Inactive precipitation is hidden. Weather and astronomy update at low frequency; no materials are recreated when conditions change.

