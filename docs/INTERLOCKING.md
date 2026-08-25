# Simplified interlocking

Reservations can be updated progressively. Sections and switch locks removed from a train's requested window are released only when no occupant or other route needs them; newly requested sections pass the same fail-restrictive checks. AI authority denial feeds its driver instead of permitting timetable playback through Halt.

> This is a simplified simulated railway-safety model built from public infrastructure data. It does not reproduce SBB's operational interlocking configuration.

Each OSM-derived graph edge is a simulated detection section. Occupancy is distinct from reservation and accounts for the complete 75 m AI train, including simultaneous occupation across edge boundaries. Missing sections return `UNKNOWN` and fail restrictive.

Routes contain an owner, required sections and required switch states. A request succeeds only when all sections are free (or occupied solely by that route's train), all switches exist and are available to that route, and no conflicting reservation exists. Establishing a route positions and locks its switches. A locked switch cannot move. At each operations update the requested window slides forward with the train rear: cleared sections and switches no longer required are released while forward reservations are retained or extended. Active AI route requests are evaluated deterministically by service order; the player does not receive automatic priority.

Player signal authority protects the next 30 graph edges attached to the signal. It remains at Halt when a protected section is occupied or reserved by conflicting AI traffic. After traffic clears and the route can be established, the aspect becomes Clear. Locations retain their mapped/scenario provenance; every aspect, route, switch state and detection section is simulated.

The driver-aid stopping-distance comparison is deliberately simple and is not an ETCS, ZUB or EuroSignum braking curve. Runtime operations events explain route denial, locking and release in debug mode.

AI trajectory targets come from the real timetable, but a denied route creates a fixed movement-authority target. The lightweight driver uses a 0.75 m/s² service-braking envelope, stops at that target, accrues simulated operational delay, and only resumes after authority is granted. Safety and speed take priority over timetable recovery.

Safety invariants covered by tests include occupied/unknown failure, conflicting-route rejection, switch locking, train-length boundary occupancy, rear release, progressive route update, AI Halt/restart and deterministic reset.
