#!/usr/bin/env python3
import json,math,pathlib
p=pathlib.Path('public/data/rapperswil-uznach/route.json');d=json.loads(p.read_text());pts=d['points'];bad=[]
for i,(a,b) in enumerate(zip(pts,pts[1:])):
    gap=math.hypot(b['x']-a['x'],b['z']-a['z'])
    if not 0<gap<1000:bad.append(f'impossible segment {i}: {gap}')
    if abs(b['elevation']-a['elevation'])>30:bad.append(f'elevation spike {i}')
assert not bad,'\n'.join(bad)
print(f"Route points: {len(pts)}\nSignals matched: {len(d['signals'])}\nStations matched: {len(d['stations'])}\nSpeed sections: {len(d['speedLimits'])}\nTerrain samples: {len(pts)*len(d['terrainRows'][0])}\nValidation errors: 0")
