# Rapperswil–Uznach vertical profile

The 13,468.3 m route is sampled every 25 m from swissALTI3D. Ground-height spikes are first removed with a centred five-sample median filter. A Gaussian low-pass filter with σ=175 m then produces the derived railway vertical profile; this preserves kilometre-scale gradients while avoiding the false assumption that rails follow every DTM bump.

| Measure | Value |
|---|---:|
| Start elevation | 408.69 m |
| End elevation | 410.18 m |
| Minimum elevation | 408.00 m |
| Maximum elevation | 415.87 m |
| Minimum gradient | −5.01 ‰ |
| Maximum gradient | +9.11 ‰ |
| Mean absolute gradient | 2.81 ‰ |

The previous runtime differentiated a sparse spline that contained two approximately 780 m sampling gaps and unsmoothed DTM heights. That produced unstable local gradients, including visually reported values around 44 ‰. Uniform resampling and the documented low-pass profile remove that processing artefact; no gradient clamp is used. The profile remains a terrain-derived approximation rather than surveyed railway vertical alignment.
