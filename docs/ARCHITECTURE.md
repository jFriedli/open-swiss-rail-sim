# Architecture

The static Vite/Three.js frontend loads a compact corridor manifest and a Rust/WASM longitudinal simulation. Swiss WGS84/LV95 inputs are converted during preprocessing to a local X=east, Y=up, Z=negative north frame. Physics advances deterministically at 120 Hz while rendering interpolates the route by arc-length proportion. Instancing is used for sleepers and catenary masts.

The data pipeline is: Overpass candidate measurement → graph route selection → LV95 conversion → swissALTI3D sampling → validation → compact runtime JSON. GitHub Actions tests Rust and TypeScript, builds WASM and Vite, and deploys the artifact with GitHub Pages Actions.

