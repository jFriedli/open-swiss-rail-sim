#!/usr/bin/env python3
"""Resolve a deterministic, route-stratified national timetable sample."""
from __future__ import annotations
import json,random,time
from collections import Counter
from pathlib import Path
from resolver import Resolver

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'data/manifests/national-support-analysis.json';SAMPLE=300
def main():
    resolver=Resolver();rng=random.Random(20260822);by_route={}
    for trip in resolver.trips:by_route.setdefault(trip[1],[]).append(trip)
    candidates=[rng.choice(values) for _,values in sorted(by_route.items())];rng.shuffle(candidates);candidates=candidates[:SAMPLE];results=[];started=time.perf_counter()
    for index,trip in enumerate(candidates,1):
        try:
            resolved=resolver.resolve(trip[0]);results.append({'tripId':trip[0],'route':trip[1],'service':trip[2],'from':resolver.stations[trip[4][0]][1],'to':resolver.stations[trip[4][-1]][1],'calls':len(trip[4]),'classification':resolved['supportTier'],'reason':resolved['reason'],'lengthM':resolved['path']['lengthM'],'maxStationOffsetM':resolved['path']['maxStationOffsetM'],'mappedSignals':resolved['path']['mappedSignals'],'speedCoverage':resolved['path']['speedCoverage'],'resolveMs':resolved['resolveMs']})
        except Exception as exc:results.append({'tripId':trip[0],'route':trip[1],'service':trip[2],'from':resolver.stations[trip[4][0]][1],'to':resolver.stations[trip[4][-1]][1],'calls':len(trip[4]),'classification':'UNRESOLVED','reason':str(exc)})
        if index%25==0:print(f'{index}/{len(candidates)}')
    counts=Counter(x['classification'] for x in results);reasons=Counter(x['reason'] for x in results if x['classification'] in {'UNSUPPORTED','UNRESOLVED'});report={'schemaVersion':1,'serviceDate':resolver.index['serviceDate'],'sampleMethod':'one deterministic active trip per GTFS route_id, shuffled with seed 20260822','sampleSize':len(results),'full':counts['FULL'],'partial':counts['PARTIAL'],'unsupported':counts['UNSUPPORTED'],'unresolved':counts['UNRESOLVED'],'topFailureReasons':reasons.most_common(10),'graphLoadMs':round(resolver.load_ms,2),'analysisSeconds':round(time.perf_counter()-started,2),'results':results};OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))
if __name__=='__main__':main()
