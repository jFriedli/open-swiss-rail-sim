#!/usr/bin/env python3
"""Create an Overpass-compatible corridor extract from the pinned national PBF."""
from __future__ import annotations
import json,subprocess,tempfile
from pathlib import Path
import osmium

ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT/'data/raw/national/switzerland-2026-08-24.osm.pbf'
class Handler(osmium.SimpleHandler):
    def __init__(self):super().__init__();self.elements=[]
    def node(self,n):
        railway=n.tags.get('railway','')
        if railway in {'switch','signal','station','halt'} and n.location.valid():self.elements.append({'type':'node','id':n.id,'lat':n.location.lat,'lon':n.location.lon,'tags':dict(n.tags)})
    def way(self,w):
        railway=w.tags.get('railway','');public=w.tags.get('public_transport','')
        if railway not in {'rail','platform'} and public!='platform':return
        geometry=[];nodes=[]
        for n in w.nodes:
            if n.location.valid():nodes.append(n.ref);geometry.append({'lat':n.location.lat,'lon':n.location.lon})
        if len(nodes)>1:self.elements.append({'type':'way','id':w.id,'nodes':nodes,'geometry':geometry,'tags':dict(w.tags)})
def extract(bounds,output):
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        subset=Path(temporary)/'corridor.osm.pbf';bbox=','.join(str(x) for x in bounds)
        subprocess.run(['osmium','extract','-b',bbox,'--strategy','complete_ways',str(SOURCE),'-o',str(subset)],check=True)
        handler=Handler();handler.apply_file(str(subset),locations=True);output.write_text(json.dumps({'version':.6,'generator':'Open Swiss Rail Sim national corridor extractor','osm3s':{'timestamp_osm_base':'2026-08-24'},'elements':handler.elements},separators=(',',':')))
    return output
