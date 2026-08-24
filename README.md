# Open Swiss Rail Sim

A browser-based open-data railway driving simulator for the real 13.47 km Rapperswil–Uznach alignment. It combines sampled Swiss national elevation data and OpenStreetMap railway infrastructure with deterministic Rust/WASM train physics. Operational state is explicitly simulated.

## Features

- Cab and chase cameras on an actual Swiss alignment
- 120 Hz longitudinal physics with traction, service/emergency braking, resistance, gradient and energy
- Real elevation strip, mapped speed sections, four route stops and 26 mapped signal positions
- Procedural rails, sleepers and synthetic catenary
- Speed, limit, gradient, next signal/station and engineering telemetry HUD
- In-app real/derived/simulated provenance inspector

## Controls

W/Up increases power, S/Down increases brake, A releases a notch, Space applies emergency brake, C changes camera, and R restarts.

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

Terrain is a sampled corridor strip without orthophotography or buildings. Signal aspects and simplified authority are simulated, not live or recorded SBB state. No complete interlocking, ETCS/train-protection model, timetable, AI traffic, stop-result dialog, touch controls or certified train model is claimed.

## License and attribution

Project code is MIT licensed. Runtime data attribution: © swisstopo; © OpenStreetMap contributors, ODbL. Dataset details and transformations are documented in `docs/DATA_PROVENANCE.md`.

