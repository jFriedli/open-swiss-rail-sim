# Timetable traffic

The default operating window is 13:55–14:25 on Saturday 22 August 2026. `scripts/data/build_traffic.py` filters official static feed `GTFS_FP2026_20260822.zip` by calendar and exception dates, corridor stops, and time window. The earlier player trip ID was an inactive calendar variant; the active equivalent is S17 trip `.ojp-91-17-M.1.TA.200.j26`, public train 12353.

Three AI services are retained:

| Train | Direction | Corridor calls |
| --- | --- | --- |
| 11448 | Uznach → Rapperswil | Uznach 14:13, Rapperswil 14:23 |
| 11648 | Uznach → Rapperswil | Uznach 14:15, Schmerikon 14:17, Blumenau 14:23, Rapperswil 14:27 |
| 2025 | Rapperswil → Uznach | Rapperswil 14:07, Uznach 14:17 |

Timetables are **real official static data**. Paths are deterministic shortest paths through the OSM-derived graph, with a penalty that keeps opposing services off the player path where the mapped topology permits. Positions, acceleration, braking, occupancy, dwell and delay are **simulated**.

The lightweight driver uses a trapezoidal motion profile between scheduled calls. It accelerates and brakes for up to 25 seconds at each end of a leg and cruises between them. The cruise speed is derived from path distance and scheduled running time; the selected services remain within the corridor's plausible main-line range. Trains occupy every graph edge from their 75 m rear to front. A stopped train remains logically dwelling through its GTFS arrival/departure interval.

The renderer is separate from simulation identity. Stable AI IDs own timetable/motion state; generic three-car meshes are only visible representations with front and rear lights. The expanded/debug map shows traffic and the nearby-trains panel reports direction, distance and next stop.
