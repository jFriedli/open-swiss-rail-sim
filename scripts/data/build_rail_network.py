#!/usr/bin/env python3
"""Build a compact railway graph from the cached corridor Overpass extract.

Ways are split only at shared OSM nodes, explicit railway switches, and endpoints.
Projected line crossings are deliberately never joined.
"""
import collections,json,math,pathlib

SOURCE=pathlib.Path('data/intermediate/candidates/rapperswil_uznach.json')
ROUTE=pathlib.Path('public/data/rapperswil-uznach/route.json')
TERRAIN=pathlib.Path('public/data/rapperswil-uznach/terrain.json')
LANDSCAPE=pathlib.Path('public/data/rapperswil-uznach/landscape.json')
OUT=pathlib.Path('public/data/rapperswil-uznach/rail-network.json')

def wgs_to_lv95(lat,lon):
    p=(lat*3600-169028.66)/10000;l=(lon*3600-26782.5)/10000
    return (2600072.37+211455.93*l-10938.51*l*p-.36*l*p*p-44.54*l*l*l,
            1200147.07+308807.95*p+3745.25*l*l+76.63*p*p-194.56*l*l*p+119.79*p*p*p)

def main():
    osm=json.loads(SOURCE.read_text());route=json.loads(ROUTE.read_text());terrain=json.loads(TERRAIN.read_text());land=json.loads(LANDSCAPE.read_text())
    oe=wgs_to_lv95(route['points'][0]['lat'],route['points'][0]['lon'])[0];on=wgs_to_lv95(route['points'][0]['lat'],route['points'][0]['lon'])[1]
    ways=[x for x in osm['elements'] if x['type']=='way' and x.get('tags',{}).get('railway')=='rail']
    switches={x['id']:x for x in osm['elements'] if x['type']=='node' and x.get('tags',{}).get('railway')=='switch'}
    degree=collections.Counter(n for w in ways for n in w.get('nodes',[]));coords={}
    for w in ways:
        for nid,p in zip(w.get('nodes',[]),w.get('geometry',[])):coords[nid]=(p['lat'],p['lon'])
    def terrain_at(x,z):
        gx=max(0,min(terrain['width']-1.001,(x-terrain['originX'])/terrain['spacingM']));gz=max(0,min(terrain['height']-1.001,(z-terrain['originZ'])/terrain['spacingM']));x0=int(gx);z0=int(gz);tx=gx-x0;tz=gz-z0;h=terrain['heights'];w=terrain['width'];a=h[z0*w+x0];b=h[z0*w+x0+1];c=h[(z0+1)*w+x0];d=h[(z0+1)*w+x0+1];return (a+(b-a)*tx)+(c+(d-c)*tx-(a+(b-a)*tx))*tz
    def local(nid):
        e,n=wgs_to_lv95(*coords[nid]);x=e-oe;z=-(n-on);return [round(x,2),round(terrain_at(x,z)+.52,2),round(z,2)]
    split={nid for nid,count in degree.items() if count!=2}|set(switches)
    raw=[]
    for way in ways:
        nodes=way['nodes'];start=0
        for i in range(1,len(nodes)):
            if nodes[i] in split or i==len(nodes)-1:
                segment=nodes[start:i+1]
                if len(segment)>1:raw.append((way,segment))
                start=i
    graph_nodes={};edges=[]
    for index,(way,nodes) in enumerate(raw):
        points=[local(n) for n in nodes if n in coords]
        if len(points)<2:continue
        length=sum(math.dist(a,c) for a,c in zip(points,points[1:]));
        if length<.5:continue
        for nid in (nodes[0],nodes[-1]):
            if nid not in coords:continue
            graph_nodes[str(nid)]={'id':str(nid),'position':local(nid),'type':'switch' if nid in switches else ('connection' if degree[nid]>1 else 'buffer'),'osmNodeId':nid,'tags':switches.get(nid,{}).get('tags',{})}
        tags=way.get('tags',{});edges.append({'id':f'e{len(edges)}','osmWayId':way['id'],'from':str(nodes[0]),'to':str(nodes[-1]),'points':points,'lengthM':round(length,2),'maxSpeedKmh':int(tags['maxspeed']) if str(tags.get('maxspeed','')).isdigit() else 80,'electrified':tags.get('electrified')=='contact_line','service':tags.get('service','main'),'usage':tags.get('usage',''),'trackRef':tags.get('railway:track_ref',tags.get('ref','')),'source':'OpenStreetMap'})
    # Match the existing smoothed player centreline to its nearest graph edge sequence.
    player=[]
    for p in route['points'][::4]:
        best=min(edges,key=lambda e:min((q[0]-p['x'])**2+(q[2]-p['z'])**2 for q in e['points']))
        if not player or player[-1]!=best['id']:player.append(best['id'])
    # Associate platform polygons to nearest edge, retaining the real polygon index.
    platforms=[]
    for i,poly in enumerate(land['platforms']):
        centre=[sum(p[0] for p in poly)/len(poly),sum(p[1] for p in poly)/len(poly)]
        edge=min(edges,key=lambda e:min((q[0]-centre[0])**2+(q[2]-centre[1])**2 for q in e['points']))
        distance=min(math.hypot(q[0]-centre[0],q[2]-centre[1]) for q in edge['points']);platforms.append({'platformIndex':i,'edgeId':edge['id'],'distanceM':round(distance,2),'source':'OpenStreetMap / DERIVED association'})
    adjacency=collections.defaultdict(list)
    for e in edges:adjacency[e['from']].append(e['id']);adjacency[e['to']].append(e['id'])
    components=[];remaining=set(graph_nodes)
    while remaining:
        todo=[remaining.pop()];seen=set(todo)
        while todo:
            n=todo.pop()
            for eid in adjacency[n]:
                e=edges[int(eid[1:])];other=e['to'] if e['from']==n else e['from']
                if other not in seen:seen.add(other);remaining.discard(other);todo.append(other)
        components.append(len(seen))
    payload={'version':1,'source':'OpenStreetMap','classification':'OPEN_MAPPING / DERIVED GRAPH','nodes':list(graph_nodes.values()),'edges':edges,'switches':[{'id':str(n),'nodeId':str(n),'state':'NORMAL','source':'OpenStreetMap location / SIMULATED state'} for n in switches if str(n) in graph_nodes],'platformAssociations':platforms,'playerRouteEdges':player,'stats':{'nodes':len(graph_nodes),'edges':len(edges),'switches':sum(n in coords for n in switches),'totalTrackKm':round(sum(e['lengthM'] for e in edges)/1000,2),'connectedComponents':len(components),'componentNodeCounts':sorted(components,reverse=True),'playerRouteEdges':len(player)}}
    OUT.write_text(json.dumps(payload,separators=(',',':')));pathlib.Path('data/manifests/rail-network.json').write_text(json.dumps(payload['stats'],indent=2)+'\n');print(json.dumps(payload['stats'],indent=2))

if __name__=='__main__':main()
