# Open Swiss Rail Sim

A browser-based open-data railway driving simulator driven by versioned Swiss `RoutePackage` datasets. Four real corridors use the same Three.js and Rust/WASM engine; operational state is explicitly simulated. A national timetable index and supported-class rail resolver provide the path toward service-driven compilation.

**Live simulator:** https://jfriedli.com/open-swiss-rail-sim/

## Features

- Search 17,194 active official timetable trips by origin, destination and time
- Selectable Rapperswil–Uznach, Olten–Aarau, Gümligen–Konolfingen and Winterthur–Frauenfeld packages
- Generic build-time compiler for official timetable trips, mapped rail topology, terrain and imagery
- National standard-gauge-compatible OSM graph with explicit support classification

- Cab and chase cameras on an actual Swiss alignment
- 120 Hz longitudinal physics with traction, service/emergency braking, resistance, gradient and energy
- Regular swissALTI3D-derived terrain grid, mapped speed sections and audited full-route signal context
- Real SWISSIMAGE ground imagery in four georeferenced, content-hashed scenery sectors
- 7,965 real swissBUILDINGS3D LOD2 buildings with semantic roofs/walls, derived roof colour and streamed sectors
- Mapped Obersee/water surfaces, 171 km of surrounding roads, ten platforms and 2,242 forest-derived trees
- Route-local procedural rails, ballast, sleepers and synthetic catenary
- Interactive combined traction/brake controller, emergency brake and speed/limit dial
- Speed, limit, gradient, next signal/station and engineering telemetry HUD
- In-app real/derived/simulated provenance inspector
- Geographic local-data minimap with heading, stations and route progress
- Official static S17 timetable scenario with platform targets, dwell, missed-stop detection and journey completion
- 31.54 km OSM rail graph with 689 edges, 35 switches and surrounding station tracks
- Three official-timetable AI services with deterministic motion, dwell and train-length occupancy
- Simplified fail-safe section reservation, switch locking and traffic-driven signal aspects
- Geographic NOAA sun model with service-date time, continuous day/twilight/night lighting and procedural sky
- MeteoSwiss service-date observation field plus custom clear, overcast, rain, fog and snow environments
- Wet surfaces, elevation-aware derived snow cover, precipitation, synthetic facade windows and night station lighting

## Controls

The combined controller has neutral, P1–P5 power and B1–B5 service-brake notches. Click a labelled notch or drag the lever with mouse/touch. W/Up moves toward power, S/Down moves toward braking, A moves one notch toward neutral, Space applies the separate emergency brake, C changes camera, P/Escape pauses the shared player/traffic clock, and R deterministically restarts the scenario. The current scenario's reverser is fixed Forward.

## Development

Requires Node, Rust, the `wasm32-unknown-unknown` target and wasm-pack.

```sh
npm install
cargo test --workspace
npm test
npm run build
npm run dev
```

See [architecture](docs/ARCHITECTURE.md), [environment](docs/ENVIRONMENT.md), [weather](docs/WEATHER.md), [national graph](docs/NATIONAL_RAIL_GRAPH.md), [service resolution](docs/SERVICE_RESOLUTION.md), [route packages](docs/ROUTE_PACKAGE.md), [provenance](docs/DATA_PROVENANCE.md), and [performance](docs/PERFORMANCE.md).

Generate and validate the configured compiler-proof routes from the pinned local source cache:

```sh
python3 scripts/route_compiler.py --all
python3 scripts/data/validate_route_packages.py
```

An unconfigured trip can be compiled without a route-definition entry:

```sh
.venv/bin/python scripts/route_compiler.py \
  --trip-id '.ojp-91-30-A.1.TA.337.j26' \
  --from-station Winterthur --to-station Frauenfeld \
  --service-date 2026-08-22 --id winterthur-frauenfeld
```

## Deployment

Pushes to `main` run tests, build Rust/WASM and Vite, and deploy through the official GitHub Pages Actions flow. Vite uses relative asset paths so repository subpath hosting works.

## Limitations

Rapperswil–Uznach is the `FULL` showcase. The other routes are `PARTIAL` compiler proofs: they include real terrain, imagery, timetable and railway topology but omit the showcase's swissBUILDINGS3D and complete landscape payload. Searchability does not imply driveability; only committed packages expose a Select action. The national graph currently targets standard-gauge-compatible adhesion railways and leaves many narrow-gauge, tram, rack, foreign or topology-ambiguous trips unsupported/unresolved. Terrain uses 300 m swissALTI3D samples interpolated to a stable 75 m render grid. Detection sections, route locking, AI motion and signal aspects are simplified simulations, not SBB operational data.

## License and attribution

Project code is MIT licensed. Runtime data attribution: © swisstopo; © OpenStreetMap contributors, ODbL; Source: MeteoSwiss. Dataset details and transformations are documented in `docs/DATA_PROVENANCE.md`.
