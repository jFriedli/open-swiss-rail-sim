# Open Swiss Rail Sim

A browser-based open-data railway driving simulator for the real 13.47 km Rapperswil–Uznach alignment. It combines Swiss national elevation, orthophotography and 3D building data with mapped landscape/railway infrastructure and deterministic Rust/WASM train physics. Operational state is explicitly simulated.

**Live simulator:** https://jfriedli.com/open-swiss-rail-sim/

## Features

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

## Controls

The combined controller has neutral, P1–P5 power and B1–B5 service-brake notches. Click a labelled notch or drag the lever with mouse/touch. W/Up moves toward power, S/Down moves toward braking, A moves one notch toward neutral, Space applies the separate emergency brake, C changes camera, and R restarts. The current scenario's reverser is fixed Forward.

## Development

Requires Node, Rust, the `wasm32-unknown-unknown` target and wasm-pack.

```sh
npm install
cargo test --workspace
npm test
npm run build
npm run dev
```

See [architecture](docs/ARCHITECTURE.md), [scenery](docs/SCENERY.md), [journey](docs/JOURNEY.md), [pipeline](docs/DATA_PIPELINE.md), [provenance](docs/DATA_PROVENANCE.md), [physics](docs/PHYSICS.md), [signalling](docs/SIGNALLING.md), [selection](docs/CORRIDOR_SELECTION.md), and [performance](docs/PERFORMANCE.md).

## Deployment

Pushes to `main` run tests, build Rust/WASM and Vite, and deploy through the official GitHub Pages Actions flow. Vite uses relative asset paths so repository subpath hosting works.

## Limitations

Terrain still uses 300 m swissALTI3D source samples interpolated to a stable 75 m render grid, so small embankments and cuts are simplified. Orthophotography is intentionally reduced to about 1.85 m/pixel. Trees are synthetic instances within real mapped forest boundaries; roads, water and platforms use open-mapping geometry rather than swissTLM3D in this build. Roof colours are derived from orthophotography and walls use a muted deterministic palette, not official material data. OpenStreetMap signal coverage ends near s=1.07 km, so eight clearly classified scenario signals fill the gameplay gap. Signal aspects and authority are simulated. The static timetable is real, but the player run, dwell, score and doors are simulated. No complete interlocking, ETCS/train-protection model, AI traffic or certified train model is claimed.

## License and attribution

Project code is MIT licensed. Runtime data attribution: © swisstopo; © OpenStreetMap contributors, ODbL. Dataset details and transformations are documented in `docs/DATA_PROVENANCE.md`.
