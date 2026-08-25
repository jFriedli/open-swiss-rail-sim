#!/usr/bin/env python3
"""Build grounded, semantic, batched swissBUILDINGS3D runtime meshes."""
from __future__ import annotations
import argparse,hashlib,json,math,pathlib,statistics,struct,urllib.parse,urllib.request,zipfile
import xml.etree.ElementTree as ET
from PIL import Image

PRODUCT='ch.swisstopo.swissbuildings3d_3_0';API='https://ogd.swisstopo.admin.ch/services/swiseld/services'
RAW=pathlib.Path('data/raw/scenery/buildings')
GML='{http://www.opengis.net/gml}';BLDG='{http://www.opengis.net/citygml/building/2.0}';SURFACES={'roof':BLDG+'RoofSurface','wall':BLDG+'WallSurface','ground':BLDG+'GroundSurface','other':BLDG+'ClosureSurface'}
WALL_PALETTE=((196,184,160),(181,181,174),(209,193,155),(169,181,184),(198,169,145),(184,151,137),(207,202,187))

def assets(bounds):
    query={'format':'application/x.gml+zip','srid':2056,'state':'current','variant':'tiled','xMin':bounds[0],'xMax':bounds[1],'yMin':bounds[2],'yMax':bounds[3]}
    try:
        with urllib.request.urlopen(f'{API}/assets/{PRODUCT}/search?'+urllib.parse.urlencode(query),timeout=60) as r:return json.load(r)['items']
    except Exception as exc:raise RuntimeError(f'official swissBUILDINGS3D asset search failed: {exc}') from exc

def download(asset):
    path=RAW/asset['ass_asset_id']
    if path.exists() and path.stat().st_size>100:return path
    print('download',path.name)
    try:
        with urllib.request.urlopen(asset['ass_asset_href'],timeout=180) as r:path.write_bytes(r.read())
    except Exception as exc:raise RuntimeError(f'building tile download failed ({path.name}): {exc}') from exc
    return path

def polygons(element):
    result=[]
    for pos in element.iter(GML+'posList'):
        values=[float(x) for x in (pos.text or '').split()]
        if len(values)%3:continue
        points=[values[i:i+3] for i in range(0,len(values),3)]
        if len(points)>3 and all(math.isfinite(x) for p in points for x in p):result.append(points)
    return result

def percentile(values,p):
    ordered=sorted(values);return ordered[min(len(ordered)-1,round((len(ordered)-1)*p))]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--route',default='rapperswil-uznach');args=parser.parse_args();package_dir=pathlib.Path('public/data')/args.route;package_path=package_dir/'package.json';package=json.loads(package_path.read_text());SCENERY=package_dir/package['assets']['scenery'];TERRAIN=package_dir/package['assets']['terrain'];OUT=package_dir/'buildings';REPORT=pathlib.Path('data/manifests')/f'{args.route}-building-alignment.json'
    origin=package['localOriginLv95'];oe,on,oh=origin['easting'],origin['northing'],origin['elevation'];terrain=json.loads(TERRAIN.read_text());scenery=json.loads(SCENERY.read_text());bounds=[t['bounds'] for t in scenery['tiles']];local=(min(b['minX'] for b in bounds),max(b['maxX'] for b in bounds),min(b['minZ'] for b in bounds),max(b['maxZ'] for b in bounds));lv95=(oe+local[0],oe+local[1],on-local[3],on-local[2]);RAW.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True);REPORT.parent.mkdir(parents=True,exist_ok=True)
    def terrain_at(x,z):
        gx=max(0,min(terrain['width']-1.001,(x-terrain['originX'])/terrain['spacingM']));gz=max(0,min(terrain['height']-1.001,(z-terrain['originZ'])/terrain['spacingM']));x0=int(gx);z0=int(gz);tx=gx-x0;tz=gz-z0;h=terrain['heights'];w=terrain['width']
        return (h[z0*w+x0]*(1-tx)+h[z0*w+x0+1]*tx)*(1-tz)+(h[(z0+1)*w+x0]*(1-tx)+h[(z0+1)*w+x0+1]*tx)*tz
    tile_ranges=[(x['bounds']['minX'],x['bounds']['maxX']) for x in scenery['tiles']];imagery=[]
    for tile in scenery['tiles']:
        image_path=(SCENERY.parent/tile['imagery']['url']).resolve();imagery.append((tile['bounds'],Image.open(image_path).convert('RGB')))
    def roof_colour(x,z):
        for bounds,image in imagery:
            if bounds['minX']<=x<=bounds['maxX'] and bounds['minZ']<=z<=bounds['maxZ']:
                px=round((x-bounds['minX'])/(bounds['maxX']-bounds['minX'])*(image.width-1));py=round((z-bounds['minZ'])/(bounds['maxZ']-bounds['minZ'])*(image.height-1));samples=[image.getpixel((max(0,min(image.width-1,px+dx)),max(0,min(image.height-1,py+dy)))) for dx in range(-2,3) for dy in range(-2,3)];rgb=tuple(int(statistics.median(p[c] for p in samples)) for c in range(3));mean=sum(rgb)/3
                if rgb[1]>rgb[0]*1.22 and rgb[1]>rgb[2]*1.15:return (112,105,96)
                return tuple(max(55,min(210,round(mean+(v-mean)*.72))) for v in rgb)
        return (112,105,96)
    buffers=[[{'points':[],'map':{},'indices':[],'colors':[]} for _ in range(3)] for _ in tile_ranges];counts=[0]*len(tile_ranges);deltas=[];corrections=[];ground_count=0;large=[];degenerate=0;source_assets=[];semantic={k:0 for k in SURFACES}
    for asset in assets(lv95):
        path=download(asset);source_assets.append(asset['ass_asset_id'])
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if not name.lower().endswith('.gml'):continue
                with archive.open(name) as stream:
                    for _,building in ET.iterparse(stream,events=('end',)):
                        if building.tag!=BLDG+'Building':continue
                        bid=building.attrib.get(GML+'id','unknown');classified={kind:[p for surface in building.iter(tag) for p in polygons(surface)] for kind,tag in SURFACES.items()};all_points=[p for group in classified.values() for poly in group for p in poly]
                        if not all_points:building.clear();continue
                        cx=sum(p[0] for p in all_points)/len(all_points);north=sum(p[1] for p in all_points)/len(all_points);lx,lz=cx-oe,on-north
                        if not(local[0]<=lx<=local[1] and local[2]<=lz<=local[3]):building.clear();continue
                        ti=next((i for i,(a,b) in enumerate(tile_ranges) if a<=lx<=b),None)
                        if ti is None:building.clear();continue
                        ground=[p for poly in classified['ground'] for p in poly];ground_count+=bool(ground);base=ground or [min(all_points,key=lambda p:p[2])];samples=[terrain_at(p[0]-oe,on-p[1])-(p[2]-oh) for p in base];delta=-statistics.median(samples);limit=40 if ground else 4;correction=-delta if abs(delta)<=limit else 0;deltas.append(delta);corrections.append(correction)
                        if abs(delta)>3:large.append({'id':bid,'deltaM':round(delta,3),'correctedM':round(correction,3),'groundSurface':bool(ground),'x':round(lx,1),'z':round(lz,1)})
                        counts[ti]+=1;roof_points=[p for poly in classified['roof'] for p in poly];roof_cx=sum(p[0] for p in roof_points)/len(roof_points)-oe if roof_points else lx;roof_cz=on-sum(p[1] for p in roof_points)/len(roof_points) if roof_points else lz;colours={'roof':roof_colour(roof_cx,roof_cz),'wall':WALL_PALETTE[int(hashlib.sha1(bid.encode()).hexdigest()[:8],16)%len(WALL_PALETTE)],'other':(170,172,168)}
                        for si,kind in enumerate(('roof','wall','other')):
                            semantic[kind]+=len(classified[kind]);buf=buffers[ti][si]
                            for poly in classified[kind]:
                                ring=poly[:-1] if poly[0]==poly[-1] else poly
                                if len(ring)<3:degenerate+=1;continue
                                for j in range(1,len(ring)-1):
                                    tri=(ring[0],ring[j],ring[j+1]);area=math.dist(tri[0],tri[1])*math.dist(tri[0],tri[2])
                                    if area<1e-6:degenerate+=1;continue
                                    for p in tri:
                                        value=(round(p[0]-oe,3),round(p[2]-oh+correction,3),round(on-p[1],3),*colours[kind]);idx=buf['map'].get(value)
                                        if idx is None:idx=len(buf['points'])//3;buf['map'][value]=idx;buf['points'].extend(value[:3]);buf['colors'].extend(value[3:])
                                        buf['indices'].append(idx)
                        semantic['ground']+=len(classified['ground']);building.clear()
    runtime=[];total_bytes=0
    for ti,surfaces in enumerate(buffers):
        entry={'buildingCount':counts[ti],'surfaces':{}}
        for kind,buf in zip(('roof','wall','other'),surfaces):
            if not buf['indices']:
                entry['surfaces'][kind]={'positions':'','indices':'','colors':'','vertices':0,'triangles':0,'bytes':0}
                continue
            pos=struct.pack('<%sf'%len(buf['points']),*buf['points']);idx=struct.pack('<%sI'%len(buf['indices']),*buf['indices']);colors=bytes(buf['colors']);digest=hashlib.sha256(pos+idx+colors).hexdigest()[:10];base=f'tile-{ti}-{kind}-{digest}'
            for suffix,data in (('positions.bin',pos),('indices.bin',idx),('colors.bin',colors)):(OUT/f'{base}.{suffix}').write_bytes(data)
            size=len(pos)+len(idx)+len(colors);total_bytes+=size;entry['surfaces'][kind]={'positions':f'./buildings/{base}.positions.bin','indices':f'./buildings/{base}.indices.bin','colors':f'./buildings/{base}.colors.bin','vertices':len(buf['points'])//3,'triangles':len(buf['indices'])//3,'bytes':size}
        runtime.append(entry)
    used={pathlib.Path(v[key]).name for t in runtime for v in t['surfaces'].values() for key in ('positions','indices','colors') if v[key]};[p.unlink() for p in OUT.glob('*.bin') if p.name not in used]
    absolute=[abs(x) for x in deltas];report={'buildings':sum(counts),'withGroundSurface':ground_count,'medianBaseTerrainDeltaM':round(statistics.median(deltas),3),'p95AbsoluteDeltaM':round(percentile(absolute,.95),3),'maximumPositiveDeltaM':round(max(deltas),3),'maximumNegativeDeltaM':round(min(deltas),3),'countOver1M':sum(x>1 for x in absolute),'countOver3M':sum(x>3 for x in absolute),'countOver10M':sum(x>10 for x in absolute),'corrected':sum(abs(x)>.01 for x in corrections),'largestMismatches':sorted(large,key=lambda x:abs(x['deltaM']),reverse=True)[:100],'semanticPolygons':semantic,'degenerateRejected':degenerate}
    REPORT.write_text(json.dumps(report,indent=2)+'\n');scenery['buildings']={'source':'swissBUILDINGS3D 3.0 CityGML','classification':'REAL geometry / DERIVED grounding and colours','format':'semantic indexed meshes with vertex colour','tiles':runtime,'sourceAssets':source_assets,'alignmentReport':str(REPORT)};SCENERY.write_text(json.dumps(scenery,indent=2)+'\n');package['sources']['buildings']={'classification':'REAL','dataset':'swissBUILDINGS3D 3.0'};package['packageBytes']=sum(p.stat().st_size for p in package_dir.rglob('*') if p.is_file());package_path.write_text(json.dumps(package,indent=2)+'\n')
    print(json.dumps({**{k:report[k] for k in ('buildings','withGroundSurface','medianBaseTerrainDeltaM','p95AbsoluteDeltaM','maximumPositiveDeltaM','maximumNegativeDeltaM','countOver1M','countOver3M','countOver10M','corrected','degenerateRejected')},'semanticPolygons':semantic,'bytes':total_bytes,'perTile':counts},indent=2))
if __name__=='__main__':main()
