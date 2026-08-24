# Open Swiss Rail Sim

A browser-based open-data railway driving simulator for the real 13.47 km Rapperswil–Uznach alignment. It combines sampled Swiss national elevation data and OpenStreetMap railway infrastructure with deterministic Rust/WASM train physics. Operational state is explicitly simulated.

**Live simulator:** https://jfriedli.com/open-swiss-rail-sim/

## Features

- Cab and chase cameras on an actual Swiss alignment
- 120 Hz longitudinal physics with traction, service/emergency braking, resistance, gradient and energy
- Regular swissALTI3D-derived terrain grid, mapped speed sections, four route stops and 26 mapped signal positions
- Route-local procedural rails, ballast, sleepers and synthetic catenary
- Interactive combined traction/brake controller, emergency brake and speed/limit dial
- Speed, limit, gradient, next signal/station and engineering telemetry HUD
- In-app real/derived/simulated provenance inspector

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

See [architecture](docs/ARCHITECTURE.md), [pipeline](docs/DATA_PIPELINE.md), [provenance](docs/DATA_PROVENANCE.md), [physics](docs/PHYSICS.md), [signalling](docs/SIGNALLING.md), [selection](docs/CORRIDOR_SELECTION.md), and [performance](docs/PERFORMANCE.md).

## Deployment

Pushes to `main` run tests, build Rust/WASM and Vite, and deploy through the official GitHub Pages Actions flow. Vite uses relative asset paths so repository subpath hosting works.

## Limitations

Terrain uses 300 m swissALTI3D source samples interpolated to a stable 75 m render grid and has no orthophotography or buildings. Signal aspects and simplified authority are simulated, not live or recorded SBB state. No complete interlocking, ETCS/train-protection model, timetable, AI traffic, stop-result dialog or certified train model is claimed.

## License and attribution

Project code is MIT licensed. Runtime data attribution: © swisstopo; © OpenStreetMap contributors, ODbL. Dataset details and transformations are documented in `docs/DATA_PROVENANCE.md`.
