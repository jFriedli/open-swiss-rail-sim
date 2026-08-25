#!/usr/bin/env python3
"""Build the supported-class Swiss rail graph from an official OSM snapshot extract."""
from __future__ import annotations
import argparse,gzip,hashlib,json,math,time
from collections import Counter
from pathlib import Path
import osmium

ROOT=Path(__file__).resolve().parents[2]
DEFAULT_SOURCE=ROOT/'data/raw/national/switzerland-2026-08-24.osm.pbf'
DEFAULT_OUT=ROOT/'data/national/rail-graph.json.gz'
MANIFEST=ROOT/'data/manifests/national-rail-graph.json'
SUPPORTED_GAUGES={'','1435','1435;1000'}

def distance(a,b):
    y=math.radians((a[0]+b[0])/2)
    return math.hypot((a[0]-b[0])*111320,(a[1]-b[1])*111320*math.cos(y))

class Handler(osmium.SimpleHandler):
    def __init__(self): super().__init__();self.nodes={};self.edges=[];self.ways=0;self.unsupported=Counter();self.switches=set();self.signals=set();self.stations=[];self.platforms=[]
    def way(self,w):
        railway=w.tags.get('railway','');gauge=w.tags.get('gauge','')
        if railway=='platform' or w.tags.get('public_transport')=='platform':
            points=[(n.location.lat,n.location.lon) for n in w.nodes if n.location.valid()]
            if points:self.platforms.append([w.id,round(sum(x[0] for x in points)/len(points),7),round(sum(x[1] for x in points)/len(points),7),w.tags.get('name',''),w.tags.get('ref','')])
            return
        if railway!='rail':
            if railway in {'narrow_gauge','tram','funicular'}:self.unsupported[railway]+=1
            return
        if gauge not in SUPPORTED_GAUGES:
            self.unsupported['gauge:'+gauge]+=1;return
        locations=[]
        for n in w.nodes:
            if not n.location.valid():continue
            point=(round(n.location.lat,7),round(n.location.lon,7));self.nodes[n.ref]=point;locations.append((n.ref,point))
        tags={k:w.tags[k] for k in ('gauge','electrified','usage','service','maxspeed','oneway','bridge','tunnel','layer') if k in w.tags}
        for (a,pa),(b,pb) in zip(locations,locations[1:]):
            length=distance(pa,pb)
            if .05<length<5000:self.edges.append([a,b,round(length,1),w.id,tags])
        self.ways+=1
    def node(self,n):
        kind=n.tags.get('railway','')
        if kind=='switch':self.switches.add(n.id)
        elif kind=='signal':self.signals.add(n.id)
        elif kind in {'station','halt'} and n.location.valid():self.stations.append([n.id,round(n.location.lat,7),round(n.location.lon,7),n.tags.get('name',''),kind])

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,default=DEFAULT_SOURCE);parser.add_argument('--output',type=Path,default=DEFAULT_OUT);args=parser.parse_args()
    if not args.source.exists():raise SystemExit(f'missing OSM PBF: {args.source}')
    started=time.perf_counter();handler=Handler();handler.apply_file(str(args.source),locations=True,idx='sparse_file_array')
    degree=Counter();total=0
    for a,b,length,*_ in handler.edges:degree[a]+=1;degree[b]+=1;total+=length
    # Component labels support cheap rejection before Dijkstra.
    adjacency={}
    for index,(a,b,*_) in enumerate(handler.edges):adjacency.setdefault(a,[]).append((b,index));adjacency.setdefault(b,[]).append((a,index))
    components={};sizes=[]
    for node in handler.nodes:
        if node in components or node not in adjacency:continue
        cid=len(sizes);stack=[node];components[node]=cid;count=0
        while stack:
            current=stack.pop();count+=1
            for nxt,_ in adjacency[current]:
                if nxt not in components:components[nxt]=cid;stack.append(nxt)
        sizes.append(count)
    graph={'schemaVersion':1,'source':{'name':'switzerland-2026-08-24.osm.pbf','derivedInput':args.source.name,'publisher':'Geofabrik extract of OpenStreetMap','date':'2026-08-24','license':'ODbL'},'capability':{'railway':'rail','gauges':sorted(SUPPORTED_GAUGES),'adhesionAssumed':True},'nodes':[[node,*point,components.get(node,-1)] for node,point in handler.nodes.items() if node in adjacency],'edges':handler.edges,'switchNodeIds':sorted(handler.switches & handler.nodes.keys()),'signalNodeIds':sorted(handler.signals & handler.nodes.keys()),'stations':handler.stations,'platforms':handler.platforms}
    encoded=json.dumps(graph,separators=(',',':')).encode();digest=hashlib.sha256(encoded).hexdigest();args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('wb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',compresslevel=9,mtime=0) as out:out.write(encoded)
    stats={'schemaVersion':1,'contentHash':'sha256:'+digest,'source':graph['source'],'compiler':'scripts/national/rail_graph.py v1','nodes':len(graph['nodes']),'edges':len(handler.edges),'totalTrackKm':round(total/1000,1),'connectedComponents':len(sizes),'largestComponentNodes':max(sizes,default=0),'switchNodes':len(graph['switchNodeIds']),'mappedSignals':len(graph['signalNodeIds']),'stations':len(handler.stations),'platforms':len(handler.platforms),'veryShortEdges':sum(edge[2]<1 for edge in handler.edges),'branchNodes':sum(value>2 for value in degree.values()),'unsupportedWays':dict(handler.unsupported),'uncompressedBytes':len(encoded),'compressedBytes':args.output.stat().st_size,'buildSeconds':round(time.perf_counter()-started,2)}
    MANIFEST.parent.mkdir(parents=True,exist_ok=True);MANIFEST.write_text(json.dumps(stats,indent=2)+'\n');print(json.dumps(stats,indent=2))
if __name__=='__main__':main()
