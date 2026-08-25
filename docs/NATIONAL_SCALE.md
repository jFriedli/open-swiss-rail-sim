# National-scale architecture

Precompiled packages are static and simple but duplicate scenery. Browser assembly avoids a backend but would ship large indexes and geospatial complexity. Per-request compilation offers flexibility but cold conversion adds minutes and operational cost.

The recommended next architecture is hybrid: immutable national LV95 scenery/rail tiles shared by content hash, plus small per-trip manifests containing path, timetable, operational sections and derived scenarios. Popular trips can be precompiled; an eventual service can assemble less common supported trips from the same tile store. The browser remains a static consumer.

The fourth route begins this migration: its SWISSIMAGE files live in a global content-addressed store and its package references them rather than owning copies. Four images total 1.89 MB while route-specific metadata is 0.62 MB. A cached deterministic rebuild reuses the same four hashes and adds zero new bytes. Tile records now carry a stable LV95 bounds identifier, but the current route-strip bounds are not yet the final fixed 1–2 km national grid; cross-route overlap savings are therefore not overstated.

Observed payload is 1.59–2.55 MB for terrain/imagery/topology compiler proofs and 15.56 MB for the building-rich showcase. Direct national extrapolation is unsafe because overlap and urban density dominate, but this demonstrates why overlapping routes should reference shared LV95 tiles.

Cold validation-route builds, including official downloads, measured roughly 135–163 seconds; fully cached builds measured 2.76–4.30 seconds. On-demand assembly is therefore seconds-scale only after geographic tiles are cached, and minutes-scale otherwise. These are measured examples, not national guarantees.

The runtime and simulation use JavaScript/Rust 64-bit state, while GPU vertex attributes are 32-bit. Approximate float32 position increments are 0.004 m at 50 km, 0.008 m at 100 km and 0.016 m at 200 km from a route origin. That remains acceptable for the current 16 km maximum, but a floating render origin should be introduced before routine 100–200 km packages so track/camera transforms retain millimetre-to-centimetre stability.
