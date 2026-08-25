#!/usr/bin/env python3
"""Search official services and resolve their calls through the national OSM rail graph."""
from __future__ import annotations
import argparse,gzip,heapq,json,math,time,unicodedata
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];INDEX=ROOT/'public/data/national/service-index.json';GRAPH=ROOT/'data/national/rail-graph.json.gz'
def normalize(value):return ''.join(c for c in unicodedata.normalize('NFKD',value.casefold().replace('ü','ue').replace('ö','oe').replace('ä','ae')) if not unicodedata.combining(c))
def distance(a,b):
    y=math.radians((a[0]+b[0])/2);return math.hypot((a[0]-b[0])*111320,(a[1]-b[1])*111320*math.cos(y))
class Resolver:
    def __init__(self):
        self.index=json.loads(INDEX.read_text());self.stations=self.index['stations'];self.trips=self.index['trips'];started=time.perf_counter()
        with gzip.open(GRAPH,'rt') as source:self.graph=json.load(source)
        self.coords={n[0]:(n[1],n[2]) for n in self.graph['nodes']};self.components={n[0]:n[3] for n in self.graph['nodes']};self.adj=defaultdict(list)
        for edge_id,(a,b,length,way,tags) in enumerate(self.graph['edges']):self.adj[a].append((b,length,edge_id,tags));self.adj[b].append((a,length,edge_id,tags))
        self.grid=defaultdict(list)
        for node,(lat,lon) in self.coords.items():self.grid[(round(lat*100),round(lon*100))].append(node)
        self.load_ms=(time.perf_counter()-started)*1000
    def station_matches(self,text,limit=8):
        query=normalize(text);ranked=[]
        for i,row in enumerate(self.stations):
            name=row[4]
            if query in name:ranked.append((0 if name==query else 1 if name.startswith(query) else 2,len(name),i))
        return [i for *_,i in sorted(ranked)[:limit]]
    def search(self,origin,destination,around=None,limit=12):
        origins=set(self.station_matches(origin,20));destinations=set(self.station_matches(destination,20));results=[]
        for trip in self.trips:
            calls=trip[4];oi=next((i for i,s in enumerate(calls) if s in origins),None)
            if oi is None:continue
            di=next((i for i,s in enumerate(calls[oi+1:],oi+1) if s in destinations),None)
            if di is None:continue
            departure=trip[6][oi];delta=abs(departure-around) if around is not None else 0
            results.append((delta,departure,trip,oi,di))
        return sorted(results,key=lambda x:(x[0],x[1]))[:limit]
    def nearest_node(self,station_index):
        _,_,lat,lon,_=self.stations[station_index];candidates=[]
        for radius in range(1,8):
            for y in range(round(lat*100)-radius,round(lat*100)+radius+1):
                for x in range(round(lon*100)-radius,round(lon*100)+radius+1):candidates.extend(self.grid.get((y,x),()))
            if candidates:break
        if not candidates:raise RuntimeError('no national rail node near station')
        node=min(set(candidates),key=lambda n:distance((lat,lon),self.coords[n]));return node,distance((lat,lon),self.coords[node])
    def path(self,start,goal,max_expansions=400000):
        if self.components.get(start)!=self.components.get(goal):raise RuntimeError('stations lie in disconnected rail components')
        queue=[(distance(self.coords[start],self.coords[goal]),0,start)];cost={start:0};previous={};expansions=0
        while queue:
            _,g,node=heapq.heappop(queue)
            if g!=cost[node]:continue
            if node==goal:break
            expansions+=1
            if expansions>max_expansions:raise RuntimeError('path search expansion limit exceeded')
            for nxt,length,edge,tags in self.adj[node]:
                penalty=1+(4 if tags.get('service') in {'yard','siding','spur'} else 0)+(2 if tags.get('usage') in {'industrial','military'} else 0);ng=g+length*penalty
                if ng<cost.get(nxt,1e30):cost[nxt]=ng;previous[nxt]=(node,edge);heapq.heappush(queue,(ng+distance(self.coords[nxt],self.coords[goal]),ng,nxt))
        if goal not in cost:raise RuntimeError('rail path unresolved')
        nodes=[goal];edges=[]
        while nodes[-1]!=start:node,edge=previous[nodes[-1]];nodes.append(node);edges.append(edge)
        nodes.reverse();edges.reverse();return nodes,edges,expansions
    def resolve(self,trip_id,from_name=None,to_name=None):
        trip=next((x for x in self.trips if x[0]==trip_id),None)
        if not trip:raise RuntimeError('trip not in service-date index')
        start=0;end=len(trip[4])-1
        if from_name:
            matches=set(self.station_matches(from_name,30));start=next((i for i,s in enumerate(trip[4]) if s in matches),-1)
            if start<0:raise RuntimeError('origin is not a call on trip')
        if to_name:
            matches=set(self.station_matches(to_name,30));end=next((i for i,s in enumerate(trip[4][start+1:],start+1) if s in matches),-1)
            if end<0:raise RuntimeError('destination is not a later call on trip')
        selected_stations=trip[4][start:end+1];selected_arrivals=trip[5][start:end+1];selected_departures=trip[6][start:end+1]
        started=time.perf_counter();anchors=[];max_offset=0
        for station in selected_stations:
            node,offset=self.nearest_node(station);anchors.append(node);max_offset=max(max_offset,offset)
        all_nodes=[];all_edges=[];expansions=0
        for origin_node,destination_node in zip(anchors,anchors[1:]):
            if origin_node==destination_node:continue
            nodes,edges,count=self.path(origin_node,destination_node);all_nodes+=nodes[:-1];all_edges+=edges;expansions+=count
        all_nodes.append(anchors[-1]);length=sum(self.graph['edges'][edge][2] for edge in all_edges);elapsed=(selected_arrivals[-1]-selected_departures[0]);ratio=length/max(1,elapsed)
        mapped_signals=len(set(all_nodes)&set(self.graph.get('signalNodeIds',[])));speed_length=sum(self.graph['edges'][edge][2] for edge in all_edges if str(self.graph['edges'][edge][4].get('maxspeed','')).isdigit());speed_coverage=round(speed_length/max(1,length),3)
        if max_offset>1500:tier='UNSUPPORTED';reason='timetable stop cannot be matched reliably to standard-gauge graph'
        elif not all_edges:tier='UNSUPPORTED';reason='no connected railway path'
        elif max_offset>500 or ratio>70:tier='PARTIAL';reason='low-confidence station/path association'
        elif mapped_signals and speed_coverage>=.6:tier='FULL';reason='supported-class path with usable mapped signals and speed coverage'
        else:tier='PARTIAL';reason='path resolved; sparse signals or speed data require scenario completion'
        return {'tripId':trip_id,'service':trip[2] or trip[1],'headsign':trip[3],'serviceDate':self.index['serviceDate'],'stops':[{'id':self.stations[s][0],'name':self.stations[s][1],'lat':self.stations[s][2],'lon':self.stations[s][3],'arrival':selected_arrivals[i],'departure':selected_departures[i]} for i,s in enumerate(selected_stations)],'supportTier':tier,'reason':reason,'path':{'nodeIds':all_nodes,'edgeIndexes':all_edges,'lengthM':round(length,1),'maxStationOffsetM':round(max_offset,1),'mappedSignals':mapped_signals,'speedCoverage':speed_coverage,'expansions':expansions,'confidence':'HIGH' if max_offset<=250 else 'MEDIUM' if max_offset<=500 else 'LOW'},'resolveMs':round((time.perf_counter()-started)*1000,2),'graphHash':self.graph.get('source',{}).get('contentHash')}
def clock(value):
    h,m=map(int,value.split(':')[:2]);return h*3600+m*60
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--from-station');parser.add_argument('--to-station');parser.add_argument('--time');parser.add_argument('--trip-id');parser.add_argument('--resolve',action='store_true');parser.add_argument('--output',type=Path);args=parser.parse_args();resolver=Resolver()
    if args.trip_id:result=resolver.resolve(args.trip_id)
    else:
        if not args.from_station or not args.to_station:parser.error('--from-station and --to-station required')
        found=resolver.search(args.from_station,args.to_station,clock(args.time) if args.time else None);result={'serviceDate':resolver.index['serviceDate'],'loadMs':round(resolver.load_ms,2),'results':[{'tripId':trip[0],'service':trip[2] or trip[1],'headsign':trip[3],'departure':trip[6][oi],'arrival':trip[5][di],'from':resolver.stations[trip[4][oi]][1],'to':resolver.stations[trip[4][di]][1]} for _,_,trip,oi,di in found]}
        if args.resolve:
            for item in result['results']:
                try:item['resolution']=resolver.resolve(item['tripId'])
                except Exception as exc:item['resolution']={'supportTier':'UNRESOLVED','reason':str(exc)}
    encoded=json.dumps(result,indent=2,ensure_ascii=False)
    if args.output:args.output.write_text(encoded+'\n')
    print(encoded)
if __name__=='__main__':main()
