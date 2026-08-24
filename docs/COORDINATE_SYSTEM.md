# Coordinate system and route frame

The source alignment is WGS84 (`EPSG:4326`). Preprocessing applies swisstopo's published approximate WGS84→LV95 conversion and records the LV95 origin in the corridor manifest. Runtime coordinates subtract that origin and use metres:

- **X**: local east
- **Y**: up, relative to the origin elevation
- **Z**: local south (negative LV95 northing)

One Three.js unit is one metre. `TrackFrameSampler.sample(s)` is the sole railway placement convention. It returns centre position, unit tangent, horizontal no-cant right vector, corrected up vector, orientation quaternion, and gradient at arc distance `s`. Local object axes are +X right, +Y up and +Z forward. The stable right vector is `worldUp × horizontalTangent`; this avoids Frenet normal flips on straight and low-curvature track. Superelevation is not modelled.

OSM supplies longitudinal signal positions after preprocessing. Their lateral offsets are inferred and therefore derived, not surveyed positions.
