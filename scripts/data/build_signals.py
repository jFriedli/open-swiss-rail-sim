#!/usr/bin/env python3
"""Audit mapped signals against the Rapperswil→Uznach route and fill gameplay gaps."""
from __future__ import annotations
import json,math,pathlib

RAW=pathlib.Path('data/raw/railway/signals-full.json');ROUTE=pathlib.Path('public/data/rapperswil-uznach/route.json');NETWORK=pathlib.Path('public/data/rapperswil-uznach/rail-network.json');OUT=pathlib.Path('data/manifests/signal-coverage.json')

def xy(lat,lon,lat0=47.225):return ((lon-8.816)*111320*math.cos(math.radians(lat0)),(lat-lat0)*111320)

def main():
    raw=json.loads(RAW.read_text());route=json.loads(ROUTE.read_text());points=route['points'];nodes={e['id']:e for e in raw['elements'] if e['type']=='node'};signal_nodes={i:n for i,n in nodes.items() if n.get('tags',{}).get('railway')=='signal'};ways=[e for e in raw['elements'] if e['type']=='way'];members={n:[] for n in signal_nodes}
    for way in ways:
        ids=way['nodes']
        for i,n in enumerate(ids):
            if n in members:members[n].append((way,i))
    def match(node):
        p=xy(node['lat'],node['lon']);best=None
        for i,(a,b) in enumerate(zip(points,points[1:])):
            q=xy(a['lat'],a['lon']);r=xy(b['lat'],b['lon']);dx=r[0]-q[0];dy=r[1]-q[1];d2=dx*dx+dy*dy;t=0 if not d2 else max(0,min(1,((p[0]-q[0])*dx+(p[1]-q[1])*dy)/d2));distance=math.hypot(p[0]-(q[0]+t*dx),p[1]-(q[1]+t*dy))
            if best is None or distance<best[0]:best=(distance,a['s']+t*(b['s']-a['s']),(dx,dy))
        return best
    accepted=[];audit=[]
    for node in signal_nodes.values():
        tags=node.get('tags',{});distance,s,tangent=match(node);direction=tags.get('railway:signal:direction','unknown');way_alignment=None;forward=None
        candidates=[]
        for way,i in members.get(node['id'],[]):
            ids=way['nodes'];before=nodes.get(ids[max(0,i-1)]);after=nodes.get(ids[min(len(ids)-1,i+1)])
            if before and after and before['id']!=after['id']:
                a=xy(before['lat'],before['lon']);b=xy(after['lat'],after['lon']);dot=(b[0]-a[0])*tangent[0]+(b[1]-a[1])*tangent[1];candidates.append(dot)
        if candidates:way_alignment=max(candidates,key=abs);same=way_alignment>0;forward=direction=='both' or direction=='forward' and same or direction=='backward' and not same
        reason='accepted' if distance<=12 and forward else 'too far from selected track' if distance>12 else 'ambiguous direction' if forward is None else 'opposes simulation direction'
        item={'sourceId':node['id'],'lat':node['lat'],'lon':node['lon'],'routeS':round(s,2),'distanceFromRouteM':round(distance,2),'mappedDirection':direction,'mappedSide':tags.get('railway:signal:position'),'mappedType':{k:v for k,v in tags.items() if k.startswith('railway:signal:') and k not in ('railway:signal:direction','railway:signal:position')},'wayAlignmentDot':round(way_alignment,2) if way_alignment is not None else None,'accepted':reason=='accepted','reason':reason}
        audit.append(item)
        if item['accepted']:accepted.append({'id':node['id'],'s':round(s,2),'tags':{**tags,'provenance':'OPEN_MAPPING'}})
    accepted.sort(key=lambda x:x['s']);dedup=[]
    for signal in accepted:
        if not dedup or signal['s']-dedup[-1]['s']>.75:dedup.append(signal)
    # Public mapping ends near Rapperswil. Scenario block signals keep the journey legible.
    scenario=[];cursor=dedup[-1]['s'] if dedup else 0;index=1
    while cursor<points[-1]['s']-700:
        cursor=min(cursor+1500,points[-1]['s']-450)
        if all(abs(cursor+x-s['s'])>150 for s in dedup for x in (0,)):scenario.append({'id':f'scenario-{index:02d}','s':round(cursor,2),'tags':{'railway':'signal','railway:signal:direction':'forward','railway:signal:position':'right','provenance':'SIMULATED_SCENARIO','note':'scenario block boundary; not mapped infrastructure'}});index+=1
    signals=sorted(dedup+scenario,key=lambda x:x['s']);network=json.loads(NETWORK.read_text());player_edges=network['playerRouteEdges']
    for signal in signals:
        index=min(len(player_edges)-1,max(0,int(signal['s']/points[-1]['s']*len(player_edges))));signal['networkEdgeId']=player_edges[index];signal['edgeOffsetClassification']='DERIVED_FROM_PLAYER_PATH';signal['protectedSections']=player_edges[index:index+30]
    route['signals']=signals;ROUTE.write_text(json.dumps(route,separators=(',',':')))
    gaps=[b['s']-a['s'] for a,b in zip(signals,signals[1:])];summary={'routeLengthM':points[-1]['s'],'rawMappedSignals':len(signal_nodes),'matchedWithin12M':sum(x['distanceFromRouteM']<=12 for x in audit),'forwardMappedSignals':len(dedup),'reverseOrAmbiguous':sum(x['distanceFromRouteM']<=12 and not x['accepted'] for x in audit),'rejectedSignals':sum(not x['accepted'] for x in audit),'scenarioSignals':len(scenario),'largestGameplaySignalGapM':round(max(gaps),2),'lastMappedForwardSignalS':dedup[-1]['s'] if dedup else None,'mappedGapToRouteEndM':round(points[-1]['s']-(dedup[-1]['s'] if dedup else 0),2)}
    OUT.write_text(json.dumps({'summary':summary,'mappedCandidates':sorted(audit,key=lambda x:x['routeS']),'runtimeSignals':signals},indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
