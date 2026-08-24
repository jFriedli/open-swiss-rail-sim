#!/usr/bin/env python3
"""Build the compact Rapperswil–Uznach runtime package from cached OSM data.

Elevation samples come from the documented geo.admin.ch height service (Swiss
national elevation model). Runtime coordinates are local ENU-like metres.
"""
from __future__ import annotations
import collections, datetime, heapq, json, math, pathlib, time, urllib.request

SOURCE=pathlib.Path('data/intermediate/candidates/rapperswil_uznach.json')
OUT=pathlib.Path('public/data/rapperswil-uznach')
START=(47.2266,8.8163); END=(47.2253,8.9824)

def dist(a,b):
    y=math.radians((a[0]+b[0])/2)
    return math.hypot((a[0]-b[0])*111_320,(a[1]-b[1])*111_320*math.cos(y))

def wgs_to_lv95(lat,lon):
    # swisstopo's published approximate transformation, metre-level accuracy.
    p=(lat*3600-169028.66)/10000; l=(lon*3600-26782.5)/10000
    e=2600072.37+211455.93*l-10938.51*l*p-0.36*l*p*p-44.54*l*l*l
    n=1200147.07+308807.95*p+3745.25*l*l+76.63*p*p-194.56*l*l*p+119.79*p*p*p
    return e,n

def height(lat,lon):
    e,n=wgs_to_lv95(lat,lon)
    url=f'https://api3.geo.admin.ch/rest/services/height?easting={e:.2f}&northing={n:.2f}'
    for wait in (0,2,5):
        time.sleep(wait)
        try:
            with urllib.request.urlopen(url,timeout=20) as r: return float(json.load(r)['height'])
        except Exception:
            pass
    raise RuntimeError(f'height request failed: {lat},{lon}')

def main():
    data=json.loads(SOURCE.read_text()); coords={}; graph=collections.defaultdict(list); ways=[]
    for w in data['elements']:
        if w['type']!='way' or w.get('tags',{}).get('railway')!='rail': continue
        ids=w.get('nodes',[]); geom=w.get('geometry',[])
        for i,p in enumerate(geom): coords[ids[i]]=(p['lat'],p['lon'])
        for a,b in zip(ids,ids[1:]):
            d=dist(coords[a],coords[b]);graph[a].append((b,d));graph[b].append((a,d))
        ways.append(w)
    def nearest(ll): return min(coords,key=lambda n:dist(ll,coords[n]))
    src,dst=nearest(START),nearest(END); q=[(0,src)]; cost={src:0}; prev={}
    while q:
        c,n=heapq.heappop(q)
        if n==dst: break
        if c!=cost[n]:continue
        for nxt,d in graph[n]:
            nc=c+d
            if nc<cost.get(nxt,1e30):cost[nxt]=nc;prev[nxt]=n;heapq.heappush(q,(nc,nxt))
    path=[];n=dst
    while True:
        path.append(coords[n])
        if n==src:break
        n=prev[n]
    path.reverse()
    # Resample to ~75 m so browser interpolation is smooth and API load bounded.
    samples=[path[0]]; carry=0
    for a,b in zip(path,path[1:]):
        seg=dist(a,b);carry+=seg
        if carry>=75:samples.append(b);carry=0
    if samples[-1]!=path[-1]:samples.append(path[-1])
    origin_ll=samples[0];oe,on=wgs_to_lv95(*origin_ll); heights=[]
    cache=pathlib.Path('data/intermediate/heights.json')
    hc=json.loads(cache.read_text()) if cache.exists() else {}
    for i,(lat,lon) in enumerate(samples):
        key=f'{lat:.7f},{lon:.7f}'
        if key not in hc: hc[key]=height(lat,lon);cache.write_text(json.dumps(hc));time.sleep(.05)
        e,n=wgs_to_lv95(lat,lon);heights.append({'x':round(e-oe,2),'y':round(hc[key]-hc[f"{samples[0][0]:.7f},{samples[0][1]:.7f}"],2),'z':round(-(n-on),2),'lat':lat,'lon':lon,'elevation':hc[key]})
        if i%25==0:print(f'elevation {i}/{len(samples)}')
    # Project mapped objects to nearest sampled route point and retain source tags.
    cumulative=[0.0]
    for a,b in zip(samples,samples[1:]):cumulative.append(cumulative[-1]+dist(a,b))
    def objects(kind):
        out=[]
        for e in data['elements']:
            if e['type']!='node' or e.get('tags',{}).get('railway')!=kind:continue
            ll=(e['lat'],e['lon']);i=min(range(len(samples)),key=lambda j:dist(ll,samples[j]))
            if dist(ll,samples[i])<120:out.append({'id':e['id'],'s':round(cumulative[i],1),'lat':ll[0],'lon':ll[1],'tags':e.get('tags',{}),'source':'OpenStreetMap'})
        return out
    signals=objects('signal');stations=objects('station')+objects('halt')
    limits=[]
    for w in ways:
        tag=w.get('tags',{}).get('maxspeed')
        if not tag or not str(tag).isdigit():continue
        near=[]
        for p in w.get('geometry',[]):
            ll=(p['lat'],p['lon']);i=min(range(len(samples)),key=lambda j:dist(ll,samples[j]))
            if dist(ll,samples[i])<25:near.append(cumulative[i])
        if near:limits.append({'start':round(min(near),1),'end':round(max(near),1),'speed':int(tag),'source':'OpenStreetMap','confidence':'OPEN_MAPPING'})
    OUT.mkdir(parents=True,exist_ok=True)
    manifest={'corridor':'Rapperswil–Uznach','sourceCrs':'EPSG:4326 / LV95 height queries','localOrigin':{'lat':origin_ll[0],'lon':origin_ll[1],'easting':oe,'northing':on,'elevation':heights[0]['elevation']},'bounds':{'routeLengthM':round(cumulative[-1],1)},'terrain':{'source':'swissALTI3D via geo.admin.ch height service','sampleSpacingM':75,'classification':'REAL'},'railway':{'source':'OpenStreetMap','routePoints':len(heights),'signals':len(signals),'stations':len(stations),'speedSections':len(limits),'classification':'REAL / OPEN_MAPPING'},'sources':['swissALTI3D','OpenStreetMap'],'generatedAt':datetime.datetime.now(datetime.UTC).isoformat()}
    (OUT/'route.json').write_text(json.dumps({'points':heights,'signals':signals,'stations':stations,'speedLimits':limits},separators=(',',':')))
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
