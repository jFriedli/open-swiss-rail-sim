# Performance

Production build measured 24 August 2026: JavaScript 511 kB (130 kB gzip), WASM 15.6 kB (7.1 kB gzip), route JSON 92 kB and terrain JSON 60 kB. The 204 × 48 regular terrain grid has 9,792 vertices and 19,082 triangles over 15.225 × 3.525 km. The scene uses instanced sleepers/catenary and exposes FPS, draw calls and rendered triangles in `?debug=1` mode. Headless SwiftShader screenshot runs are not representative of hardware FPS, so no unsupported desktop figure is claimed.
