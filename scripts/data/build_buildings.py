#!/usr/bin/env python3
"""Fetch corridor swissBUILDINGS3D CityGML and create batched Float32 meshes."""
from __future__ import annotations
import hashlib, io, json, pathlib, struct, urllib.parse, urllib.request, zipfile
import xml.etree.ElementTree as ET

PRODUCT='ch.swisstopo.swissbuildings3d_3_0'; API='https://ogd.swisstopo.admin.ch/services/swiseld/services'
RAW=pathlib.Path('data/raw/scenery/buildings');OUT=pathlib.Path('public/data/rapperswil-uznach/buildings')
MANIFEST=pathlib.Path('public/data/rapperswil-uznach/manifest.json');SCENERY=pathlib.Path('public/data/rapperswil-uznach/scenery-manifest.json')
GML='{http://www.opengis.net/gml}';BLDG='{http://www.opengis.net/citygml/building/2.0}'

def assets(bounds):
    query={'format':'application/x.gml+zip','srid':'2056','state':'current','variant':'tiled','xMin':bounds[0],'xMax':bounds[1],'yMin':bounds[2],'yMax':bounds[3]}
    url=f'{API}/assets/{PRODUCT}/search?'+urllib.parse.urlencode(query)
    try:
        with urllib.request.urlopen(url,timeout=60) as r:return json.load(r)['items']
    except Exception as exc:raise RuntimeError(f'official swissBUILDINGS3D asset search failed: {exc}') from exc

def download(asset):
    path=RAW/asset['ass_asset_id']
    if path.exists() and path.stat().st_size>100:return path
    print('download',path.name)
    try:
        with urllib.request.urlopen(asset['ass_asset_href'],timeout=180) as r:path.write_bytes(r.read())
    except Exception as exc:raise RuntimeError(f'building tile download failed ({path.name}): {exc}') from exc
    return path

def main():
    origin=json.loads(MANIFEST.read_text())['localOrigin'];oe,on,oh=origin['easting'],origin['northing'],origin['elevation']
    scenery=json.loads(SCENERY.read_text());local=(-1500,13725,-1500,2025);lv95=(oe+local[0],oe+local[1],on-local[3],on-local[2]);RAW.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    tile_ranges=[(x['bounds']['minX'],x['bounds']['maxX']) for x in scenery['tiles']];points=[[] for _ in tile_ranges];point_maps=[{} for _ in tile_ranges];indices=[[] for _ in tile_ranges];counts=[0]*len(tile_ranges);source_assets=[]
    for asset in assets(lv95):
        path=download(asset);source_assets.append(asset['ass_asset_id'])
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if not name.lower().endswith('.gml'):continue
                with archive.open(name) as stream:
                    for _,building in ET.iterparse(stream,events=('end',)):
                        if building.tag!=BLDG+'Building':continue
                        polygons=[];all_points=[]
                        for pos in building.iter(GML+'posList'):
                            values=[float(x) for x in (pos.text or '').split()];poly_points=[values[i:i+3] for i in range(0,len(values)-2,3)]
                            if len(poly_points)>2:polygons.append(poly_points);all_points.extend(poly_points)
                        if all_points:
                            cx=sum(p[0] for p in all_points)/len(all_points);cz=on-sum(p[1] for p in all_points)/len(all_points)
                            lx=cx-oe
                            if local[0]<=lx<=local[1] and local[2]<=cz<=local[3]:
                                ti=next((i for i,(a,b) in enumerate(tile_ranges) if a<=lx<=b),None)
                                if ti is not None:
                                    counts[ti]+=1
                                    for poly in polygons:
                                        # CityGML roof/wall rings are planar and normally convex; fan triangles preserve LOD2 surfaces.
                                        ring=poly[:-1] if poly[0]==poly[-1] else poly
                                        for i in range(1,len(ring)-1):
                                            for p in (ring[0],ring[i],ring[i+1]):
                                                value=(round(p[0]-oe,3),round(p[2]-oh,3),round(on-p[1],3));idx=point_maps[ti].get(value)
                                                if idx is None:idx=len(points[ti])//3;point_maps[ti][value]=idx;points[ti].extend(value)
                                                indices[ti].append(idx)
                        building.clear()
    runtime=[];total_bytes=0
    for i,data in enumerate(points):
        pos=struct.pack('<%sf'%len(data),*data);idx=struct.pack('<%sI'%len(indices[i]),*indices[i]);digest=hashlib.sha256(pos+idx).hexdigest()[:10];pname=f'tile-{i}-{digest}.positions.bin';iname=f'tile-{i}-{digest}.indices.bin'
        for stale in OUT.glob(f'tile-{i}-*.bin'):stale.unlink()
        (OUT/pname).write_bytes(pos);(OUT/iname).write_bytes(idx);size=len(pos)+len(idx);total_bytes+=size;runtime.append({'positions':'./buildings/'+pname,'indices':'./buildings/'+iname,'buildingCount':counts[i],'vertices':len(data)//3,'triangles':len(indices[i])//3,'bytes':size})
    scenery['buildings']={'source':'swissBUILDINGS3D 3.0 CityGML','classification':'REAL','format':'indexed Float32 positions + Uint32 indices','tiles':runtime,'sourceAssets':source_assets}
    SCENERY.write_text(json.dumps(scenery,indent=2)+'\n')
    print(json.dumps({'buildings':sum(counts),'uniqueVertices':sum(len(x)//3 for x in points),'triangles':sum(len(x)//3 for x in indices),'bytes':total_bytes,'perTile':counts},indent=2))
if __name__=='__main__':main()
