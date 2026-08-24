#!/usr/bin/env python3
"""Fetch official SWISSIMAGE WMS crops and build hashed WebP scenery tiles."""
from __future__ import annotations
import hashlib,json,math,pathlib,urllib.parse,urllib.request
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[2];CORRIDOR=ROOT/'public/data/rapperswil-uznach';RAW=ROOT/'data/raw/scenery/swissimage';RAW.mkdir(parents=True,exist_ok=True)
terrain=json.loads((CORRIDOR/'terrain.json').read_text());base=json.loads((CORRIDOR/'manifest.json').read_text());origin=base['localOrigin'];out_dir=CORRIDOR/'imagery';out_dir.mkdir(exist_ok=True)
splits=[0,51,102,153,terrain['width']-1];tiles=[]
for index,(c0,c1) in enumerate(zip(splits,splits[1:])):
    x0=terrain['originX']+c0*terrain['spacingM'];x1=terrain['originX']+c1*terrain['spacingM'];z0=terrain['originZ'];z1=z0+(terrain['height']-1)*terrain['spacingM']
    bbox=(origin['easting']+x0,origin['northing']-z1,origin['easting']+x1,origin['northing']-z0)
    width=2048;height=round(width*(z1-z0)/(x1-x0));params={'SERVICE':'WMS','VERSION':'1.1.1','REQUEST':'GetMap','LAYERS':'ch.swisstopo.swissimage','STYLES':'','SRS':'EPSG:2056','BBOX':','.join(f'{v:.3f}' for v in bbox),'WIDTH':width,'HEIGHT':height,'FORMAT':'image/jpeg'}
    url='https://wms.geo.admin.ch/?'+urllib.parse.urlencode(params);raw=RAW/f'tile-{index}-{width}x{height}.jpg'
    if not raw.exists():
        print('fetch',index,url)
        try:urllib.request.urlretrieve(url,raw)
        except Exception as e:raise RuntimeError(f'SWISSIMAGE tile {index} failed: {e}') from e
    with Image.open(raw) as image:
        if image.size!=(width,height):raise RuntimeError(f'invalid WMS image dimensions {image.size}')
        temp=out_dir/f'tile-{index}.webp';image.save(temp,'WEBP',quality=78,method=6)
    digest=hashlib.sha256(temp.read_bytes()).hexdigest()[:10];final=out_dir/f'tile-{index}-{digest}.webp';temp.replace(final)
    for stale in out_dir.glob(f'tile-{index}-*.webp'):
        if stale!=final:stale.unlink()
    tiles.append({'id':f'scenery-{index}','bounds':{'minX':x0,'maxX':x1,'minZ':z0,'maxZ':z1},'terrain':{'columnStart':c0,'columnEnd':c1},'imagery':{'url':f'./imagery/{final.name}','format':'WebP','width':width,'height':height,'metresPerPixel':round((x1-x0)/width,3),'source':'SWISSIMAGE via official WMS','classification':'REAL'}})
manifest={'corridor':'rapperswil-uznach','version':2,'crs':'EPSG:2056 → local X east, Y up, Z south','localOrigin':origin,'tiles':tiles,'sources':[{'dataset':'SWISSIMAGE','publisher':'Federal Office of Topography swisstopo','access':'https://wms.geo.admin.ch/','attribution':'© swisstopo'}]}
(CORRIDOR/'scenery-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'tiles':len(tiles),'bytes':sum((ROOT/'public/data/rapperswil-uznach'/t['imagery']['url'][2:]).stat().st_size for t in tiles)},indent=2))
