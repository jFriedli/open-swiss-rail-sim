# Service search and resolution

`scripts/national/service_index.py` turns the pinned official GTFS into a date-correct compact index. For 22 August 2026 it contains 4,504 referenced stations, 17,194 active rail trips and 381 route/service identifiers in 4.47 MB. Calendar exceptions and GTFS hours above 24 are preserved as absolute seconds.

The browser loads the index only after a service search. It normalizes Swiss spelling aliases, matches ordered origin/destination calls and ranks results by requested time. A timetable result is distinct from a compiled drive package; only committed packages receive a Select action.

`scripts/national/resolver.py` maps every selected timetable call to a nearby supported graph node, then runs A* independently through each consecutive call. Edge scoring penalizes yards, sidings, spurs and industrial infrastructure. The final path must visit calls in order and remain in one connected component. Station offset, mapped-signal count and max-speed coverage determine `FULL`, `PARTIAL`, `UNSUPPORTED` or `UNRESOLVED` classification.

The national graph loads in about 1.5 seconds on the development machine. Typical resolved searches take tens of milliseconds after load. Complex or disconnected services fail with an explicit reason.
