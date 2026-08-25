# Generic route validation

Three materially different packages load through one engine and package schema. Rapperswil–Uznach remains the 13.47 km lakeside `FULL` showcase. Olten–Aarau is a 13.38 km busy multi-track test with 366 graph edges, 170 normalized branch/switch nodes, 37 accepted mapped signals and one official-timetable opposing service. Gümligen–Konolfingen is a 12.80 km curving, climbing regional test with four scheduled calls, 74 graph edges, 36 normalized branch/switch nodes, no usable mapped signals, eight explicit scenario signals and one official-timetable opposing service.

The latter routes are intentionally `PARTIAL`: official swissALTI3D terrain, SWISSIMAGE, OSM railway/platform topology and official GTFS are present, but swissBUILDINGS3D and the full water/road/forest render payload are not. Both passed schema, asset, browser loading and visual coordinate/alignment checks without hand-editing generated JSON.

| Route | Length | Calls | Edges | Player edges | Signals mapped/scenario | AI | Package |
|---|---:|---:|---:|---:|---:|---:|---:|
| Rapperswil–Uznach | 13.47 km | 4 | 689 | 263 | 10/8 | 3 | 15.56 MB |
| Olten–Aarau | 13.38 km | 2 | 366 | 52 | 37/2 | 1 | 2.55 MB |
| Gümligen–Konolfingen | 12.80 km | 4 | 74 | 27 | 0/8 | 1 | 1.59 MB |

Normalized branch counts are graph/pathing data, not a claim that every entry is a surveyed movable point machine.
