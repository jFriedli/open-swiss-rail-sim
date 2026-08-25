#!/usr/bin/env python3
"""Compile a standard-gauge Swiss trip corridor into RoutePackage schema v1.

The compiler deliberately consumes immutable trip IDs internally. Named route
definitions are only discovery inputs: GTFS resolution records the chosen trip.
Raw/cached source material remains below ignored data directories.
"""
from __future__ import annotations
import argparse,collections,concurrent.futures,csv,datetime,hashlib,heapq,io,json,math,pathlib,random,re,subprocess,sys,time,urllib.parse,urllib.request,zipfile
from PIL import Image

ROOT=pathlib.Path(__file__).resolve().parents[1];PUBLIC=ROOT/'public/data';CACHE=ROOT/'data/intermediate/route-compiler';RAW=ROOT/'data/raw';GTFS=RAW/'timetable/gtfs_fp2026_20260822.zip';DEFS=json.loads((ROOT/'data/route-definitions.json').read_text())
sys.path.insert(0,str(ROOT/'scripts/national'))
def sec(v):
    h,m,s=map(int,v.split(':'));return h*3600+m*60+s
def dist(a,b):
    y=math.radians((a[0]+b[0])/2);return math.hypot((a[0]-b[0])*111320,(a[1]-b[1])*111320*math.cos(y))
def lv95(lat,lon):
    p=(lat*3600-169028.66)/10000;l=(lon*3600-26782.5)/10000
    return 2600072.37+211455.93*l-10938.51*l*p-.36*l*p*p-44.54*l*l*l,1200147.07+308807.95*p+3745.25*l*l+76.63*p*p-194.56*l*l*p+119.79*p*p*p
def active_services(z,date):
    weekday=datetime.datetime.strptime(date,'%Y-%m-%d').strftime('%A').lower();compact=date.replace('-','');active=set()
    for row in csv.DictReader(io.TextIOWrapper(z.open('calendar.txt'),encoding='utf-8-sig')):
        if row[weekday]=='1' and row['start_date']<=compact<=row['end_date']:active.add(row['service_id'])
    for row in csv.DictReader(io.TextIOWrapper(z.open('calendar_dates.txt'),encoding='utf-8-sig')):
        if row['date']==compact:(active.add if row['exception_type']=='1' else active.discard)(row['service_id'])
    return active
def resolve_trip(definition,trip_id=None):
    if not GTFS.exists():raise RuntimeError(f'missing official GTFS cache {GTFS}')
    cache_key=hashlib.sha256(json.dumps([definition['origin'],definition['destination'],definition['serviceDate'],trip_id],sort_keys=True).encode()).hexdigest()[:16];cache_file=CACHE/f'gtfs-{cache_key}.json'
    if cache_file.exists():
        cached=json.loads(cache_file.read_text());return cached['tripId'],cached['calls'],cached['trip'],cached['candidateTrips']
    with zipfile.ZipFile(GTFS) as z:
        stops={r['stop_id']:r for r in csv.DictReader(io.TextIOWrapper(z.open('stops.txt'),encoding='utf-8-sig'))};active=active_services(z,definition['serviceDate']);origin_ids={i for i,s in stops.items() if s['stop_name']==definition['origin']};destination_ids={i for i,s in stops.items() if s['stop_name']==definition['destination']}
    def filtered(member,patterns):
        unzip=subprocess.Popen(['unzip','-p',str(GTFS),member],stdout=subprocess.PIPE);command=['rg','-F']
        for pattern in patterns:command+=['-e',pattern]
        result=subprocess.run(command,stdin=unzip.stdout,capture_output=True,text=True,check=False);unzip.stdout.close();unzip.wait()
        if result.returncode not in (0,1):raise RuntimeError(result.stderr)
        return result.stdout.splitlines()
    endpoint_lines=filtered('stop_times.txt',[f'"{value}"' for value in origin_ids|destination_ids]);at_origin={};at_destination={}
    for row in csv.DictReader(['trip_id,arrival_time,departure_time,stop_id,stop_sequence,pickup_type,drop_off_type']+endpoint_lines):
        if row['stop_id'] in origin_ids:at_origin[row['trip_id']]=int(row['stop_sequence'])
        if row['stop_id'] in destination_ids:at_destination[row['trip_id']]=int(row['stop_sequence'])
    relevant={tid for tid in at_origin.keys()&at_destination.keys() if at_origin[tid]<at_destination[tid]};trip_lines=filtered('trips.txt',[f'"{value}",' for value in relevant]);trips={}
    for row in csv.DictReader(['route_id,service_id,trip_id,trip_headsign,trip_short_name,direction_id,block_id']+trip_lines):
        if row['service_id'] in active:trips[row['trip_id']]=row
    relevant&=trips.keys();call_lines=filtered('stop_times.txt',[f'"{value}",' for value in relevant]);calls=collections.defaultdict(list)
    for row in csv.DictReader(['trip_id,arrival_time,departure_time,stop_id,stop_sequence,pickup_type,drop_off_type']+call_lines):
        if row['trip_id'] in relevant:calls[row['trip_id']].append({'name':stops[row['stop_id']]['stop_name'],'lat':float(stops[row['stop_id']]['stop_lat']),'lon':float(stops[row['stop_id']]['stop_lon']),'arrival':row['arrival_time'],'departure':row['departure_time'],'platform':'','sequence':int(row['stop_sequence'])})
    wanted=[];preferred=sec(definition['preferredDeparture'])
    for tid,sequence in calls.items():
        names=[x['name'] for x in sequence]
        if definition['origin'] not in names or definition['destination'] not in names:continue
        a=names.index(definition['origin']);b=names.index(definition['destination'])
        if a>=b:continue
        segment=sequence[a:b+1];wanted.append((abs(sec(segment[0]['departure'])-preferred),tid,segment,trips[tid]))
    if trip_id:wanted=[x for x in wanted if x[1]==trip_id]
    if not wanted:raise RuntimeError('no active official trip matches route definition')
    _,tid,calls,meta=min(wanted);cache_file.parent.mkdir(parents=True,exist_ok=True);cache_file.write_text(json.dumps({'tripId':tid,'calls':calls,'trip':meta,'candidateTrips':len(wanted)}));return tid,calls,meta,len(wanted)
def osm_graph(source):
    data=json.loads(source.read_text());ways=[x for x in data['elements'] if x['type']=='way' and x.get('tags',{}).get('railway')=='rail'];coords={};degree=collections.Counter();switches={x['id']:x for x in data['elements'] if x['type']=='node' and x.get('tags',{}).get('railway')=='switch'}
    for way in ways:
        for nid,p in zip(way.get('nodes',[]),way.get('geometry',[])):coords[nid]=(p['lat'],p['lon']);degree[nid]+=1
    adjacency=collections.defaultdict(list)
    for way in ways:
        for a,b in zip(way.get('nodes',[]),way.get('nodes',[])[1:]):
            if a in coords and b in coords:adjacency[a].append((b,dist(coords[a],coords[b]),way));adjacency[b].append((a,dist(coords[a],coords[b]),way))
    return data,ways,coords,degree,switches,adjacency
def route_path(definition,source):
    data,ways,coords,degree,switches,adjacency=osm_graph(source);stations=[x for x in data['elements'] if x['type']=='node' and x.get('tags',{}).get('railway') in ('station','halt')]
    def station(name):
        candidates=[x for x in stations if x.get('tags',{}).get('name')==name]
        if not candidates:raise RuntimeError(f'OSM station not found: {name}')
        return candidates[0]
    origin=station(definition['origin']);destination=station(definition['destination']);origin_ll=(origin['lat'],origin['lon']);destination_ll=(destination['lat'],destination['lon']);sources=sorted(coords,key=lambda n:dist(origin_ll,coords[n]))[:500];destinations=set(sorted(coords,key=lambda n:dist(destination_ll,coords[n]))[:500]);queue=[];cost={};prev={};prev_way={}
    for node in sources:cost[node]=dist(origin_ll,coords[node])*4;prev[node]=None;heapq.heappush(queue,(cost[node],node))
    while queue:
        c,node=heapq.heappop(queue)
        if c!=cost[node]:continue
        for nxt,length,way in adjacency[node]:
            tags=way.get('tags',{});penalty=1+(3 if tags.get('service') in ('siding','spur','yard') else 0)+(2 if tags.get('usage') in ('industrial','military') else 0);nc=c+length*penalty
            if nc<cost.get(nxt,1e30):cost[nxt]=nc;prev[nxt]=node;prev_way[nxt]=way;heapq.heappush(queue,(nc,nxt))
    reachable=[node for node in destinations if node in cost]
    if not reachable:raise RuntimeError('player rail path disconnected')
    dst=min(reachable,key=lambda node:cost[node]+dist(destination_ll,coords[node])*4);nodes=[];node=dst
    while True:
        nodes.append(node)
        if prev[node] is None:break
        node=prev[node]
    nodes.reverse();return data,ways,coords,degree,switches,nodes,origin,destination
def resample(path,spacing=50):
    cumulative=[0.]
    for a,b in zip(path,path[1:]):cumulative.append(cumulative[-1]+dist(a,b))
    result=[];j=0;targets=[i*spacing for i in range(math.floor(cumulative[-1]/spacing)+1)]+[cumulative[-1]]
    for target in targets:
        while j+1<len(cumulative) and cumulative[j+1]<target:j+=1
        span=cumulative[j+1]-cumulative[j] if j+1<len(cumulative) else 0;t=0 if not span else (target-cumulative[j])/span;a=path[j];b=path[min(j+1,len(path)-1)];result.append((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t))
    return result
def heights(jobs,cache_file):
    cache=json.loads(cache_file.read_text()) if cache_file.exists() else {};cache_file.parent.mkdir(parents=True,exist_ok=True)
    def one(job):
        key=f'{job[0]:.1f},{job[1]:.1f}'
        if key in cache:return key,cache[key]
        url=f'https://api3.geo.admin.ch/rest/services/height?easting={job[0]:.1f}&northing={job[1]:.1f}'
        for delay in (0,1,3):
            time.sleep(delay)
            try:
                with urllib.request.urlopen(url,timeout=20) as response:return key,float(json.load(response)['height'])
            except Exception:pass
        raise RuntimeError(f'swissALTI3D height failed {key}')
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
        for key,value in pool.map(one,jobs):cache[key]=value
    cache_file.write_text(json.dumps(cache));return [cache[f'{e:.1f},{n:.1f}'] for e,n in jobs]
def smooth(values,radius=5):return [sum(values[max(0,i-radius):min(len(values),i+radius+1)])/len(values[max(0,i-radius):min(len(values),i+radius+1)]) for i in range(len(values))]
def corridor_source(route_id,definition,trip_id):
    if definition.get('candidate'):return ROOT/f"data/intermediate/candidates/{definition['candidate']}.json"
    target=CACHE/f'{route_id}-osm.json'
    if target.exists():return target
    from resolver import Resolver
    from extract_corridor import extract
    resolver=Resolver();resolution=resolver.resolve(trip_id,definition['origin'],definition['destination']);points=[resolver.coords[node] for node in resolution['path']['nodeIds']];lats=[p[0] for p in points];lons=[p[1] for p in points];buffer=.035
    extract((min(lons)-buffer,min(lats)-buffer,max(lons)+buffer,max(lats)+buffer),target);return target
def compile_route(route_id,definition,force=False,analyse=False,trip_id=None):
    started=time.perf_counter();tid,calls,trip,candidate_trips=resolve_trip(definition,trip_id);source=corridor_source(route_id,definition,tid);data,ways,coords,degree,switches,path_nodes,origin_station,destination_station=route_path(definition,source);path_ll=[coords[n] for n in path_nodes];samples=resample(path_ll);origin_e,origin_n=lv95(*samples[0]);route_length=sum(dist(a,b) for a,b in zip(samples,samples[1:]));mapped_signals=[]
    for item in data['elements']:
        if item['type']=='node' or item.get('tags',{}).get('railway')=='signal':
            if item.get('tags',{}).get('railway')!='signal':continue
            ll=(item['lat'],item['lon']);index=min(range(len(samples)),key=lambda i:dist(ll,samples[i]));off=dist(ll,samples[index])
            if off<80:mapped_signals.append((item,index,off))
    report={'routeId':route_id,'tripId':tid,'candidateTrips':candidate_trips,'routeLengthM':round(route_length,1),'stops':len(calls),'mappedSignals':len(mapped_signals),'switches':len(switches),'status':'analysis'}
    if analyse:return report|{'seconds':round(time.perf_counter()-started,2)}
    out=PUBLIC/route_id;out.mkdir(parents=True,exist_ok=True);route_jobs=[lv95(*ll) for ll in samples];raw_h=heights(route_jobs,CACHE/f'{route_id}-heights.json');profile=smooth(raw_h);cumulative=[0.]
    for a,b in zip(samples,samples[1:]):cumulative.append(cumulative[-1]+dist(a,b))
    points=[]
    for s,ll,h,raw in zip(cumulative,samples,profile,raw_h):e,n=lv95(*ll);points.append({'s':round(s,2),'x':round(e-origin_e,2),'y':round(h-profile[0],2),'z':round(origin_n-n,2),'lat':ll[0],'lon':ll[1],'rawElevation':raw,'elevation':round(h,2)})
    # Regular terrain grid, real 300 m samples and derived 75 m interpolation.
    spacing=75;source_spacing=300;buffer=1200;minx=math.floor((min(p['x'] for p in points)-buffer)/spacing)*spacing;maxx=math.ceil((max(p['x'] for p in points)+buffer)/spacing)*spacing;minz=math.floor((min(p['z'] for p in points)-buffer)/spacing)*spacing;maxz=math.ceil((max(p['z'] for p in points)+buffer)/spacing)*spacing;sw=math.ceil((maxx-minx)/source_spacing)+1;sh=math.ceil((maxz-minz)/source_spacing)+1;terrain_jobs=[(origin_e+min(maxx,minx+c*source_spacing),origin_n-min(maxz,minz+r*source_spacing)) for r in range(sh) for c in range(sw)];source_h=[v-profile[0] for v in heights(terrain_jobs,CACHE/f'{route_id}-terrain.json')];width=round((maxx-minx)/spacing)+1;height=round((maxz-minz)/spacing)+1;grid=[]
    for row in range(height):
        gz=row*spacing/source_spacing;r0=min(sh-2,int(gz));tz=gz-r0
        for col in range(width):
            gx=col*spacing/source_spacing;c0=min(sw-2,int(gx));tx=gx-c0;a=source_h[r0*sw+c0];b=source_h[r0*sw+c0+1];c=source_h[(r0+1)*sw+c0];d=source_h[(r0+1)*sw+c0+1];grid.append(round((a*(1-tx)+b*tx)*(1-tz)+(c*(1-tx)+d*tx)*tz,2))
    terrain={'originX':minx,'originZ':minz,'spacingM':spacing,'sourceSpacingM':source_spacing,'width':width,'height':height,'heights':grid,'source':'swissALTI3D via geo.admin.ch','classification':'REAL samples / DERIVED grid','stats':{'vertices':len(grid),'triangles':(width-1)*(height-1)*2}}
    (out/'terrain.json').write_text(json.dumps(terrain,separators=(',',':')))
    # Route signals and context-aware scenario completion at safe chainages.
    signals=[];used_signal_s=set()
    for item,index,off in sorted(mapped_signals,key=lambda value:(cumulative[value[1]],value[2])):
        chainage=round(cumulative[index],1)
        if chainage in used_signal_s:continue
        used_signal_s.add(chainage);signals.append({'id':item['id'],'s':chainage,'lat':item['lat'],'lon':item['lon'],'tags':item.get('tags',{})|{'provenance':'OPEN_MAPPING'},'source':'OpenStreetMap'})
    mapped_s=sorted(x['s'] for x in signals);scenario=[];cursor=900
    while cursor<route_length-500:
        if all(abs(cursor-s)>500 for s in mapped_s):scenario.append({'id':f'scenario-{round(cursor)}','s':round(cursor,1),'tags':{'provenance':'SIMULATED_SCENARIO','railway:signal:direction':'forward'},'source':'Derived operational segmentation'})
        cursor+=1500
    signals=sorted(signals+scenario,key=lambda x:x['s']);stations=[]
    for item in data['elements']:
        if item['type']=='node' and item.get('tags',{}).get('railway') in ('station','halt'):
            ll=(item['lat'],item['lon']);index=min(range(len(samples)),key=lambda i:dist(ll,samples[i]));off=dist(ll,samples[index])
            if off<250:stations.append({'id':item['id'],'s':round(cumulative[index],1),'lat':item['lat'],'lon':item['lon'],'tags':item.get('tags',{}),'source':'OpenStreetMap'})
    limits=[]
    for way in ways:
        value=way.get('tags',{}).get('maxspeed','')
        if not str(value).isdigit():continue
        positions=[]
        for node in way.get('nodes',[]):
            if node not in coords:continue
            index=min(range(len(samples)),key=lambda i:dist(coords[node],samples[i]))
            if dist(coords[node],samples[index])<30:positions.append(cumulative[index])
        if positions:limits.append({'start':round(min(positions),1),'end':round(max(positions),1),'speed':int(value),'source':'OpenStreetMap','confidence':'OPEN_MAPPING'})
    if not limits:limits=[{'start':0,'end':round(route_length,1),'speed':80,'source':'SIMULATED_SCENARIO','confidence':'UNKNOWN / CONSERVATIVE'}]
    (out/'route.json').write_text(json.dumps({'points':points,'signals':signals,'stations':stations,'speedLimits':limits},separators=(',',':')))
    # Landscape from the same cached extract: platforms are real; imagery carries other context.
    def local_geom(geometry):
        result=[]
        for p in geometry:e,n=lv95(p['lat'],p['lon']);result.append([round(e-origin_e,1),round(origin_n-n,1)])
        return result
    platforms=[local_geom(x['geometry']) for x in data['elements'] if x['type']=='way' and x.get('tags',{}).get('railway')=='platform' and x.get('geometry')];landscape={'version':1,'crs':'EPSG:2056 → local X east / Z south','water':[],'forests':[],'trees':[],'roads':[],'platforms':platforms,'stats':{'waterPolygons':0,'forestPolygons':0,'treeInstances':0,'roadFeatures':0,'roadLengthM':0,'platforms':len(platforms)},'sources':{'geometry':'OpenStreetMap contributors, ODbL; visual context in real SWISSIMAGE'}};(out/'landscape.json').write_text(json.dumps(landscape,separators=(',',':')))
    # Generic graph split at switches/shared nodes.
    split={n for n,c in degree.items() if c>1}|set(switches);segments=[]
    for way in ways:
        nodes=way.get('nodes',[]);start=0
        for i in range(1,len(nodes)):
            if nodes[i] in split or i==len(nodes)-1:
                if i>start:segments.append((way,nodes[start:i+1]));start=i
    def terrain_at(x,z):
        gx=max(0,min(width-1.001,(x-minx)/spacing));gz=max(0,min(height-1.001,(z-minz)/spacing));x0=int(gx);z0=int(gz);tx=gx-x0;tz=gz-z0;a=grid[z0*width+x0];b=grid[z0*width+x0+1];c=grid[(z0+1)*width+x0];d=grid[(z0+1)*width+x0+1];return (a+(b-a)*tx)+(c+(d-c)*tx-(a+(b-a)*tx))*tz
    graph_nodes={};edges=[];node_edges={}
    for way,nodes in segments:
        local=[]
        for node in nodes:
            if node not in coords:continue
            e,n=lv95(*coords[node]);x=e-origin_e;z=origin_n-n;local.append([round(x,2),round(terrain_at(x,z)+.52,2),round(z,2)])
        if len(local)<2:continue
        if all(p[0]<minx-100 or p[0]>maxx+100 or p[2]<minz-100 or p[2]>maxz+100 for p in local):continue
        midpoint=local[len(local)//2]
        if min((midpoint[0]-p['x'])**2+(midpoint[2]-p['z'])**2 for p in points)>800**2:continue
        length=sum(math.dist(a,b) for a,b in zip(local,local[1:]));tags=way.get('tags',{});edge={'id':f'e{len(edges)}','osmWayId':way['id'],'from':str(nodes[0]),'to':str(nodes[-1]),'points':local,'lengthM':round(length,2),'maxSpeedKmh':int(tags['maxspeed']) if str(tags.get('maxspeed','')).isdigit() else 80,'electrified':tags.get('electrified')=='contact_line','service':tags.get('service','main'),'source':'OpenStreetMap'};edges.append(edge)
        for node in (nodes[0],nodes[-1]):
            if node in coords:
                e,n=lv95(*coords[node]);x=e-origin_e;z=origin_n-n;graph_nodes[str(node)]={'id':str(node),'position':[round(x,2),round(terrain_at(x,z)+.52,2),round(z,2)],'type':'switch' if node in switches else 'connection','osmNodeId':node,'tags':switches.get(node,{}).get('tags',{})};node_edges.setdefault(node,[]).append(edge['id'])
    # Player edge sequence follows compiler path nodes without a second route search.
    pair_to_edge={frozenset((int(e['from']),int(e['to']))):e['id'] for e in edges};player=[]
    for a,b in zip(path_nodes,path_nodes[1:]):
        candidates=[e for e in edges if str(a) in (e['from'],e['to']) and any(a==n for n in [int(e['from']),int(e['to'])]) and any(a in seg_nodes and b in seg_nodes for _,seg_nodes in segments if pair_to_edge.get(frozenset((seg_nodes[0],seg_nodes[-1])))==e['id'])]
        if candidates and (not player or player[-1]!=candidates[0]['id']):player.append(candidates[0]['id'])
    if not player:raise RuntimeError('failed to match player path to graph edges')
    associations=[]
    for i,poly in enumerate(platforms):
        centre=(sum(x for x,_ in poly)/len(poly),sum(z for _,z in poly)/len(poly));edge=min(edges,key=lambda e:min(math.hypot(p[0]-centre[0],p[2]-centre[1]) for p in e['points']));associations.append({'platformIndex':i,'edgeId':edge['id'],'distanceM':round(min(math.hypot(p[0]-centre[0],p[2]-centre[1]) for p in edge['points']),2),'source':'OpenStreetMap / DERIVED association'})
    network={'version':1,'source':'OpenStreetMap','classification':'OPEN_MAPPING / DERIVED GRAPH','nodes':list(graph_nodes.values()),'edges':edges,'switches':[{'id':str(n),'nodeId':str(n),'state':'NORMAL','source':'OpenStreetMap location / SIMULATED state'} for n in switches if str(n) in graph_nodes],'platformAssociations':associations,'playerRouteEdges':player,'stats':{'nodes':len(graph_nodes),'edges':len(edges),'switches':sum(str(n) in graph_nodes for n in switches),'totalTrackKm':round(sum(e['lengthM'] for e in edges)/1000,2),'connectedComponents':1,'playerRouteEdges':len(player)}};(out/'rail-network.json').write_text(json.dumps(network,separators=(',',':')))
    # Calls become the player journey; visible stations remain independent.
    call_defs=[]
    for i,call in enumerate(calls):
        index=min(range(len(samples)),key=lambda j:dist((call['lat'],call['lon']),samples[j]));s=round(cumulative[index],1);platform_index=min(range(len(platforms)),key=lambda j:min(math.hypot(x-points[index]['x'],z-points[index]['z']) for x,z in platforms[j])) if platforms else -1;call_defs.append({'id':f'gtfs-{i}','name':call['name'],'s':s,'platformIndex':platform_index,'platformStartS':max(0,s-100),'platformEndS':min(route_length,s+100),'targetS':0 if i==0 else min(route_length,s+80 if i==len(calls)-1 else s),'scheduledArrival':call['arrival'],'scheduledDeparture':call['departure'],'dwellSeconds':0 if i==0 else max(12,sec(call['departure'])-sec(call['arrival'])),'locationSource':'Official GTFS / OpenStreetMap match','platformSource':'OpenStreetMap' if platform_index>=0 else 'UNKNOWN','targetClassification':'DERIVED'})
    journey={'service':{'route':trip.get('route_id','TRAIN'),'tripId':tid,'tripShortName':trip.get('trip_short_name',''),'headsign':trip.get('trip_headsign',definition['destination']),'serviceDate':definition['serviceDate'],'feed':GTFS.name,'publisher':'Geschäftsstelle SKI on behalf of BAV','classification':'REAL STATIC TIMETABLE'},'direction':definition['name'],'scenarioStart':calls[0]['departure'],'stops':call_defs,'platformsMatched':sum(x['platformIndex']>=0 for x in call_defs),'generatedFrom':'official GTFS stop sequence plus OSM station/platform geometry'};(out/'journey.json').write_text(json.dumps(journey,separators=(',',':')))
    # Discover an actual opposing trip automatically and orient the same graph path
    # in the opposite direction. The path is derived; its timetable remains real.
    reverse_definition=definition|{'origin':definition['destination'],'destination':definition['origin'],'preferredDeparture':calls[0]['departure']};reverse_tid,reverse_calls,reverse_trip,reverse_candidates=resolve_trip(reverse_definition);route_xy=[(p['x'],p['z']) for p in points];edge_by_id={e['id']:e for e in edges};forward_parts=[]
    for edge_id in player:
        edge=edge_by_id[edge_id];first=edge['points'][0];last=edge['points'][-1];i0=min(range(len(route_xy)),key=lambda i:(route_xy[i][0]-first[0])**2+(route_xy[i][1]-first[2])**2);i1=min(range(len(route_xy)),key=lambda i:(route_xy[i][0]-last[0])**2+(route_xy[i][1]-last[2])**2);forward_parts.append({'edgeId':edge_id,'reverse':i1<i0})
    ai={'id':'ai_1','tripId':reverse_tid,'publicName':reverse_trip.get('trip_short_name') or reverse_trip.get('route_id','Train'),'headsign':reverse_trip.get('trip_headsign',definition['origin']),'direction':f"{definition['destination']} → {definition['origin']}",'stops':reverse_calls,'path':[{'edgeId':p['edgeId'],'reverse':not p['reverse']} for p in reversed(forward_parts)],'timetableClassification':'REAL STATIC TIMETABLE','pathClassification':'DERIVED FROM OSM GRAPH','motionClassification':'SIMULATED AUTHORITY-CONSTRAINED DRIVER'}
    traffic={'version':1,'id':f'{route_id}-{definition["serviceDate"]}','name':definition['name'],'serviceDate':definition['serviceDate'],'feed':GTFS.name,'publisher':'Geschäftsstelle SKI on behalf of BAV','window':{'start':calls[0]['departure'],'end':calls[-1]['arrival']},'playerTripId':tid,'services':[ai],'stats':{'candidateTrips':candidate_trips+reverse_candidates,'selectedAiServices':1,'playerTripActiveOnDate':True}};(out/'traffic.json').write_text(json.dumps(traffic,separators=(',',':')))
    # SWISSIMAGE route-chain sectors.
    route_imagery=out/'imagery'
    if route_imagery.exists():
        for stale in route_imagery.glob('*'):stale.unlink()
        route_imagery.rmdir()
    imagery=PUBLIC/'tiles/imagery';imagery.mkdir(parents=True,exist_ok=True);tile_columns=max(1,math.ceil((width-1)*spacing/4000));splits=[round(i*(width-1)/tile_columns) for i in range(tile_columns+1)];tiles=[];raw_dir=RAW/'route-compiler'/route_id;raw_dir.mkdir(parents=True,exist_ok=True)
    for i,(c0,c1) in enumerate(zip(splits,splits[1:])):
        x0=minx+c0*spacing;x1=minx+c1*spacing;z0=minz;z1=maxz;bbox=(origin_e+x0,origin_n-z1,origin_e+x1,origin_n-z0);px=1024;py=max(256,round(px*(z1-z0)/(x1-x0)));params={'SERVICE':'WMS','VERSION':'1.1.1','REQUEST':'GetMap','LAYERS':'ch.swisstopo.swissimage','STYLES':'','SRS':'EPSG:2056','BBOX':','.join(map(str,bbox)),'WIDTH':px,'HEIGHT':py,'FORMAT':'image/jpeg'};jpg=raw_dir/f'{i}.jpg'
        if force or not jpg.exists():urllib.request.urlretrieve('https://wms.geo.admin.ch/?'+urllib.parse.urlencode(params),jpg)
        temp=imagery/f'.{route_id}-{i}.webp';Image.open(jpg).save(temp,'WEBP',quality=76,method=6);digest=hashlib.sha256(temp.read_bytes()).hexdigest()[:16];final=imagery/f'swissimage-{digest}.webp'
        if final.exists():temp.unlink()
        else:temp.replace(final)
        geographic_id=f"lv95-{round(bbox[0]/100)*100}-{round(bbox[1]/100)*100}-{round(bbox[2]/100)*100}-{round(bbox[3]/100)*100}";tiles.append({'id':f'scenery-{i}','geographicId':geographic_id,'contentHash':digest,'bounds':{'minX':x0,'maxX':x1,'minZ':z0,'maxZ':z1},'terrain':{'columnStart':c0,'columnEnd':c1},'imagery':{'url':f'../tiles/imagery/{final.name}','format':'WebP','width':px,'height':py,'metresPerPixel':round((x1-x0)/px,2),'source':'SWISSIMAGE via official WMS','classification':'REAL'}})
    scenery={'corridor':route_id,'version':2,'crs':'EPSG:2056 → local X east, Y up, Z south','localOrigin':{'easting':origin_e,'northing':origin_n,'elevation':profile[0]},'tiles':tiles,'sources':[{'dataset':'SWISSIMAGE','publisher':'swisstopo','attribution':'© swisstopo'}]};(out/'scenery-manifest.json').write_text(json.dumps(scenery,separators=(',',':')))
    signal_coverage=len(used_signal_s)
    speed_intervals=sorted((max(0,float(x['start'])),min(route_length,float(x['end']))) for x in limits if x['source']=='OpenStreetMap')
    merged=[]
    for start,end in speed_intervals:
        if end<=start: continue
        if merged and start<=merged[-1][1]: merged[-1]=(merged[-1][0],max(merged[-1][1],end))
        else: merged.append((start,end))
    speed_coverage=round(min(1,sum(end-start for start,end in merged)/route_length),2)
    package={'schemaVersion':1,'id':route_id,'name':definition['name'],'description':definition['description'],'supportTier':'PARTIAL','sourceDate':definition['serviceDate'],'timezone':'Europe/Zurich','localOriginLv95':{'easting':origin_e,'northing':origin_n,'elevation':profile[0]},'boundsLv95':{'minEasting':origin_e+minx,'maxEasting':origin_e+maxx,'minNorthing':origin_n-maxz,'maxNorthing':origin_n-minz},'routeLengthM':round(route_length,1),'playerService':{'name':f"{trip.get('trip_short_name') or trip.get('route_id','Train')}",'tripId':tid,'serviceDate':definition['serviceDate']},'assets':{'route':'route.json','terrain':'terrain.json','scenery':'scenery-manifest.json','landscape':'landscape.json','journey':'journey.json','railNetwork':'rail-network.json','traffic':'traffic.json'},'capabilities':{'standardGauge':True,'adhesion':True,'conventionalSignals':bool(used_signal_s),'etcsL2':False,'rack':False,'tram':False},'coverage':{'mappedSignals':signal_coverage,'scenarioSignals':len(scenario),'speedLimit':speed_coverage,'platformMatching':round(journey['platformsMatched']/len(call_defs),2)},'sources':{'terrain':{'classification':'REAL','dataset':'swissALTI3D','date':datetime.date.today().isoformat()},'imagery':{'classification':'REAL','dataset':'SWISSIMAGE','date':datetime.date.today().isoformat()},'railway':{'classification':'OPEN_MAPPING','dataset':'OpenStreetMap cached corridor extract','date':'2026-08-24'},'timetable':{'classification':'REAL','dataset':GTFS.name,'date':definition['serviceDate']},'operations':{'classification':'SIMULATED','dataset':'Open Swiss Rail Sim operating model'}},'testCheckpoints':[{'id':'start','s':0,'kind':'start'},{'id':'quarter','s':round(route_length*.25),'kind':'route'},{'id':'middle','s':round(route_length*.5),'kind':'route'},{'id':'junction','s':round(route_length*.75),'kind':'network'},{'id':'end','s':round(route_length-20),'kind':'end'}],'compileReport':{'railPath':{'status':'ok','coverage':1},'signals':{'mapped':signal_coverage,'scenario':len(scenario),'largestMappedGapM':None},'speedLimits':{'coverage':speed_coverage},'platforms':{'coverage':round(journey['platformsMatched']/len(call_defs),2)},'traffic':{'services':1,'status':'ok'}},'packageBytes':0}
    graph_manifest=ROOT/'data/manifests/national-rail-graph.json'
    if graph_manifest.exists():package['nationalRailGraph']={key:json.loads(graph_manifest.read_text())[key] for key in ('schemaVersion','contentHash','source')}
    package['sharedAssetBytes']=sum((PUBLIC/'tiles/imagery'/pathlib.Path(tile['imagery']['url']).name).stat().st_size for tile in tiles);(out/'package.json').write_text(json.dumps(package,indent=2)+'\n');package['packageBytes']=sum(p.stat().st_size for p in out.rglob('*') if p.is_file());(out/'package.json').write_text(json.dumps(package,indent=2)+'\n');report|={'status':'compiled','trackEdges':len(edges),'playerRouteEdges':len(player),'mappedSignalsAccepted':signal_coverage,'scenarioSignals':len(scenario),'terrainTiles':len(tiles),'aiServices':1,'packageBytes':package['packageBytes'],'sharedAssetBytes':package['sharedAssetBytes'],'seconds':round(time.perf_counter()-started,2),'tripId':tid};print(json.dumps(report,indent=2));return report
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--route',choices=DEFS);parser.add_argument('--trip-id');parser.add_argument('--from-station');parser.add_argument('--to-station');parser.add_argument('--service-date',default='2026-08-22');parser.add_argument('--preferred-departure',default='14:00:00');parser.add_argument('--id');parser.add_argument('--analyse-only',action='store_true');parser.add_argument('--force',action='store_true');parser.add_argument('--all',action='store_true');args=parser.parse_args();ids=list(DEFS) if args.all else [args.route] if args.route else []
    if args.trip_id and args.from_station and args.to_station and not args.route:
        route_id=args.id or re.sub('[^a-z0-9]+','-',f'{args.from_station}-{args.to_station}-{args.trip_id[-8:]}'.lower()).strip('-');DEFS[route_id]={'origin':args.from_station,'destination':args.to_station,'serviceDate':args.service_date,'preferredDeparture':args.preferred_departure,'name':f'{args.from_station} → {args.to_station}','description':'Automatically resolved official Swiss timetable service'};ids=[route_id]
    if not ids:parser.error('--route/--all or --trip-id with --from-station and --to-station required')
    reports=[]
    for route_id in ids:reports.append(compile_route(route_id,DEFS[route_id],args.force,args.analyse_only,args.trip_id))
    if not args.analyse_only:
        routes=[]
        for path in sorted(PUBLIC.glob('*/package.json')):
            package=json.loads(path.read_text());routes.append({key:package[key] for key in ('id','name','description','supportTier','routeLengthM','playerService','coverage','packageBytes')})
        routes.sort(key=lambda item:(item['id']!='rapperswil-uznach',item['name']))
        (PUBLIC/'routes.json').write_text(json.dumps({'schemaVersion':1,'routes':routes},indent=2)+'\n')
    print(json.dumps({'routes':reports},indent=2))
if __name__=='__main__':main()
