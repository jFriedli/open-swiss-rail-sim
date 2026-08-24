# Data provenance

| Dataset | Publisher | Source/terms | Downloaded | Extent | Processing | Distributed |
|---|---|---|---|---|---|---|
| OpenStreetMap railway infrastructure | OpenStreetMap contributors | Overpass API; ODbL 1.0; attribution: © OpenStreetMap contributors | 2026-08-24 | Rapperswil–Uznach candidate bbox | route graph, Dijkstra path, local projection, signal/station matching, speed-section extraction | derived compact JSON |
| swissALTI3D elevation | Federal Office of Topography swisstopo | geo.admin.ch height service; Swiss federal open government data terms; attribution: © swisstopo | 2026-08-24 | 13.47 km route, seven cross-track samples to ±1.2 km | LV95 height queries, local origin subtraction, triangular corridor mesh | sampled/derived JSON |

The runtime package is `public/data/rapperswil-uznach`. OSM geometry and attributes are open-mapping observations, not authoritative railway operational records. The rendered spline, gradient and terrain triangles are derived. Signal aspects, block authority, dynamics, scoring and energy are simulated.

No raw national dataset is committed. Cached requests live below ignored `data/intermediate/`.

