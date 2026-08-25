# RoutePackage schema

The browser consumes versioned, static `RoutePackage` directories under `public/data/<route-id>/`. `public/data/routes.json` is the lightweight catalogue; selecting a route loads only that package's manifest and assets.

Schema version 1 contains identity and presentation metadata, a route-specific LV95 origin and bounds, player-service metadata, relative asset URLs, capability classification, quantitative coverage, source provenance, generated validation checkpoints and measured package bytes. The canonical runtime frame remains X east, Y up, Z south, one unit per metre. The runtime rejects unknown schema versions and railway capabilities it cannot model.

Required assets are `route`, `terrain`, `scenery`, `landscape`, `journey`, `railNetwork` and `traffic`. Relative paths are resolved against the package manifest URL, making GitHub Pages subpaths safe. Heavy assets are not referenced by the catalogue and therefore are not downloaded before route selection.

New packages record the national graph content hash used for resolution. Scenery manifests may reference content-addressed assets in the shared `/data/tiles` store; package validation resolves and checks these relative references before publication.

Support tiers are `FULL`, `PARTIAL` and `UNSUPPORTED`. The current runtime targets standard-gauge adhesion railways. A route may be partial when public signal, speed, platform or scenery coverage is incomplete; the coverage report must expose that rather than silently inventing authoritative data.

Environment initialization uses package `sourceDate`, player-service time, route WGS84 samples and terrain elevation. A package does not embed a permanent weather toggle. The runtime looks up an optional date-specific weather field and otherwise uses a documented custom fallback, so every schema-v1 route receives the same environment implementation.
