#!/usr/bin/env python3
"""Deterministically sample Swiss rail trips from the pinned GTFS snapshot.

This is deliberately a metadata analysis, not a claim that scenery or a rail path
was compiled. Fully compiled packages remain the stronger validation gate.
"""
from __future__ import annotations
import csv, json, math, random, subprocess, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
GTFS=ROOT/'data/raw/timetable/gtfs_fp2026_20260822.zip'
OUT=ROOT/'data/manifests/national-route-sample.json'
SAMPLE=30

def rows(name):
    proc=subprocess.Popen(['unzip','-p',str(GTFS),name],stdout=subprocess.PIPE,text=True,encoding='utf-8-sig')
    assert proc.stdout
    yield from csv.DictReader(proc.stdout)
    if proc.wait(): raise RuntimeError(f'could not read {name}')

def main():
    if not GTFS.exists(): raise SystemExit(f'missing pinned GTFS snapshot: {GTFS}')
    with zipfile.ZipFile(GTFS) as archive:
        routes={r['route_id']:r for r in csv.DictReader(archive.read('routes.txt').decode('utf-8-sig').splitlines())}
        stops={r['stop_id']:(float(r['stop_lat']),float(r['stop_lon']),r['stop_name']) for r in csv.DictReader(archive.read('stops.txt').decode('utf-8-sig').splitlines())}
    rng=random.Random(20260822); reservoir=[]; seen=0
    for trip in rows('trips.txt'):
        route=routes.get(trip['route_id'],{})
        if route.get('route_type') not in {'2','100','101','102','103','105','106','109'}: continue
        if not trip.get('trip_short_name'): continue
        seen+=1
        item={'tripId':trip['trip_id'],'serviceId':trip['service_id'],'service':trip['trip_short_name'],'routeId':trip['route_id'],'routeName':route.get('route_long_name') or route.get('route_short_name','')}
        if len(reservoir)<SAMPLE*5: reservoir.append(item)
        else:
            j=rng.randrange(seen)
            if j<len(reservoir): reservoir[j]=item
    wanted={x['tripId']:x for x in reservoir}; calls={key:[] for key in wanted}
    for row in rows('stop_times.txt'):
        if row['trip_id'] in wanted: calls[row['trip_id']].append((int(row['stop_sequence']),row['stop_id']))
    results=[]
    for item in reservoir:
        ordered=[sid for _,sid in sorted(calls[item['tripId']]) if sid in stops]
        if len(ordered)<2: continue
        a,b=stops[ordered[0]],stops[ordered[-1]]
        dy=(b[0]-a[0])*111_320;dx=(b[1]-a[1])*111_320*math.cos(math.radians((a[0]+b[0])/2));straight=math.hypot(dx,dy)
        # Metadata-only support screening. Graph, signals and scenery are intentionally unknown.
        tier='CANDIDATE' if 8_000<=straight<=40_000 else 'OUT_OF_MVP_RANGE'
        results.append(item|{'from':a[2],'to':b[2],'calls':len(ordered),'straightDistanceM':round(straight),'classification':tier,'railPath':'NOT_ANALYSED','reason':'metadata candidate; requires graph dry-run' if tier=='CANDIDATE' else 'outside 8–40 km metadata screening range'})
        if len(results)==SAMPLE: break
    summary={'sampleSize':len(results),'seed':20260822,'railTripsSeen':seen,'candidate':sum(x['classification']=='CANDIDATE' for x in results),'outOfMvpRange':sum(x['classification']!='CANDIDATE' for x in results),'resolvedRailPaths':0,'scope':'GTFS metadata screening only; no national rail graph was available','results':results}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='results'},indent=2))

if __name__=='__main__': main()
