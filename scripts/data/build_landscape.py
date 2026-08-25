#!/usr/bin/env python3
"""Build compact OSM landscape layers in the simulator's canonical local frame.

Raw Overpass responses are cached under data/raw/scenery and are never committed.
The output contains real mapped geometry plus deterministic tree samples derived
from mapped forest polygons. swissTLM3D remains the preferred future source for
official landscape polygons; OSM is used here because it supports a genuinely
corridor-sized, reproducible extract.
"""
from __future__ import annotations
import json, math, pathlib, random, urllib.parse, urllib.request

RAW=pathlib.Path('data/raw/scenery/osm-landscape.json')
OUT=pathlib.Path('public/data/rapperswil-uznach/landscape.json')
PACKAGE=pathlib.Path('public/data/rapperswil-uznach/package.json')
ROUTE=pathlib.Path('public/data/rapperswil-uznach/route.json')
QUERY='''[out:json][timeout:180];(way[natural=water](47.195,8.79,47.255,9.02);relation[natural=water](47.195,8.79,47.255,9.02);way[landuse=forest](47.195,8.79,47.255,9.02);way[natural=wood](47.195,8.79,47.255,9.02);way[highway~"motorway|trunk|primary|secondary|tertiary|residential"](47.195,8.79,47.255,9.02);way[railway=platform](47.195,8.79,47.255,9.02););out geom;'''

def wgs_to_lv95(lat,lon):
    p=(lat*3600-169028.66)/10000; l=(lon*3600-26782.5)/10000
    return (2600072.37+211455.93*l-10938.51*l*p-.36*l*p*p-44.54*l*l*l,
            1200147.07+308807.95*p+3745.25*l*l+76.63*p*p-194.56*l*l*p+119.79*p*p*p)

def fetch():
    if RAW.exists(): return
    RAW.parent.mkdir(parents=True,exist_ok=True)
    request=urllib.request.Request('https://overpass-api.de/api/interpreter',urllib.parse.urlencode({'data':QUERY}).encode())
    try:
        with urllib.request.urlopen(request,timeout=240) as response: RAW.write_bytes(response.read())
    except Exception as exc: raise RuntimeError(f'Overpass landscape download failed: {exc}') from exc

def assemble(parts):
    """Join relation member fragments by matching endpoints (OSM multipolygon outer rings)."""
    remaining=[p[:] for p in parts if len(p)>1]; rings=[]
    while remaining:
        ring=remaining.pop()
        changed=True
        while changed and ring[0]!=ring[-1]:
            changed=False
            for i,p in enumerate(remaining):
                if ring[-1]==p[0]: ring.extend(p[1:])
                elif ring[-1]==p[-1]: ring.extend(reversed(p[:-1]))
                elif ring[0]==p[-1]: ring=p[:-1]+ring
                elif ring[0]==p[0]: ring=list(reversed(p[1:]))+ring
                else: continue
                remaining.pop(i);changed=True;break
        if len(ring)>3 and ring[0]==ring[-1]:rings.append(ring)
    return rings

def inside(point,poly):
    x,z=point; hit=False
    for a,b in zip(poly,poly[1:]):
        if (a[1]>z)!=(b[1]>z) and x < (b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]: hit=not hit
    return hit

def clip(poly,bounds):
    """Sutherland–Hodgman clip against the rectangular runtime extent."""
    output=poly[:-1] if poly and poly[0]==poly[-1] else poly[:]
    tests=[(lambda p:p[0]>=bounds[0],lambda a,b:(bounds[0],a[1]+(b[1]-a[1])*(bounds[0]-a[0])/(b[0]-a[0]))),
           (lambda p:p[0]<=bounds[1],lambda a,b:(bounds[1],a[1]+(b[1]-a[1])*(bounds[1]-a[0])/(b[0]-a[0]))),
           (lambda p:p[1]>=bounds[2],lambda a,b:(a[0]+(b[0]-a[0])*(bounds[2]-a[1])/(b[1]-a[1]),bounds[2])),
           (lambda p:p[1]<=bounds[3],lambda a,b:(a[0]+(b[0]-a[0])*(bounds[3]-a[1])/(b[1]-a[1]),bounds[3]))]
    for keep,cross in tests:
        source=output;output=[]
        if not source:break
        previous=source[-1]
        for current in source:
            if keep(current):
                if not keep(previous):output.append(cross(previous,current))
                output.append(current)
            elif keep(previous):output.append(cross(previous,current))
            previous=current
    return [[round(x,1),round(z,1)] for x,z in output]+([[round(output[0][0],1),round(output[0][1],1)]] if output else [])

def main():
    fetch(); raw=json.loads(RAW.read_text()); origin=json.loads(PACKAGE.read_text())['localOriginLv95'];oe,on=origin['easting'],origin['northing']
    route=[(p['x'],p['z']) for p in json.loads(ROUTE.read_text())['points']]
    def clear_of_track(p):
        for a,b in zip(route,route[1:]):
            dx=b[0]-a[0];dz=b[1]-a[1];d2=dx*dx+dz*dz;t=0 if d2==0 else max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dz)/d2));q=(a[0]+t*dx,a[1]+t*dz)
            if math.hypot(p[0]-q[0],p[1]-q[1])<18:return False
        return True
    def local(points):
        result=[]
        for p in points:
            e,n=wgs_to_lv95(p['lat'],p['lon']);result.append([round(e-oe,1),round(on-n,1)])
        return result
    bounds=(-1500,13725,-1500,2025)
    def relevant(p): return any(bounds[0]-100<=x<=bounds[1]+100 and bounds[2]-100<=z<=bounds[3]+100 for x,z in p)
    water=[];forests=[];roads=[];platforms=[]
    for e in raw['elements']:
        tags=e.get('tags',{}); geom=e.get('geometry')
        if e['type']=='way' and geom:
            p=local(geom)
            if not relevant(p):continue
            if tags.get('natural')=='water' and len(p)>3 and p[0]==p[-1]:water.append(clip(p,bounds))
            if (tags.get('landuse')=='forest' or tags.get('natural')=='wood') and len(p)>3 and p[0]==p[-1]:forests.append(clip(p,bounds))
            if 'highway' in tags:roads.append({'class':tags['highway'],'points':p})
            if tags.get('railway')=='platform' and len(p)>2:platforms.append(p)
        if e['type']=='relation' and tags.get('natural')=='water':
            parts=[]
            for m in e.get('members',[]):
                if m.get('role')=='outer' and m.get('geometry'):parts.append([(round(x['lat'],7),round(x['lon'],7)) for x in m['geometry']])
            for ring in assemble(parts):
                p=local([{'lat':a,'lon':b} for a,b in ring])
                if relevant(p): water.append(clip(p,bounds))
    water=[p for p in water if len(p)>3];forests=[p for p in forests if len(p)>3]
    # Deterministic, modest-density synthetic tree positions within real forest boundaries.
    rng=random.Random(471347);trees=[]
    for poly in forests:
        minx=max(bounds[0],min(x for x,_ in poly));maxx=min(bounds[1],max(x for x,_ in poly));minz=max(bounds[2],min(z for _,z in poly));maxz=min(bounds[3],max(z for _,z in poly))
        for x in range(math.floor(minx/28)*28,math.ceil(maxx/28)*28,28):
            for z in range(math.floor(minz/28)*28,math.ceil(maxz/28)*28,28):
                p=(x+rng.uniform(-8,8),z+rng.uniform(-8,8))
                if inside(p,poly) and clear_of_track(p):trees.append([round(p[0],1),round(p[1],1),round(rng.uniform(.8,1.3),2)])
    length=sum(math.hypot(b[0]-a[0],b[1]-a[1]) for r in roads for a,b in zip(r['points'],r['points'][1:]))
    payload={'version':1,'crs':'EPSG:2056 → canonical local X east / Z south','water':water,'forests':forests,'trees':trees,'roads':roads,'platforms':platforms,'stats':{'waterPolygons':len(water),'forestPolygons':len(forests),'treeInstances':len(trees),'roadFeatures':len(roads),'roadLengthM':round(length),'platforms':len(platforms)},'sources':{'geometry':'OpenStreetMap contributors, ODbL','trees':'DERIVED deterministic samples inside mapped forest polygons'}}
    OUT.write_text(json.dumps(payload,separators=(',',':')));print(json.dumps(payload['stats'],indent=2));print(f'{OUT}: {OUT.stat().st_size/1e6:.2f} MB')
if __name__=='__main__':main()
