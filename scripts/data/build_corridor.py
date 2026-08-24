#!/usr/bin/env python3
"""Build the compact Rapperswil–Uznach runtime package from cached OSM data.

Elevation samples come from the documented geo.admin.ch height service (Swiss
national elevation model). Runtime coordinates are local ENU-like metres.
"""
from __future__ import annotations
import collections, concurrent.futures, datetime, heapq, json, math, pathlib, statistics, time, urllib.request

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

def resample(path, spacing=25.0):
    """Uniformly resample the complete polyline without dropping edge distance."""
    cumulative=[0.0]
    for a,b in zip(path,path[1:]): cumulative.append(cumulative[-1]+dist(a,b))
    result=[];j=0
    for target in [i*spacing for i in range(math.floor(cumulative[-1]/spacing)+1)]+[cumulative[-1]]:
        while j+1<len(cumulative) and cumulative[j+1]<target:j+=1
        if j+1==len(path):result.append(path[-1]);continue
        span=cumulative[j+1]-cumulative[j];t=0 if span==0 else (target-cumulative[j])/span
        result.append((path[j][0]+(path[j+1][0]-path[j][0])*t,path[j][1]+(path[j+1][1]-path[j][1])*t))
    return result

def smooth_profile(values, spacing=25.0, sigma_m=175.0):
    """Median despike then Gaussian low-pass, preserving genuine long gradients."""
    median=[]
    for i in range(len(values)):median.append(statistics.median(values[max(0,i-2):min(len(values),i+3)]))
    radius=math.ceil(3*sigma_m/spacing);out=[]
    for i in range(len(values)):
        weighted=[(median[j],math.exp(-.5*((j-i)*spacing/sigma_m)**2)) for j in range(max(0,i-radius),min(len(values),i+radius+1))]
        out.append(sum(v*w for v,w in weighted)/sum(w for _,w in weighted))
    return out

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
    samples=resample(path);origin_ll=samples[0];oe,on=wgs_to_lv95(*origin_ll); heights=[]
    cache=pathlib.Path('data/intermediate/heights.json')
    hc=json.loads(cache.read_text()) if cache.exists() else {}
    def sample_height(ll):
        lat,lon=ll;key=f'{lat:.7f},{lon:.7f}'
        return key,hc.get(key) if key in hc else height(lat,lon)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
      for i,(key,value) in enumerate(ex.map(sample_height,samples)):
        hc[key]=value
        if i%50==0:print(f'elevation {i}/{len(samples)}');cache.write_text(json.dumps(hc))
    cache.write_text(json.dumps(hc));raw=[hc[f'{lat:.7f},{lon:.7f}'] for lat,lon in samples];smooth=smooth_profile(raw)
    cumulative=[0.0]
    for a,b in zip(samples,samples[1:]):cumulative.append(cumulative[-1]+dist(a,b))
    for i,(lat,lon) in enumerate(samples):
        key=f'{lat:.7f},{lon:.7f}'
        e,n=wgs_to_lv95(lat,lon);heights.append({'s':round(cumulative[i],2),'x':round(e-oe,2),'y':round(smooth[i]-smooth[0],3),'z':round(-(n-on),2),'lat':lat,'lon':lon,'rawElevation':raw[i],'elevation':round(smooth[i],3)})
    # Project mapped objects to nearest sampled route point and retain source tags.
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
    gradients=[]
    for i in range(len(smooth)):
        a=max(0,i-2);b=min(len(smooth)-1,i+2);gradients.append((smooth[b]-smooth[a])/(cumulative[b]-cumulative[a])*1000)
    profile={'method':'5-sample median + Gaussian low-pass (sigma 175 m)','minElevationM':round(min(smooth),2),'maxElevationM':round(max(smooth),2),'startElevationM':round(smooth[0],2),'endElevationM':round(smooth[-1],2),'minGradientPermille':round(min(gradients),2),'maxGradientPermille':round(max(gradients),2),'meanAbsoluteGradientPermille':round(sum(map(abs,gradients))/len(gradients),2)}
    manifest={'corridor':'Rapperswil–Uznach','sourceCrs':'EPSG:4326 → LV95 → local ENU-like','localOrigin':{'lat':origin_ll[0],'lon':origin_ll[1],'easting':oe,'northing':on,'elevation':heights[0]['elevation']},'bounds':{'routeLengthM':round(cumulative[-1],1)},'terrain':{'source':'swissALTI3D via geo.admin.ch height service','classification':'REAL'},'railway':{'source':'OpenStreetMap','routePoints':len(heights),'sampleSpacingM':25,'verticalProfile':profile,'signals':len(signals),'stations':len(stations),'speedSections':len(limits),'classification':'REAL / OPEN_MAPPING'},'sources':['swissALTI3D','OpenStreetMap'],'generatedAt':datetime.datetime.now(datetime.UTC).isoformat()}
    (OUT/'route.json').write_text(json.dumps({'points':heights,'signals':signals,'stations':stations,'speedLimits':limits},separators=(',',':')))
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
