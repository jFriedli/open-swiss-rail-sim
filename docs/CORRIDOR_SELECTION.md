# Corridor selection

Five candidate areas were measured on 24 August 2026 with `scripts/data/evaluate_corridors.py`. Counts are raw infrastructure in each bounding box, so complex station areas increase track-km; final-route matching is performed separately.

| Candidate | Track km | Signals | Signals/km | Switches | Stops | Platforms | Speed coverage | Tunnels |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Rapperswil–Uznach | 31.5 | 39 | 1.24 | 83 | 6 | 9 | 100% | 0% |
| Olten–Lenzburg area | 161.0 | 227 | 1.41 | 685 | 32 | 39 | 98% | 12% |
| Bern–Thun north | 114.0 | 67 | 0.59 | 335 | 29 | 108 | 99% | 1% |
| Luzern–Sursee south | 74.9 | 56 | 0.75 | 190 | 14 | 15 | 98% | 6% |
| Basel–Liestal | unavailable | — | — | — | — | — | — | — |

Rapperswil–Uznach was selected because its resolved route is 13.47 km, has four matched stops and 26 signals, complete mapped electrification and speed-tag coverage, varied lake/plain/topographic scenery, and no tunnel treatment requirement. The denser Olten candidate would require substantially more topology and scenery for a first corridor. The Basel request was rate-limited; that does not affect the clear engineering choice.

