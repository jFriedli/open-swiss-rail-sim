# Performance

Production build measured 24 August 2026: JavaScript 513 kB (131 kB gzip), CSS 4.0 kB (1.6 kB gzip), WASM 15.6 kB (7.1 kB gzip), route JSON 92 kB and terrain JSON 60 kB. The 204 × 48 regular terrain grid has 9,792 vertices and 19,082 triangles over 15.225 × 3.525 km. The scene uses instanced sleepers/catenary and exposes FPS, draw calls and rendered triangles in `?debug=1` mode. Diagnostic scenes report roughly 164k–178k rendered triangles and 55–143 draw calls depending on visible signals. Headless SwiftShader screenshot FPS is not representative of hardware performance, so no unsupported desktop figure is claimed.

SWISSIMAGE adds four WebP files totalling 2.115 MB transfer. Their decoded RGB/RGBA texture-memory estimate is about 60 MiB. Images are approximately 1.85 m/pixel, use generated mipmaps and maximum supported anisotropic filtering. Complete production `dist` is approximately 2.8 MB before HTTP transfer compression.
