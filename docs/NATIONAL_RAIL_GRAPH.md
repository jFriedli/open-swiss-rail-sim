# National supported-class rail graph

The build-time graph is derived from the Geofabrik Switzerland OpenStreetMap snapshot dated 24 August 2026. `osmium tags-filter` first reduces the 544 MB country PBF to railway ways and referenced nodes; `scripts/national/rail_graph.py` then keeps `railway=rail` with standard-gauge-compatible tagging. Narrow gauge, tram and funicular ways are counted rather than silently treated as supported.

The normalized graph contains 296,833 nodes, 302,622 consecutive-node edges, 9,703.6 track-km, 17,430 mapped switch nodes, 7,510 mapped signals, 1,979 station/halt nodes and 16,645 platform geometries in 608 connected components. The largest component contains 272,489 nodes. There are 436 sub-metre edges for later normalization review. Projected line intersections are never connected: connectivity exists only through shared OSM nodes, preserving bridge/tunnel/layer topology.

The canonical JSON is 45.38 MB and 6.78 MB gzip. It is therefore a compiler/resolver input, not a browser startup asset. Its content identity is `sha256:93b95311c59649c1c7f21eb8988fc2e12def1ada8b997372b3f951328b8f516e`; generated packages identify this graph version.

Build:

```sh
osmium tags-filter data/raw/national/switzerland-2026-08-24.osm.pbf \
  w/railway=rail,platform w/public_transport=platform \
  n/railway=switch,signal,station,halt \
  -o data/raw/national/supported-rail.osm.pbf
.venv/bin/python scripts/national/rail_graph.py \
  --source data/raw/national/supported-rail.osm.pbf
```

“Standard-gauge compatible” is a public-data capability classification, not operational certification. Missing gauge tags are provisionally accepted and surfaced through confidence/validation.
