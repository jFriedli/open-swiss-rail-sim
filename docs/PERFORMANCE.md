# Performance

Production build measured 24 August 2026: JavaScript 502 kB (127 kB gzip), WASM 15.6 kB (7.1 kB gzip), corridor JSON 52 kB, total `dist` 588 kB. The scene uses one 1,080-triangle terrain strip, two rail meshes, and instanced sleepers/catenary. The deployed app and corridor asset both returned HTTP 200 and its Playwright drive smoke test passed. FPS remains device-dependent and was not instrumented; no unsupported figure is claimed.
