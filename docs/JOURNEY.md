# Journey scenario

The scenario uses official Swiss static timetable feed `GTFS_FP2026_20260822.zip`, published by Geschäftsstelle SKI on behalf of BAV. Calendar validation selects active Saturday S17 trip `.ojp-91-17-M.1.TA.200.j26` (trip 12353), Rapperswil–Uznach, with planned calls at 14:03, 14:05, 14:11, and 14:14.

Required calls are Rapperswil SG (departure), Blumenau, Schmerikon, and Uznach. Each is matched to an OpenStreetMap platform; target points are derived from platform extent, train length, and travel direction. A stop is accepted below 0.5 km/h within ±10 m (perfect ±2 m, good ±5 m). Intermediate/final dwell is 12 seconds, during which traction is inhibited. Passing 15 m beyond the platform end records a miss without teleporting the train.

The deterministic journey state emits approach, arrival, miss, dwell-complete, signal-pass, and route-complete events. Station points combine stopping error and schedule deviation. The result panel reports completed/missed calls and cumulative station points. Player time, arrivals, doors/dwell, score, and completion are simulated.

The minimap is a local Canvas rendering of the same OSM route, roads, water, and station geometry already distributed with the corridor. It has no external tile requests, API key, or network failure mode. Its train marker is sampled directly from the canonical route frame; the north-up map projection uses the shared local LV95-derived metre coordinates.
