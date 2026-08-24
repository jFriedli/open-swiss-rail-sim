#!/usr/bin/env python3
"""Extract the corridor operating window from official GTFS and path AI services.

The large source feed is cached below data/raw and never committed. The compact
scenario contains only corridor calls and derived paths through rail-network.json.
"""
import csv,heapq,io,json,pathlib,zipfile

GTFS=pathlib.Path('data/raw/timetable/gtfs_fp2026_20260822.zip');NETWORK=pathlib.Path('public/data/rapperswil-uznach/rail-network.json');JOURNEY=pathlib.Path('public/data/rapperswil-uznach/journey.json');OUT=pathlib.Path('public/data/rapperswil-uznach/traffic.json');SERVICE_DATE='20260822';SERVICE_WEEKDAY='saturday'
STATIONS={'Rapperswil SG','Blumenau','Schmerikon','Uznach'};WINDOW=(13*3600+55*60,14*3600+25*60)
def sec(t):
    h,m,s=map(int,t.split(':'));return h*3600+m*60+s
def main():
    z=zipfile.ZipFile(GTFS);stops={}
    for row in csv.DictReader(io.TextIOWrapper(z.open('stops.txt'),encoding='utf-8-sig')):
        if row['stop_name'] in STATIONS:stops[row['stop_id']]={'name':row['stop_name'],'platform':row.get('platform_code',''),'lat':float(row['stop_lat']),'lon':float(row['stop_lon'])}
    calls={}
    for row in csv.DictReader(io.TextIOWrapper(z.open('stop_times.txt'),encoding='utf-8-sig')):
        if row['stop_id'] not in stops:continue
        t=sec(row['departure_time'] or row['arrival_time'])
        if WINDOW[0]-900<=t<=WINDOW[1]+900:calls.setdefault(row['trip_id'],[]).append({**stops[row['stop_id']],'arrival':row['arrival_time'],'departure':row['departure_time'],'sequence':int(row['stop_sequence'])})
    candidates={k:sorted(v,key=lambda x:x['sequence']) for k,v in calls.items() if len({x['name'] for x in v})>=2 and any(WINDOW[0]<=sec(x['departure'] or x['arrival'])<=WINDOW[1] for x in v)}
    trips={}
    for row in csv.DictReader(io.TextIOWrapper(z.open('trips.txt'),encoding='utf-8-sig')):
        if row['trip_id'] in candidates:trips[row['trip_id']]={'routeId':row['route_id'],'serviceId':row['service_id'],'headsign':row['trip_headsign'],'shortName':row['trip_short_name']}
    active=set()
    for row in csv.DictReader(io.TextIOWrapper(z.open('calendar.txt'),encoding='utf-8-sig')):
        if row['start_date']<=SERVICE_DATE<=row['end_date'] and row[SERVICE_WEEKDAY]=='1':active.add(row['service_id'])
    for row in csv.DictReader(io.TextIOWrapper(z.open('calendar_dates.txt'),encoding='utf-8-sig')):
        if row['date']!=SERVICE_DATE:continue
        if row['exception_type']=='1':active.add(row['service_id'])
        elif row['exception_type']=='2':active.discard(row['service_id'])
    network=json.loads(NETWORK.read_text());journey=json.loads(JOURNEY.read_text());edges={e['id']:e for e in network['edges']};adj={n['id']:[] for n in network['nodes']}
    for e in edges.values():adj[e['from']].append((e['to'],e['lengthM'],e['id'],False));adj[e['to']].append((e['from'],e['lengthM'],e['id'],True))
    station_s={x['name']:x['s'] for x in journey['stops']};route_points=json.loads(pathlib.Path('public/data/rapperswil-uznach/route.json').read_text())['points']
    def edge_station(name,opposite):
        p=min(route_points,key=lambda p:abs(p['s']-station_s[name]));rank=[]
        for e in edges.values():rank.append((min((q[0]-p['x'])**2+(q[2]-p['z'])**2 for q in e['points']),e['id']))
        rank.sort();return rank[min(opposite,len(rank)-1)][1]
    player_edges=set(network['playerRouteEdges'])
    def path(start_edge,end_edge,avoid_player):
        starts=[edges[start_edge]['from'],edges[start_edge]['to']];targets={edges[end_edge]['from'],edges[end_edge]['to']};queue=[(0,n,[]) for n in starts];heapq.heapify(queue);best={n:0 for n in starts}
        while queue:
            cost,node,path_edges=heapq.heappop(queue)
            if cost!=best[node]:continue
            if node in targets:return path_edges
            for other,length,eid,reverse in adj[node]:
                nc=cost+length*(25 if avoid_player and eid in player_edges else 1)
                if nc<best.get(other,1e30):best[other]=nc;heapq.heappush(queue,(nc,other,path_edges+[{'edgeId':eid,'reverse':reverse}]))
        raise RuntimeError('no AI path')
    # Keep the nearest services in the window; prefer opposing complete-corridor runs.
    selected=[]
    for trip_id,stops_seq in candidates.items():
        if trips.get(trip_id,{}).get('serviceId') not in active:continue
        names=[x['name'] for x in stops_seq]
        if 'Rapperswil SG' not in names or 'Uznach' not in names:continue
        forward=names.index('Rapperswil SG')<names.index('Uznach');start=names[0];end=names[-1];derived=path(edge_station(start,1 if not forward else 0),edge_station(end,1 if not forward else 0),not forward);meta=trips.get(trip_id,{})
        selected.append({'id':'ai_'+str(len(selected)+1),'tripId':trip_id,'publicName':meta.get('shortName') or meta.get('headsign') or 'S17','headsign':meta.get('headsign',''),'direction':'Rapperswil → Uznach' if forward else 'Uznach → Rapperswil','stops':stops_seq,'path':derived,'timetableClassification':'REAL STATIC TIMETABLE','pathClassification':'DERIVED FROM OSM GRAPH','motionClassification':'SIMULATED'})
    # GTFS contains calendar/service variants of the same public movement. Collapse
    # identical public runs rather than rendering duplicate trains on top of one another.
    unique={}
    for train in selected:
        key=(train['publicName'],train['direction'],tuple((s['name'],s['arrival'],s['departure']) for s in train['stops']))
        unique.setdefault(key,train)
    selected=list(unique.values());centre=14*3600+8*60
    selected.sort(key=lambda x:min(abs(sec(s['departure'] or s['arrival'])-centre) for s in x['stops']))
    opposing=[x for x in selected if x['direction']=='Uznach → Rapperswil' and sec(x['stops'][-1]['arrival'])>=14*3600+3*60];forward=[x for x in selected if x['direction']=='Rapperswil → Uznach' and x['tripId']!=journey['service']['tripId']]
    selected=(opposing[:3]+forward[:2])[:5]
    player_active=trips.get(journey['service']['tripId'],{}).get('serviceId') in active
    payload={'version':1,'id':'s17-1403-living-railway','name':'S17 14:03 operating window','serviceDate':'2026-08-22','feed':'GTFS_FP2026_20260822.zip','publisher':'Geschäftsstelle SKI on behalf of BAV','window':{'start':'13:55:00','end':'14:25:00'},'playerTripId':journey['service']['tripId'],'services':selected,'stats':{'candidateTrips':len(candidates),'selectedAiServices':len(selected),'playerTripActiveOnDate':player_active}}
    OUT.write_text(json.dumps(payload,separators=(',',':')));pathlib.Path('data/manifests/traffic.json').write_text(json.dumps({'stats':payload['stats'],'services':[{'tripId':x['tripId'],'name':x['publicName'],'direction':x['direction'],'stops':[(s['name'],s['arrival'],s['departure']) for s in x['stops']]} for x in selected]},indent=2)+'\n');print(json.dumps(pathlib.Path('data/manifests/traffic.json').read_text()))
if __name__=='__main__':main()
