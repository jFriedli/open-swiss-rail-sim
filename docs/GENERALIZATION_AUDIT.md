# Generalization audit

The initial runtime and preprocessing pipeline were built around one corridor. This audit records the coupling found before introducing RoutePackage schema version 1.

| Assumption | Location | Resolution |
|---|---|---|
| Fixed `data/rapperswil-uznach` URLs | browser bootstrap | package-relative asset map |
| Fixed route/start/result labels | browser templates | package and journey metadata |
| Direction detected by the word `Rapperswil` | AI simulation | explicit package path orientation and station-distance lookup |
| Fixed station names and four calls | journey/traffic scripts and smoke tests | compiler derives GTFS calls; runtime journey arrays are variable length |
| Fixed trip, date and 30-minute window | journey/traffic scripts | route definitions plus resolved trip and derived operating window |
| Fixed LV95 origin and landscape bounds | data scripts | package-specific origin/bounds |
| Four imagery/building sectors | imagery script and streaming | compiler-derived sector chain; runtime already iterates arbitrary tiles |
| Terrain extents 15.225 × 3.525 km | terrain/landscape scripts | derived route bounds and buffers |
| Signal fallback tailored to one mapped gap | signal script | context-aware package compiler stage |
| Player protected route is 30 graph edges | runtime operations | package-derived operational sections required |
| Player spline and graph matching use corridor files | graph script | compiler stage parameters |
| Tests name Blumenau/Uznach and fixed chainages | Playwright | generic route matrix uses catalogue/package metadata; flagship regression tests remain intentionally specific |

No route-specific runtime branch is an accepted long-term solution. Capability branches may distinguish supported infrastructure classes, but must be expressed in package metadata.
