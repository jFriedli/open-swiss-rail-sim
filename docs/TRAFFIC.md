# Timetable traffic

Generated packages select an official reverse-direction GTFS trip in the same operating window. Calls are real; graph path, continuous position and movement are derived/simulated. AI now uses a deterministic controller with acceleration, service braking, speed-limit priority and a movement-authority hold point. Safety and authority take precedence over timetable recovery.

The default operating window is 13:55–14:25 on Saturday 22 August 2026. `scripts/data/build_traffic.py` filters official static feed `GTFS_FP2026_20260822.zip` by calendar and exception dates, corridor stops, and time window. The earlier player trip ID was an inactive calendar variant; the active equivalent is S17 trip `.ojp-91-17-M.1.TA.200.j26`, public train 12353.

Three AI services are retained:

| Train | Direction | Corridor calls |
| --- | --- | --- |
| 11448 | Uznach → Rapperswil | Uznach 14:13, Rapperswil 14:23 |
| 11648 | Uznach → Rapperswil | Uznach 14:15, Schmerikon 14:17, Blumenau 14:23, Rapperswil 14:27 |
| 2025 | Rapperswil → Uznach | Rapperswil 14:07, Uznach 14:17 |

Timetables are **real official static data**. Paths are deterministic shortest paths through the OSM-derived graph, with a penalty that keeps opposing services off the player path where the mapped topology permits. Positions, acceleration, braking, occupancy, dwell and delay are **simulated**.

The timetable supplies a moving schedule target. The lightweight deterministic driver accelerates at up to 0.65 m/s², service-brakes at 0.75 m/s² and limits its target to 160 km/h. A route denial establishes a fixed authority target: the AI brakes, stops, waits, records delay and accelerates again only after the interlocking grants authority. Safety has priority over schedule recovery. Trains occupy every graph edge from their 75 m rear to front. A stopped train remains logically dwelling through its GTFS arrival/departure interval.

The renderer is separate from simulation identity. Stable AI IDs own timetable/motion state; generic three-car meshes are only visible representations with front and rear lights. The expanded/debug map shows traffic and the nearby-trains panel reports direction, distance and next stop.
