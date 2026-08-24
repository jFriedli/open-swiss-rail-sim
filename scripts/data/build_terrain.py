#!/usr/bin/env python3
"""Build an axis-aligned, regular swissALTI3D terrain grid in local metres."""
import concurrent.futures,json,math,pathlib,time,urllib.request
ROUTE=pathlib.Path('public/data/rapperswil-uznach/route.json');OUT=ROUTE.with_name('terrain.json');CACHE=pathlib.Path('data/intermediate/terrain-grid-heights.json');SPACING=75;SOURCE_SPACING=300;BUFFER=1200
data=json.loads(ROUTE.read_text());points=data['points'];manifest=json.loads(ROUTE.with_name('manifest.json').read_text());origin=manifest['localOrigin'];cache=json.loads(CACHE.read_text()) if CACHE.exists() else {}
min_x=math.floor((min(p['x'] for p in points)-BUFFER)/SPACING)*SPACING;max_x=math.ceil((max(p['x'] for p in points)+BUFFER)/SPACING)*SPACING
min_z=math.floor((min(p['z'] for p in points)-BUFFER)/SPACING)*SPACING;max_z=math.ceil((max(p['z'] for p in points)+BUFFER)/SPACING)*SPACING
width=round((max_x-min_x)/SPACING)+1;height=round((max_z-min_z)/SPACING)+1
def get(job):
    i,e,n=job;key=f'{e:.1f},{n:.1f}'
    if key in cache:return i,key,cache[key]
    url=f'https://api3.geo.admin.ch/rest/services/height?easting={e:.1f}&northing={n:.1f}'
    for delay in (0,1,3,7):
        time.sleep(delay)
        try:
            with urllib.request.urlopen(url,timeout=25) as r:return i,key,float(json.load(r)['height'])
        except Exception:pass
    raise RuntimeError(f'height request failed {key}')
source_width=math.ceil((max_x-min_x)/SOURCE_SPACING)+1;source_height=math.ceil((max_z-min_z)/SOURCE_SPACING)+1;jobs=[]
for row in range(source_height):
    z=min(max_z,min_z+row*SOURCE_SPACING)
    for col in range(source_width):
        x=min(max_x,min_x+col*SOURCE_SPACING);jobs.append((row*source_width+col,origin['easting']+x,origin['northing']-z))
source_heights=[0.0]*len(jobs)
with concurrent.futures.ThreadPoolExecutor(max_workers=24) as ex:
    for count,(i,key,value) in enumerate(ex.map(get,jobs)):
        source_heights[i]=value-origin['elevation'];cache[key]=value
        if count%500==0:print(count,'/',len(jobs));CACHE.write_text(json.dumps(cache))
CACHE.write_text(json.dumps(cache));heights=[]
# Bilinear resampling onto the stable 75 m render grid. Source samples remain real;
# interpolated vertices are explicitly derived.
for row in range(height):
    gz=(row*SPACING)/SOURCE_SPACING;r0=min(source_height-2,math.floor(gz));tz=gz-r0
    for col in range(width):
        gx=(col*SPACING)/SOURCE_SPACING;c0=min(source_width-2,math.floor(gx));tx=gx-c0
        a=source_heights[r0*source_width+c0];b=source_heights[r0*source_width+c0+1];c=source_heights[(r0+1)*source_width+c0];d=source_heights[(r0+1)*source_width+c0+1]
        heights.append((a*(1-tx)+b*tx)*(1-tz)+(c*(1-tx)+d*tx)*tz)
# Derived cut/fill envelope: a coarse DTM must not bridge across the railway.
# Blend the terrain to 0.35 m below the smoothed formation inside 180 m.
for row in range(height):
    z=min_z+row*SPACING
    for col in range(width):
        x=min_x+col*SPACING;i=row*width+col
        nearest=min(points,key=lambda p:(p['x']-x)**2+(p['z']-z)**2);distance=math.hypot(nearest['x']-x,nearest['z']-z)
        if distance<180:
            target=nearest['y']-.35
            weight=1 if distance<=75 else (180-distance)/105
            heights[i]=heights[i]*(1-weight)+target*weight
max_delta=0
for r in range(height):
    for c in range(width):
        i=r*width+c
        if c+1<width:max_delta=max(max_delta,abs(heights[i+1]-heights[i]))
        if r+1<height:max_delta=max(max_delta,abs(heights[i+width]-heights[i]))
stats={'vertices':len(heights),'triangles':(width-1)*(height-1)*2,'minElevationM':round(min(heights)+origin['elevation'],2),'maxElevationM':round(max(heights)+origin['elevation'],2),'largestTriangleEdgeM':round(SPACING*math.sqrt(2),2),'maxNeighbourElevationDeltaM':round(max_delta,2)}
payload={'originX':min_x,'originZ':min_z,'spacingM':SPACING,'sourceSpacingM':SOURCE_SPACING,'width':width,'height':height,'heights':[round(h,2) for h in heights],'source':'swissALTI3D via geo.admin.ch','classification':'REAL 300 m samples / DERIVED 75 m bilinear grid and triangulation','stats':stats}
OUT.write_text(json.dumps(payload,separators=(',',':')));manifest['terrain'].update({'classification':'REAL samples / DERIVED grid, interpolation and railway cut-fill','gridSpacingM':SPACING,'sourceSpacingM':SOURCE_SPACING,'width':width,'height':height,'extentM':{'x':max_x-min_x,'z':max_z-min_z},'stats':stats});ROUTE.with_name('manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest['terrain'],indent=2))
