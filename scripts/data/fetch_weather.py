#!/usr/bin/env python3
"""Build a tiny, reproducible MeteoSwiss observation field for a scenario date."""
from __future__ import annotations
import argparse,csv,json,urllib.request
from datetime import datetime
from pathlib import Path

STAC='https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn/items'
DEFAULT_STATIONS=('lac','goe','bus','ber','klo')

def number(row,key,default=0.0):
    try:return float(row.get(key) or default)
    except ValueError:return default

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--date',default='2026-08-22');parser.add_argument('--output',default='public/data/environment/meteo-swiss-2026-08-22.json');parser.add_argument('--force',action='store_true');args=parser.parse_args()
    cache=Path('data/raw/meteoswiss');cache.mkdir(parents=True,exist_ok=True);stations=[]
    for code in DEFAULT_STATIONS:
        meta=json.load(urllib.request.urlopen(f'{STAC}/{code}'));csv_path=cache/f'ogd-smn_{code}_h_recent.csv'
        if args.force or not csv_path.exists():urllib.request.urlretrieve(meta['assets'][f'ogd-smn_{code}_h_recent.csv']['href'],csv_path)
        samples=[]
        with csv_path.open(encoding='utf-8-sig') as handle:
            for row in csv.DictReader(handle,delimiter=';'):
                stamp=datetime.strptime(row['reference_timestamp'],'%d.%m.%Y %H:%M')
                if stamp.strftime('%Y-%m-%d')!=args.date:continue
                humidity=number(row,'ure200h0',60);precip=number(row,'rre150h0');sunshine=number(row,'sre000h0')
                cloud=max(0,min(1,.15+humidity/200+precip*.2-sunshine/120))
                visibility=max(700,min(30000,30000*(1-cloud*.65)/(1+precip*.45)))
                samples.append({'seconds':stamp.hour*3600+stamp.minute*60,'temperatureC':number(row,'tre200h0',10),'relativeHumidity':humidity/100,'precipitationMmH':precip,'windSpeedMps':number(row,'fkl010h0'),'windDirectionDeg':number(row,'dkl010h0'),'cloudCoverDerived':round(cloud,3),'visibilityMDerived':round(visibility)})
        if not samples:raise SystemExit(f'No {args.date} observations for {code}')
        lon,lat=meta['bbox'][:2];stations.append({'id':code.upper(),'name':meta['properties']['title'],'latitude':lat,'longitude':lon,'samples':samples})
    result={'schemaVersion':1,'date':args.date,'source':'MeteoSwiss automatic weather stations (OGD SMN)','sourceCollection':'ch.meteoschweiz.ogd-smn','retrieved':datetime.now().astimezone().isoformat(timespec='seconds'),'license':'Open Data; Source: MeteoSwiss','observedVariables':['temperatureC','relativeHumidity','precipitationMmH','windSpeedMps','windDirectionDeg'],'derivedVariables':['cloudCoverDerived','visibilityMDerived'],'stations':stations}
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(f'{len(stations)} stations / {sum(len(x["samples"]) for x in stations)} hourly samples -> {output} ({output.stat().st_size} bytes)')
if __name__=='__main__':main()
