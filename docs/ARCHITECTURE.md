# Architecture

The static Vite/Three.js frontend loads a compact corridor manifest and a Rust/WASM longitudinal simulation. Swiss WGS84/LV95 inputs are converted during preprocessing to a local X=east, Y=up, Z=south frame. `TrackFrameSampler` supplies the shared position, tangent, right, up and quaternion used by rails, ballast, sleepers, train, signals, catenary and cameras. Physics advances deterministically at 120 Hz. Instancing is used for sleepers and catenary masts.

The data pipeline is: Overpass candidate measurement → graph route selection → uniform 25 m resampling → LV95 conversion → swissALTI3D sampling → smoothed railway profile and regular terrain grid → validation → compact runtime JSON. Terrain is stored as a predictable rectangular height grid so later tile textures can use the same topology. GitHub Actions tests Rust and TypeScript, builds WASM and Vite, and deploys the artifact with GitHub Pages Actions.

The HTML/SVG cockpit is an accessible overlay. A single integer controller state from −5 (B5) through zero to +5 (P5) synchronizes keyboard, click, pointer/touch drag and WASM inputs. Emergency braking remains a separate deliberate state. The fixed Forward reverser is an indicator, not a non-functional control.
