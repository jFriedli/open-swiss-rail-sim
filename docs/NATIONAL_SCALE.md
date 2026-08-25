# National-scale architecture

Precompiled packages are static and simple but duplicate scenery. Browser assembly avoids a backend but would ship large indexes and geospatial complexity. Per-request compilation offers flexibility but cold conversion adds minutes and operational cost.

The recommended next architecture is hybrid: immutable national LV95 scenery/rail tiles shared by content hash, plus small per-trip manifests containing path, timetable, operational sections and derived scenarios. Popular trips can be precompiled; an eventual service can assemble less common supported trips from the same tile store. The browser remains a static consumer.

Observed payload is 1.59–2.55 MB for terrain/imagery/topology compiler proofs and 15.56 MB for the building-rich showcase. Direct national extrapolation is unsafe because overlap and urban density dominate, but this demonstrates why overlapping routes should reference shared LV95 tiles.

Cold validation-route builds, including official downloads, measured roughly 135–163 seconds; fully cached builds measured 2.76–4.30 seconds. On-demand assembly is therefore seconds-scale only after geographic tiles are cached, and minutes-scale otherwise. These are measured examples, not national guarantees.
