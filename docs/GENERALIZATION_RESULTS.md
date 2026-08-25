# Generalization results

A shared compiler generated two new corridors from route definitions and cached sources; the browser loads all three with the same asset loader, coordinate conversion, scene, minimap, journey and operations code. No route-ID conditional was added to rendering or simulation.

The pinned 2026-08-22 official GTFS snapshot contains 256,328 inspected rail trip records with public train numbers. A deterministic 30-trip metadata sample found 15 trips in the current 8–40 km MVP distance screen and 15 outside it. This is only timetable screening: zero random trips are claimed as graph-resolved because a national normalized rail graph is not yet available. Results are in `data/manifests/national-route-sample.json`.

The strongest evidence is three complete graph/path compilations, not the broad metadata count. Common limitations are missing mapped signals, platform/track ambiguity, incomplete speed tags, unavailable converted buildings outside cached tiles, unusual gauge/rack systems and ETCS-only environments. Generic standard-gauge adhesion route compilation is viable; arbitrary Swiss service support is not yet proven and remains capability-gated.
