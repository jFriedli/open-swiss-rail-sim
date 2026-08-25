#!/usr/bin/env python3
"""Build a compact, date-correct browser index from the pinned Swiss GTFS."""
from __future__ import annotations
import argparse,csv,datetime,io,json,time,unicodedata,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];GTFS=ROOT/'data/raw/timetable/gtfs_fp2026_20260822.zip';OUT=ROOT/'public/data/national/service-index.json';MANIFEST=ROOT/'data/manifests/national-service-index.json'
RAIL_TYPES={'2','100','101','102','103','105','106','109'}
def normalize(value):return ''.join(c for c in unicodedata.normalize('NFKD',value.casefold().replace('ü','ue').replace('ö','oe').replace('ä','ae')) if not unicodedata.combining(c))
def seconds(value):
    h,m,s=map(int,value.split(':'));return h*3600+m*60+s
def active_services(z,date):
    compact=date.replace('-','');weekday=datetime.datetime.strptime(date,'%Y-%m-%d').strftime('%A').lower();active=set()
    for row in csv.DictReader(io.TextIOWrapper(z.open('calendar.txt'),encoding='utf-8-sig')):
        if row[weekday]=='1' and row['start_date']<=compact<=row['end_date']:active.add(row['service_id'])
    for row in csv.DictReader(io.TextIOWrapper(z.open('calendar_dates.txt'),encoding='utf-8-sig')):
        if row['date']==compact:(active.add if row['exception_type']=='1' else active.discard)(row['service_id'])
    return active
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--date',default='2026-08-22');args=parser.parse_args();started=time.perf_counter()
    with zipfile.ZipFile(GTFS) as z:
        active=active_services(z,args.date);routes={r['route_id']:r for r in csv.DictReader(io.TextIOWrapper(z.open('routes.txt'),encoding='utf-8-sig')) if r['route_type'] in RAIL_TYPES};stops={r['stop_id']:r for r in csv.DictReader(io.TextIOWrapper(z.open('stops.txt'),encoding='utf-8-sig'))}
        trips={r['trip_id']:r for r in csv.DictReader(io.TextIOWrapper(z.open('trips.txt'),encoding='utf-8-sig')) if r['service_id'] in active and r['route_id'] in routes}
        calls={trip_id:[] for trip_id in trips}
        for row in csv.DictReader(io.TextIOWrapper(z.open('stop_times.txt'),encoding='utf-8-sig')):
            if row['trip_id'] in calls:calls[row['trip_id']].append((int(row['stop_sequence']),row['stop_id'],seconds(row['arrival_time']),seconds(row['departure_time'])))
    used=sorted({stop for sequence in calls.values() for _,stop,_,_ in sequence if stop in stops});station_index={stop:i for i,stop in enumerate(used)};station_rows=[[stop,stops[stop]['stop_name'],round(float(stops[stop]['stop_lat']),6),round(float(stops[stop]['stop_lon']),6),normalize(stops[stop]['stop_name'])] for stop in used]
    trip_rows=[]
    for trip_id,meta in trips.items():
        sequence=[x for x in sorted(calls[trip_id]) if x[1] in station_index]
        if len(sequence)<2:continue
        route=routes[meta['route_id']];trip_rows.append([trip_id,route.get('route_short_name',''),meta.get('trip_short_name',''),meta.get('trip_headsign',''),[station_index[x[1]] for x in sequence],[x[2] for x in sequence],[x[3] for x in sequence]])
    payload={'schemaVersion':1,'serviceDate':args.date,'source':{'dataset':GTFS.name,'publisher':'Geschäftsstelle SKI on behalf of BAV','classification':'REAL STATIC TIMETABLE'},'stations':station_rows,'trips':trip_rows};OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,separators=(',',':'),ensure_ascii=False))
    report={'schemaVersion':1,'serviceDate':args.date,'stations':len(station_rows),'trips':len(trip_rows),'services':len({x[1] for x in trip_rows}),'bytes':OUT.stat().st_size,'buildSeconds':round(time.perf_counter()-started,2)};MANIFEST.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
