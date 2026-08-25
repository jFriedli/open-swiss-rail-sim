#!/usr/bin/env python3
"""Generic deployability checks for compiled RoutePackages."""
from __future__ import annotations
import json,math
from pathlib import Path

TRAIN_LENGTH_M=75.0

def _clock(value):
    h,m,s=map(int,value.split(':'));return h*3600+m*60+s
def _xz_distance(a,b):return math.hypot(a[0]-b[0],a[2]-b[2])
def _heading(a,b):return math.atan2(b[0]-a[0],-(b[2]-a[2]))
def _delta(a,b):return abs(math.degrees(math.atan2(math.sin(b-a),math.cos(b-a))))

class RouteQualityValidator:
    """Validate geometry, start state, occupancy, scenery and route progression."""
    def __init__(self,package_dir:Path):
        self.directory=package_dir;self.errors=[];self.warnings=[];self.metrics={}
        self.package=json.loads((package_dir/'package.json').read_text())
        def asset(name):return json.loads((package_dir/self.package['assets'][name]).read_text())
        self.route=asset('route');self.terrain=asset('terrain');self.network=asset('railNetwork');self.journey=asset('journey');self.traffic=asset('traffic');self.scenery=asset('scenery');self.landscape=asset('landscape')
    def fail(self,code,detail):self.errors.append({'code':code,'detail':detail})
    def warn(self,code,detail):self.warnings.append({'code':code,'detail':detail})
    def validate_geometry(self):
        points=self.route['points'];extreme=[]
        for i in range(1,len(points)-1):
            a,b,c=points[i-1],points[i],points[i+1];d=_delta(_heading((a['x'],a['y'],a['z']),(b['x'],b['y'],b['z'])),_heading((b['x'],b['y'],b['z']),(c['x'],c['y'],c['z'])))
            if d>120 and c['s']-a['s']<150:extreme.append({'s':b['s'],'headingDeltaDeg':round(d,1)})
        if extreme:self.fail('PATH_EXTREME_TURN',extreme[:10])
        # Returning close to the origin after a substantial initial detour is a
        # terminal/backtracking signature, not an ordinary tight curve.
        origin=(points[0]['x'],points[0]['y'],points[0]['z']);returns=[p for p in points if 250<p['s']<2000 and _xz_distance(origin,(p['x'],p['y'],p['z']))<80]
        if returns:self.fail('ORIGIN_BACKTRACK',{'returnChainageM':returns[0]['s'],'distanceFromOriginM':round(_xz_distance(origin,(returns[0]['x'],returns[0]['y'],returns[0]['z'])),1)})
        stop=self.journey['stops'][1];target=min(points,key=lambda p:abs(p['s']-stop['targetS']));tangent=(points[1]['x']-points[0]['x'],points[1]['z']-points[0]['z']);toward=(target['x']-points[0]['x'],target['z']-points[0]['z']);dot=sum(a*b for a,b in zip(tangent,toward))/(math.hypot(*tangent)*math.hypot(*toward) or 1)
        self.metrics['playerStartForwardDot']=round(dot,4)
        if dot<.25:self.fail('PLAYER_START_ORIENTATION',{'dotToNextStop':round(dot,3)})
    def validate_path(self):
        ids=self.network['playerRouteEdges'];edges={e['id']:e for e in self.network['edges']};seen={};repeated=[]
        for i,eid in enumerate(ids):
            if eid in seen:repeated.append({'edgeId':eid,'firstIndex':seen[eid],'repeatIndex':i})
            seen[eid]=i
        if repeated:self.fail('REPEATED_PLAYER_EDGE',repeated[:10])
        if any(b['targetS']<=a['targetS'] for a,b in zip(self.journey['stops'],self.journey['stops'][1:])):self.fail('NON_MONOTONIC_STOPS','timetable calls do not progress along route')
        if not ids or any(eid not in edges for eid in ids):self.fail('DISCONNECTED_PLAYER_PATH','empty or unknown player edge')
    def validate_start_occupancy(self):
        clock=_clock(self.journey['scenarioStart']);edge_by_id={e['id']:e for e in self.network['edges']};player=(self.route['points'][0]['x'],self.route['points'][0]['y'],self.route['points'][0]['z']);overlaps=[]
        for service in self.traffic.get('services',[]):
            if not service.get('stops'):continue
            first=service['stops'][0];active=_clock(first['arrival'])<=clock<=_clock(first['departure'])
            if not active:continue
            part=service.get('path',[None])[0]
            if not part or part['edgeId'] not in edge_by_id:continue
            edge=edge_by_id[part['edgeId']];p=(edge['points'][-1] if part.get('reverse') else edge['points'][0]);distance=_xz_distance(player,p)
            if distance<TRAIN_LENGTH_M:overlaps.append({'train':service['id'],'publicName':service.get('publicName'),'distanceM':round(distance,1),'edgeId':part['edgeId']})
        self.metrics['initialTrainOverlaps']=len(overlaps)
        if overlaps:self.fail('INITIAL_OCCUPANCY_OVERLAP',overlaps)
    def validate_scenery(self):
        tiles=self.scenery.get('tiles',[]);start=self.route['points'][0];near=[t for t in tiles if t['bounds']['minX']-100<=start['x']<=t['bounds']['maxX']+100 and t['bounds']['minZ']-100<=start['z']<=t['bounds']['maxZ']+100]
        if not near:self.fail('START_SCENERY_MISSING','no terrain/imagery sector covers player start')
        self.metrics['startSceneryTiles']=len(near);self.metrics['buildings']=sum(t.get('buildingCount',0) for t in self.scenery.get('buildings',{}).get('tiles',[]))
    def run(self):
        self.validate_geometry();self.validate_path();self.validate_start_occupancy();self.validate_scenery()
        return {'routeId':self.package['id'],'deployable':not self.errors,'errors':self.errors,'warnings':self.warnings,'metrics':self.metrics}

def validate_package(path:Path):return RouteQualityValidator(path).run()
