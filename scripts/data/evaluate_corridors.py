#!/usr/bin/env python3
"""Measure OSM railway coverage in reproducible candidate bounding boxes."""
from __future__ import annotations
import json, math, pathlib, time, urllib.parse, urllib.request

CANDIDATES = {
    "rapperswil_uznach": (47.214, 8.812, 47.242, 8.998),
    "olten_lenzburg": (47.333, 7.895, 47.405, 8.187),
    "bern_thun_north": (46.829, 7.423, 46.950, 7.641),
    "luzern_sursee_south": (47.046, 8.075, 47.166, 8.312),
    "basel_liestal": (47.472, 7.577, 47.563, 7.747),
}
OVERPASS = "https://overpass-api.de/api/interpreter"

def length(coords):
    total=0.0
    for (a,b),(c,d) in zip(coords,coords[1:]):
        y=math.radians((a+c)/2)
        total += math.hypot((c-a)*111_320, (d-b)*111_320*math.cos(y))
    return total

def query(box):
    b=','.join(map(str,box))
    q=f'''[out:json][timeout:90];(
way[railway=rail][service!~"yard|siding|spur"]({b});
node[railway~"signal|switch|station|halt"]({b});
way[railway=platform]({b}););out body geom;'''
    req=urllib.request.Request(OVERPASS,data=urllib.parse.urlencode({'data':q}).encode(),headers={'User-Agent':'open-swiss-rail-sim/0.1 research'})
    with urllib.request.urlopen(req,timeout=120) as r: return json.load(r)

def analyse(data):
    ways=[e for e in data['elements'] if e['type']=='way' and e.get('tags',{}).get('railway')=='rail']
    nodes=[e for e in data['elements'] if e['type']=='node']
    km=sum(length([(p['lat'],p['lon']) for p in w.get('geometry',[])]) for w in ways)/1000
    def n(v): return sum(x.get('tags',{}).get('railway')==v for x in nodes)
    speed_km=sum(length([(p['lat'],p['lon']) for p in w.get('geometry',[])]) for w in ways if any(k.startswith('maxspeed') for k in w.get('tags',{})))/1000
    electrified_km=sum(length([(p['lat'],p['lon']) for p in w.get('geometry',[])]) for w in ways if w.get('tags',{}).get('electrified')=='contact_line')/1000
    tunnel_km=sum(length([(p['lat'],p['lon']) for p in w.get('geometry',[])]) for w in ways if w.get('tags',{}).get('tunnel') in ('yes','building_passage'))/1000
    return {'track_km':round(km,1),'signals':n('signal'),'signals_per_km':round(n('signal')/km,2) if km else 0,'switches':n('switch'),'stations_halts':n('station')+n('halt'),'platform_ways':sum(e.get('tags',{}).get('railway')=='platform' for e in data['elements']),'maxspeed_coverage_pct':round(100*speed_km/km) if km else 0,'electrification_pct':round(100*electrified_km/km) if km else 0,'tunnel_pct':round(100*tunnel_km/km) if km else 0}

def main():
    out={}
    cache=pathlib.Path('data/intermediate/candidates');cache.mkdir(parents=True,exist_ok=True)
    for name,box in CANDIDATES.items():
        path=cache/f'{name}.json'
        if path.exists(): data=json.loads(path.read_text())
        else:
            data=query(box);path.write_text(json.dumps(data));time.sleep(2)
        out[name]=analyse(data);print(name,out[name])
    pathlib.Path('data/manifests').mkdir(parents=True,exist_ok=True)
    pathlib.Path('data/manifests/corridor-comparison.json').write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__': main()

