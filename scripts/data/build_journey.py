#!/usr/bin/env python3
"""Match mapped platforms and emit the reproducible S17 journey scenario."""
import json,math,pathlib,statistics

ROUTE=pathlib.Path('public/data/rapperswil-uznach/route.json');LANDSCAPE=pathlib.Path('public/data/rapperswil-uznach/landscape.json');OUT=pathlib.Path('public/data/rapperswil-uznach/journey.json')
TIMES={'Rapperswil SG':('14:03:00','14:03:00'),'Blumenau':('14:05:00','14:05:00'),'Schmerikon':('14:11:00','14:11:00'),'Uznach':('14:14:00','14:14:00')}

def main():
    route=json.loads(ROUTE.read_text());landscape=json.loads(LANDSCAPE.read_text());points=route['points'];candidates=[]
    for index,polygon in enumerate(landscape['platforms']):
        samples=[]
        for x,z in polygon:
            nearest=min(points,key=lambda p:(p['x']-x)**2+(p['z']-z)**2);samples.append((nearest['s'],math.hypot(nearest['x']-x,nearest['z']-z)))
        candidates.append({'index':index,'startS':min(x[0] for x in samples),'endS':max(x[0] for x in samples),'medianS':statistics.median(x[0] for x in samples),'distanceM':min(x[1] for x in samples),'medianDistanceM':statistics.median(x[1] for x in samples)})
    definitions=[]
    for station in sorted(route['stations'],key=lambda s:s['s']):
        nearby=[p for p in candidates if p['medianDistanceM']<30 and abs(p['medianS']-station['s'])<500];platform=min(nearby,key=lambda p:p['distanceM']);name=station['tags']['name'];target=station['s'] if station['s']==0 else min(points[-1]['s']-17,platform['endS']-17)
        definitions.append({'id':str(station['id']),'name':name,'s':station['s'],'platformIndex':platform['index'],'platformStartS':round(platform['startS'],1),'platformEndS':round(platform['endS'],1),'targetS':round(target,1),'scheduledArrival':TIMES[name][0],'scheduledDeparture':TIMES[name][1],'dwellSeconds':0 if station['s']==0 else 12,'locationSource':'OpenStreetMap','platformSource':'OpenStreetMap','targetClassification':'DERIVED'})
    payload={'service':{'route':'S17','tripId':'.ojp-91-17-M.1.TA.200.j26','originalTripId':'','tripShortName':'12353','headsign':'Uznach','serviceDate':'2026-08-22','feed':'GTFS_FP2026_20260822.zip','publisher':'Geschäftsstelle SKI on behalf of BAV','classification':'REAL STATIC TIMETABLE'},'direction':'Rapperswil → Uznach','scenarioStart':'14:03:00','stops':definitions,'platformsMatched':len(definitions),'generatedFrom':'official GTFS stop sequence plus OSM station/platform geometry'}
    OUT.write_text(json.dumps(payload,indent=2)+'\n');print(json.dumps(payload,indent=2))
if __name__=='__main__':main()
