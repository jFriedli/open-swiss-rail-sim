#!/usr/bin/env python3
"""Sample a real swissALTI3D cross-route terrain grid from geo.admin.ch."""
import concurrent.futures, json, math, pathlib, time, urllib.request
PATH=pathlib.Path('public/data/rapperswil-uznach/route.json')
CACHE=pathlib.Path('data/intermediate/terrain-heights.json')
OFFSETS=(-1200,-700,-350,0,350,700,1200)
data=json.loads(PATH.read_text()); points=data['points']; manifest=json.loads(PATH.with_name('manifest.json').read_text()); origin=manifest['localOrigin'];cache=json.loads(CACHE.read_text()) if CACHE.exists() else {}
def get(item):
    i,o,e,n=item;key=f'{e:.1f},{n:.1f}'
    if key in cache:return i,o,cache[key]
    url=f'https://api3.geo.admin.ch/rest/services/height?easting={e:.1f}&northing={n:.1f}'
    for delay in (0,1,3):
        time.sleep(delay)
        try:
            with urllib.request.urlopen(url,timeout=20) as r:return i,o,float(json.load(r)['height'])
        except Exception:pass
    raise RuntimeError(key)
jobs=[]
for i,p in enumerate(points):
    a=points[max(0,i-1)];b=points[min(len(points)-1,i+1)];dx=b['x']-a['x'];dz=b['z']-a['z'];ln=math.hypot(dx,dz);nx=-dz/ln;nz=dx/ln
    for o in OFFSETS:jobs.append((i,o,origin['easting']+p['x']+nx*o,origin['northing']-p['z']-nz*o))
rows=[None]*len(points)
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    for count,(i,o,h) in enumerate(ex.map(get,jobs)):
        if rows[i] is None:rows[i]=[]
        rows[i].append({'offset':o,'elevation':h,'y':round(h-origin['elevation'],2)})
        cache[f'{jobs[count][2]:.1f},{jobs[count][3]:.1f}']=h
        if count%100==0:print(count,'/',len(jobs));CACHE.write_text(json.dumps(cache))
for row in rows:row.sort(key=lambda x:x['offset'])
data['terrainRows']=rows;PATH.write_text(json.dumps(data,separators=(',',':')))
manifest['terrain'].update({'crossTrackOffsetsM':list(OFFSETS),'samples':len(jobs),'classification':'REAL elevation / DERIVED mesh'})
PATH.with_name('manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');CACHE.write_text(json.dumps(cache))
