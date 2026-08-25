# Facade generation

swissBUILDINGS3D roof and wall triangles remain the real geometric source. Roof colours remain derived from SWISSIMAGE. Wall base colours are deterministic synthetic palettes.

One shared wall shader derives a metre-scale floor/bay grid from world coordinates. It rejects most of each grid cell and emits a deterministic subset at low light, producing facade detail without window meshes, per-building materials or CPU updates. The pattern is deliberately labelled synthetic: it does not reproduce surveyed window locations or real occupancy. Roof snow uses the shared environmental material path, so no duplicate snow geometry is generated.

The rendering inputs are intentionally structured as facade class, scale/bay density, palette and night occupancy. A later offline enrichment process can populate those attributes without coupling visual inference to railway safety logic.

