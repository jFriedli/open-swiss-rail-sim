#!/usr/bin/env python3
"""CI validation for committed national graph/index and known service paths."""
from __future__ import annotations
import gzip,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from resolver import Resolver
ROOT=Path(__file__).resolve().parents[2];errors=[]
graph_manifest=json.loads((ROOT/'data/manifests/national-rail-graph.json').read_text());service_manifest=json.loads((ROOT/'data/manifests/national-service-index.json').read_text())
with gzip.open(ROOT/'data/national/rail-graph.json.gz','rt') as source:graph=json.load(source)
index=json.loads((ROOT/'public/data/national/service-index.json').read_text())
if len(graph['nodes'])!=graph_manifest['nodes'] or len(graph['edges'])!=graph_manifest['edges']:errors.append('national graph manifest mismatch')
if len(index['stations'])!=service_manifest['stations'] or len(index['trips'])!=service_manifest['trips']:errors.append('service index manifest mismatch')
resolver=Resolver();cases=[('Zürich HB','Chur',18*3600,100_000,140_000),('Bern','Thun',14*3600,25_000,40_000),('Basel SBB','Olten',14*3600,30_000,55_000),('Winterthur','Frauenfeld',14*3600,12_000,22_000)]
for origin,destination,when,minimum,maximum in cases:
    found=resolver.search(origin,destination,when,1)
    if not found:errors.append(f'{origin} → {destination}: service search empty');continue
    result=resolver.resolve(found[0][2][0],origin,destination);length=result['path']['lengthM']
    if not minimum<=length<=maximum:errors.append(f'{origin} → {destination}: implausible {length} m')
    if result['supportTier'] not in {'FULL','PARTIAL'}:errors.append(f'{origin} → {destination}: {result["supportTier"]}')
if errors:print('\n'.join('ERROR '+x for x in errors),file=sys.stderr);raise SystemExit(1)
print(f'National validation PASS · {len(graph["nodes"]):,} nodes · {len(index["trips"]):,} trips · {len(cases)} path regressions')
