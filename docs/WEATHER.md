# Weather

Bundled service-date weather comes from MeteoSwiss automatic weather station open data, collection `ch.meteoschweiz.ogd-smn`, accessed through the official federal STAC API. The committed 22 August 2026 field contains 120 hourly samples from Lachen/Galgenen, Gösgen, Buchs/Aarau, Bern/Zollikofen and Zürich/Kloten. The browser interpolates in time and inverse-distance blends the nearest three stations.

Observed variables are air temperature, relative humidity, hourly precipitation, wind speed and wind direction. Cloud cover and visibility are derived from humidity, sunshine duration and precipitation because those are not direct fields in this station product. The UI labels the station input `HISTORICAL`; cloud, visibility, particles, wetness and snow remain derived/simulated. Source attribution is “Source: MeteoSwiss”. The data is reusable under MeteoSwiss open-data terms.

Regenerate the compact snapshot while retaining raw downloads in the ignored cache:

```sh
python3 scripts/data/fetch_weather.py --date 2026-08-22
```

The static snapshot avoids a runtime dependency and CORS/network failure during driving. If the date-specific file is unavailable, the environment falls back to clear custom conditions. Current live ICON-CH forecasts are official but large GRIB products with a short availability window; they are not fetched by the browser. This release therefore does not advertise live weather.

Precipitation intensity uses a logarithmic mapping from mm/h. Wetness rises during rain and dries slowly after it. Rain darkens shared surface shaders and reduces rail roughness. Fog density is derived from visibility. A single weather wind vector drives precipitation drift and is available for clouds/vegetation.

Snowfall occurs when precipitation coincides with an elevation-adjusted temperature at or below 1.2 °C. Temperature uses a 6.5 K/km lapse-rate approximation. Cover accumulates with snowfall and melts with warm air and daylight. Terrain and upward roof surfaces receive most cover; roads, ballast and rails receive reduced cover. This is a visual derived model, not a snowpack forecast.

