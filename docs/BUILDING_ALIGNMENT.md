# Building alignment

The runtime uses semantic `RoofSurface`, `WallSurface`, and `GroundSurface` polygons from swissBUILDINGS3D. The source archives contain 154,998 roof, 318,172 wall, and 97,592 ground polygons in the downloaded corridor crop; no useful CityGML appearance payload was present.

The visible floating was not a horizontal-CRS error. Official building ground elevations were being rendered above a visual terrain grid made from much coarser elevation samples. Of 7,965 accepted buildings, 7,725 have a GroundSurface. The median source-base/terrain delta is −3.409 m; the 95th-percentile absolute delta is 14.343 m, and the observed range is −37.034 to +32.255 m. There are 7,524 deltas over 1 m, 5,277 over 3 m, and 1,004 over 10 m.

Preprocessing now translates each complete building by the median GroundSurface-to-terrain delta (maximum accepted correction 40 m). Buildings lacking a GroundSurface receive only a conservative correction of at most 4 m. Relative building geometry is preserved; installations and unsupported detached surfaces are omitted. Corrections are **derived**, not official survey values. The machine-readable report is `data/manifests/building-alignment.json`.

Roof colour is a robust, desaturated median sampled from georeferenced SWISSIMAGE pixels within the roof bounds. Wall colour comes from a stable, muted procedural palette keyed by building ID. The former is **derived from SWISSIMAGE**; neither is official facade/material data.
