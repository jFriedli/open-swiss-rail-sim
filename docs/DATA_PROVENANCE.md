# Data provenance

| Dataset | Publisher | Source/terms | Downloaded | Extent | Processing | Distributed |
|---|---|---|---|---|---|---|
| OpenStreetMap railway infrastructure | OpenStreetMap contributors | Overpass API; ODbL 1.0; attribution: © OpenStreetMap contributors | 2026-08-24 | Rapperswil–Uznach candidate bbox | route graph, Dijkstra path, local projection, signal/station matching, speed-section extraction | derived compact JSON |
| swissALTI3D elevation | Federal Office of Topography swisstopo | geo.admin.ch height service; Swiss federal open government data terms; attribution: © swisstopo | 2026-08-24 | 15.225 × 3.525 km terrain extent plus 13.47 km route | LV95 height queries; 300 m terrain sources bilinearly resampled to a 75 m regular grid; 25 m route samples median/Gaussian smoothed; derived railway cut/fill envelope | sampled/derived JSON |
| SWISSIMAGE orthophoto | Federal Office of Topography swisstopo | Official FSDI WMS `ch.swisstopo.swissimage`; swisstopo OGD terms; attribution: © swisstopo | 2026-08-24 | 15.225 × 3.525 km | Four exact LV95 WMS crops; downsampled from 0.1/0.25 m source to ~1.85 m/pixel; WebP quality 78; content-hashed filenames | derived WebP tiles |

The runtime package is `public/data/rapperswil-uznach`. OSM geometry and attributes are open-mapping observations, not authoritative railway operational records. The rendered spline, inferred lateral placement, vertical profile, ballast, terrain interpolation/triangles and catenary are derived. Signal aspects, block authority, dynamics, controller, scoring and energy are simulated.

No raw national dataset is committed. Cached requests live below ignored `data/intermediate/`.
