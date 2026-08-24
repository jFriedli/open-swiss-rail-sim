# Rail network

The corridor graph is generated from the cached OpenStreetMap rail extract by `scripts/data/build_rail_network.py`. Railway ways are split at shared OSM nodes, explicit `railway=switch` nodes, and way endpoints. Projected line crossings are never joined, preventing accidental bridge/tunnel connections. Runtime coordinates use the canonical X=east, Y=up, Z=south metre frame.

| Measure | Value |
| --- | ---: |
| Network nodes | 688 |
| Track edges | 689 |
| Total mapped track | 31.54 km |
| Mapped switches | 35 |
| Connected components | 1 |
| Player path edges | 263 |
| Platform associations | 10 |

Every edge retains its OSM way ID, endpoint node IDs, source geometry, speed/electrification/service tags and length. Switch locations are open mapping; switch state and locking are simulated. The existing smoothed player spline remains the rendering/physics path but is matched to an ordered sequence of graph edges. Platform-to-edge associations are nearest-track derivations and remain subject to mapping ambiguity in multi-track station areas.

Visual rails, sleepers and formation are derived from each edge independently using its local tangent. This graph is infrastructure context for a simplified operating simulation, not an authoritative SBB topology or interlocking plan.
