# Research notes

Research was checked against first-party sources on 24 August 2026. swisstopo provides swissALTI3D as open government data through documented download/services; the prototype uses the geo.admin.ch height endpoint and retains LV95/local-origin metadata. Open Transport Data Switzerland publishes static timetable/GTFS data under its platform terms; timetable ingestion is not yet part of this build.

SWISSIMAGE is officially supplied in LV95 as JPEG-compressed RGB Cloud Optimized GeoTIFF at 0.1 or 0.25 m ground resolution, with imagery from 2017 onward available for download. The federal WMS is also an official documented FSDI portrayal service. The runtime imagery is fetched reproducibly from the `ch.swisstopo.swissimage` WMS layer and downsampled to about 1.85 m/pixel WebP derivatives.

swisstopo's OGD terms allow use, processing, commercial use, distribution and making derivatives accessible, with mandatory attribution such as `© swisstopo`. swissTLM3D is currently available annually in LV95/LN02 as GeoPackage, Shapefile, File Geodatabase or Interlis and includes hydrography, roads, land cover and forest. Its current national download is not corridor-tiled; this build therefore uses a reproducible OSM corridor extract for these vector layers and records that choice rather than downloading the full country.

swissBUILDINGS3D 3.0 Beta is supplied in 1/16 national-map tiles in LV95/LN02. The documented SWISELD public asset search returned ten CityGML tiles intersecting the runtime extent. CityGML is available here and preserves LOD2 roof/wall surfaces, so it was selected over footprint extrusion. Source precision is approximately 0.3–0.5 m, but acquisition dates vary; the returned corridor assets are dated 2022.

Swiss railway operating rules are published by the Federal Office of Transport in FDV R 300.1–.15; the A2025 rules have applied since 14 December 2025. This simulator does not claim full FDV, interlocking, train-protection or ETCS fidelity.

Relevant OSM/OpenRailwayMap tags include `railway=rail`, `railway=signal`, `railway=switch`, `railway=station|halt`, `railway=platform`, `maxspeed`, directional maxspeed variants, `electrified=contact_line`, `voltage=15000`, `frequency=16.7`, `gauge=1435`, bridge/tunnel and Swiss `railway:signal:*` values. Completeness varies, so the UI labels these values mapped rather than authoritative.

The official 2026 GTFS publication from Geschäftsstelle SKI on behalf of BAV was inspected as a reproducible static source. Feed `GTFS_FP2026_20260822.zip` contains direction-consistent S17 trip `.ojp-91-17-M.1.TA.15.j26` (public trip 20253): Rapperswil 14:03, Blumenau 14:05, Schmerikon 14:11 and Uznach 14:14. Runtime metadata is cropped to this trip; the 225 MB source archive remains ignored under `data/raw/`.

The downloaded swissBUILDINGS3D CityGML exposes RoofSurface, WallSurface and GroundSurface semantics. The corridor archives contain 154,998 roof, 318,172 wall and 97,592 ground polygons; no useful appearance/material payload was observed. Roof colour is therefore explicitly derived from SWISSIMAGE and facade colour remains a synthetic restrained palette.
