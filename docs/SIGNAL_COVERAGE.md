# Signal coverage

The driving direction is Rapperswil → Uznach. `scripts/data/build_signals.py` matches every `railway=signal` node in the query area to the route, interprets the node's parent-way order and `railway:signal:direction`, and rejects nodes farther than 12 m from the selected track.

| Measure | Result |
| --- | ---: |
| Route length | 13,468.28 m |
| Raw mapped signals | 69 |
| Matched to selected track | 18 |
| Direction-applicable mapped signals | 10 |
| Reverse or ambiguous matched signals | 8 |
| Rejected (including off-route) | 59 |
| Last mapped forward signal | s = 1,071.00 m |
| Mapped gap from last signal to route end | 12,397.28 m |
| Scenario signals added | 8 |
| Largest playable signal gap | 1,500 m |

The old `NEXT SIGNAL: END` was therefore caused by a genuine open-mapping coverage gap, not the runtime pointer. Eight scenario block signals now provide gameplay context through the remaining corridor. Their location provenance is always `SIMULATED_SCENARIO`; they are never represented as mapped infrastructure. Aspects remain simulated for every signal. The detailed accepted/rejected records and route-distance diagram data are in `data/manifests/signal-coverage.json`.

Signal progression is an ordered route-distance lookup. Crossing detection uses previous/current route distance, so a high-speed or large debug step cannot skip a pass event.
