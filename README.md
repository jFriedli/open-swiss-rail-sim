# Open Swiss Rail Sim

A browser-based open-data railway driving simulator driven by versioned Swiss `RoutePackage` datasets. Three real corridors use the same Three.js and Rust/WASM engine; operational state is explicitly simulated.

**Live simulator:** https://jfriedli.com/open-swiss-rail-sim/

## Features

- Selectable Rapperswil–Uznach, Olten–Aarau and Gümligen–Konolfingen route packages
- Generic build-time compiler for official timetable trips, mapped rail topology, terrain and imagery

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

See [architecture](docs/ARCHITECTURE.md), [rail network](docs/RAIL_NETWORK.md), [traffic](docs/TRAFFIC.md), [interlocking](docs/INTERLOCKING.md), [scenery](docs/SCENERY.md), [journey](docs/JOURNEY.md), [pipeline](docs/DATA_PIPELINE.md), [provenance](docs/DATA_PROVENANCE.md), [physics](docs/PHYSICS.md), [signalling](docs/SIGNALLING.md), [selection](docs/CORRIDOR_SELECTION.md), and [performance](docs/PERFORMANCE.md).

Generate and validate the two compiler-proof routes from the pinned local source cache:

```sh
python3 scripts/route_compiler.py --all
python3 scripts/data/validate_route_packages.py
```

## Deployment

Pushes to `main` run tests, build Rust/WASM and Vite, and deploy through the official GitHub Pages Actions flow. Vite uses relative asset paths so repository subpath hosting works.

## Limitations

Rapperswil–Uznach is the `FULL` showcase. Olten–Aarau and Gümligen–Konolfingen are `PARTIAL` compiler proofs: they include real terrain, imagery, timetable and railway topology but omit the showcase's swissBUILDINGS3D and complete landscape payload. Terrain uses 300 m swissALTI3D source samples interpolated to a stable 75 m render grid, so small embankments and cuts are simplified. Detection sections, switch states, route locking, AI motion and signal aspects are simplified simulations, not SBB operational data. No complete SBB interlocking, ETCS/train-protection model or certified train model is claimed.

## License and attribution

Project code is MIT licensed. Runtime data attribution: © swisstopo; © OpenStreetMap contributors, ODbL. Dataset details and transformations are documented in `docs/DATA_PROVENANCE.md`.
