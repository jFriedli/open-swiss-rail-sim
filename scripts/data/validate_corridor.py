#!/usr/bin/env python3
import array,json,math,pathlib
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
land=json.loads(p.with_name('landscape.json').read_text());assert land['stats']['waterPolygons']>0 and land['stats']['treeInstances']>100 and land['stats']['platforms']>0
assert all(math.isfinite(v) for tree in land['trees'] for v in tree)
scenery=json.loads(p.with_name('scenery-manifest.json').read_text());building_count=0;building_triangles=0
for tile in scenery['buildings']['tiles']:
    for surface in tile['surfaces'].values():
        if not surface['triangles']:
            assert surface['vertices']==surface['bytes']==0
            continue
        pos_path=p.parent/surface['positions'].removeprefix('./');idx_path=p.parent/surface['indices'].removeprefix('./');colour_path=p.parent/surface['colors'].removeprefix('./')
        assert pos_path.stat().st_size==surface['vertices']*12 and idx_path.stat().st_size==surface['triangles']*12 and colour_path.stat().st_size==surface['vertices']*3
        indices=array.array('I');indices.frombytes(idx_path.read_bytes())
        if indices:assert max(indices)<surface['vertices']
        building_triangles+=surface['triangles']
    building_count+=tile['buildingCount']
alignment=json.loads(pathlib.Path('data/manifests/building-alignment.json').read_text());assert building_count==alignment['buildings']==7965 and building_triangles>400_000
assert alignment['semanticPolygons']['roof']>0 and alignment['semanticPolygons']['wall']>0 and alignment['corrected']>7000
print(f"Route points: {len(pts)}\nSignals matched: {len(d['signals'])}\nStations matched: {len(d['stations'])}\nSpeed sections: {len(d['speedLimits'])}\nTerrain vertices: {len(t['heights'])}\nTerrain triangles: {t['stats']['triangles']}\nWater polygons: {land['stats']['waterPolygons']}\nTree instances: {land['stats']['treeInstances']}\nBuildings: {building_count}\nBuilding triangles: {building_triangles}\nValidation errors: 0")
