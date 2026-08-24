# Scenery architecture

`scenery-manifest.json` is the versioned entry point. Four deterministic sectors partition the existing terrain columns and share boundary vertices, preventing seams. Each sector owns bounds in canonical local metres, a terrain-column range and a content-hashed SWISSIMAGE WebP URL. Renderer UVs are calculated from those same bounds: local X maps west→east and local Z maps north→south, while imagery pixel rows run north→south.

The current imagery is approximately 1.85 m/pixel, a deliberate reduction from the official 0.1/0.25 m source. It preserves field, settlement, road and shoreline identity in 2.1 MB while limiting decoded texture memory to an estimated 60 MiB. WebP was selected for reliable GitHub Pages/browser support, mipmap generation and compact transfer. Three.js enables trilinear mip filtering and the device's maximum supported anisotropy.

Terrain imagery, route geometry and every vector/mesh layer use the manifest's LV95 origin and the documented X-east/Y-up/Z-south frame. No visual nudging is used. Content hashes prevent stale Pages/CDN imagery and building buffers after regeneration.

The current landscape package contains 131 clipped water polygons, 149 forest polygons, 2,242 deterministic tree instances, 1,240 significant road features (171.2 km) and ten mapped platforms. Water uses a restrained translucent surface; the major lake uses its known terrain-relative datum. Road ribbons and platform surfaces sample the terrain grid. Trees are two instanced meshes, not individual objects.

Ten official swissBUILDINGS3D CityGML source tiles contribute 7,974 corridor buildings. Their LOD2 roof and wall polygons are preserved, de-duplicated and emitted as four indexed binary sector meshes: 418,958 unique vertices, 1,120,908 triangles and 18.48 MB. Sector streaming loads the current area and preloads ahead; four meshes replace thousands of Three.js objects. Neutral materials deliberately avoid inventing facade colours.
