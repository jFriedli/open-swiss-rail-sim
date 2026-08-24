#!/usr/bin/env python3
import json,math,pathlib
p=pathlib.Path('public/data/rapperswil-uznach/route.json');d=json.loads(p.read_text());t=json.loads(p.with_name('terrain.json').read_text());pts=d['points'];bad=[]
for i,(a,b) in enumerate(zip(pts,pts[1:])):
    gap=math.hypot(b['x']-a['x'],b['z']-a['z'])
    if not 0<gap<1000:bad.append(f'impossible segment {i}: {gap}')
    if abs(b['elevation']-a['elevation'])>30:bad.append(f'elevation spike {i}')
assert not bad,'\n'.join(bad)
assert len(t['heights'])==t['width']*t['height']
assert all(math.isfinite(h) for h in t['heights'])
assert t['stats']['largestTriangleEdgeM']<150
assert t['stats']['maxNeighbourElevationDeltaM']<50
print(f"Route points: {len(pts)}\nSignals matched: {len(d['signals'])}\nStations matched: {len(d['stations'])}\nSpeed sections: {len(d['speedLimits'])}\nTerrain vertices: {len(t['heights'])}\nTerrain triangles: {t['stats']['triangles']}\nValidation errors: 0")
