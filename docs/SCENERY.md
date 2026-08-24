# Scenery architecture

`scenery-manifest.json` is the versioned entry point. Four deterministic sectors partition the existing terrain columns and share boundary vertices, preventing seams. Each sector owns bounds in canonical local metres, a terrain-column range and a content-hashed SWISSIMAGE WebP URL. Renderer UVs are calculated from those same bounds: local X maps west→east and local Z maps north→south, while imagery pixel rows run north→south.

The current imagery is approximately 1.85 m/pixel, a deliberate reduction from the official 0.1/0.25 m source. It preserves field, settlement, road and shoreline identity in 2.1 MB while limiting decoded texture memory to an estimated 60 MiB. WebP was selected for reliable GitHub Pages/browser support, mipmap generation and compact transfer. Three.js enables trilinear mip filtering and the device's maximum supported anisotropy.

Terrain imagery, route geometry and future scenery layers all use the manifest's LV95 origin and the documented X-east/Y-up/Z-south frame. No visual nudging is used. Content hashes prevent stale Pages/CDN imagery after regeneration.
