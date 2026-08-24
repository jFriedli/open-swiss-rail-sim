# Research notes

Research was checked against first-party sources on 24 August 2026. swisstopo provides swissALTI3D as open government data through documented download/services; the prototype uses the geo.admin.ch height endpoint and retains LV95/local-origin metadata. Open Transport Data Switzerland publishes static timetable/GTFS data under its platform terms; timetable ingestion is not yet part of this build.

Swiss railway operating rules are published by the Federal Office of Transport in FDV R 300.1–.15; the A2025 rules have applied since 14 December 2025. This simulator does not claim full FDV, interlocking, train-protection or ETCS fidelity.

Relevant OSM/OpenRailwayMap tags include `railway=rail`, `railway=signal`, `railway=switch`, `railway=station|halt`, `railway=platform`, `maxspeed`, directional maxspeed variants, `electrified=contact_line`, `voltage=15000`, `frequency=16.7`, `gauge=1435`, bridge/tunnel and Swiss `railway:signal:*` values. Completeness varies, so the UI labels these values mapped rather than authoritative.

