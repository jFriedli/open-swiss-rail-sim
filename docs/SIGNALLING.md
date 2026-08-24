# Signalling

Signal positions and available tags come from OpenStreetMap. Lamp geometry is a recognizable simplified lineside representation. Current aspects are scenario simulation, not recorded or live infrastructure state. The Rust safety kernel fails restrictive without a reservation, refuses occupied-block reservations and prevents overlapping reservations. The browser scenario uses a deliberately small block-authority presentation; it does not reproduce an SBB interlocking, ZUB, EuroSignum or ETCS.

The complete direction-aware audit found 69 raw nodes, 18 matched to the selected track, and ten applicable to Rapperswil → Uznach. All applicable mapped signals occur before s=1,071 m. Eight explicit `SIMULATED_SCENARIO` signals at 1,500 m block intervals extend playable context to the route end. Runtime lookup is ordered by route distance and emits deterministic `SignalPassed` events. See [SIGNAL_COVERAGE.md](SIGNAL_COVERAGE.md).

Every runtime signal is now attached to a player-path graph edge and 30 following simulated detection sections. A mapped location remains `OPEN_MAPPING`; a generated location remains `SIMULATED_SCENARIO`. Both aspects are simulated from occupancy, conflicting reservation and route availability. Debug inspection reports the blocking train/route and protected edge IDs.
