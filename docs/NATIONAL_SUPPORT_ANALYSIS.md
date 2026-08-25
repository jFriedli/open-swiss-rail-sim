# National support analysis

A deterministic sample selected one active trip from each GTFS `route_id`, shuffled with seed `20260822`, then resolved 300 trips against the actual supported-class national graph.

| Result | Trips |
|---|---:|
| FULL-compatible | 78 |
| PARTIAL-compatible | 12 |
| UNSUPPORTED | 15 |
| UNRESOLVED | 195 |

The analysis took 2.57 seconds after a 1.50 second graph load. Of the unresolved trips, 189 had no nearby supported-class graph node and six crossed disconnected components. The 15 unsupported trips had station associations beyond the acceptable threshold. These categories include narrow-gauge, tram-like, foreign and topology-incompatible services; a future index should attach explicit gauge/system categories earlier so fewer failures collapse into “no supported node”.

This route-stratified sample is intentionally challenging and is not a statistical estimate of passenger journeys. It replaces the earlier metadata-only result of zero graph-resolved trips with measured path resolution, while exposing the present support boundary honestly. Full per-trip results are in `data/manifests/national-support-analysis.json`.
