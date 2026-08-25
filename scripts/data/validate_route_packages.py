#!/usr/bin/env python3
"""Fail CI when a committed RoutePackage is incomplete or internally invalid."""
import json,pathlib,sys
from route_quality import validate_package

ROOT=pathlib.Path(__file__).resolve().parents[2];DATA=ROOT/'public/data';errors=[]
catalog=json.loads((DATA/'routes.json').read_text())
if catalog.get('schemaVersion')!=1:errors.append('catalog schemaVersion must be 1')
for entry in catalog.get('routes',[]):
    package_dir=DATA/entry['id'];manifest_path=package_dir/'package.json'
    if not manifest_path.exists():errors.append(f"{entry['id']}: package.json missing");continue
    package=json.loads(manifest_path.read_text())
    if package.get('schemaVersion')!=1:errors.append(f"{entry['id']}: unsupported schema")
    if package.get('id')!=entry['id']:errors.append(f"{entry['id']}: catalogue/package id mismatch")
    if package.get('supportTier') not in ('FULL','PARTIAL','UNSUPPORTED'):errors.append(f"{entry['id']}: invalid support tier")
    for key,path in package.get('assets',{}).items():
        asset=package_dir/path
        if not asset.exists():errors.append(f"{entry['id']}: {key} asset missing: {path}")
    try:
        route=json.loads((package_dir/package['assets']['route']).read_text());network=json.loads((package_dir/package['assets']['railNetwork']).read_text());journey=json.loads((package_dir/package['assets']['journey']).read_text());traffic=json.loads((package_dir/package['assets']['traffic']).read_text());scenery=json.loads((package_dir/package['assets']['scenery']).read_text())
        points=route['points'];length=points[-1]['s'];edge_ids={edge['id'] for edge in network['edges']}
        if not points or any(not all(isinstance(p.get(k),(int,float)) for k in ('s','x','y','z','lat','lon')) for p in points):errors.append(f"{entry['id']}: invalid route points")
        if abs(length-package['routeLengthM'])>100:errors.append(f"{entry['id']}: manifest length differs from route")
        if not network['playerRouteEdges'] or not set(network['playerRouteEdges'])<=edge_ids:errors.append(f"{entry['id']}: disconnected/unknown player path")
        signals=route.get('signals',[])
        if any(b['s']<=a['s'] for a,b in zip(signals,signals[1:])):errors.append(f"{entry['id']}: signals are not strictly ordered")
        for service in traffic.get('services',[]):
            path={step['edgeId'] for step in service.get('path',[]) if isinstance(step,dict) and 'edgeId' in step}
            if not path or not path<=edge_ids:errors.append(f"{entry['id']}: AI {service.get('id')} has unknown/empty path")
        for tile in scenery.get('tiles',[]):
            imagery=(package_dir/pathlib.Path(package['assets']['scenery']).parent/tile['imagery']['url']).resolve()
            if not imagery.exists():errors.append(f"{entry['id']}: imagery missing: {tile['imagery']['url']}")
        if any(b['targetS']<a['targetS'] for a,b in zip(journey['stops'],journey['stops'][1:])):errors.append(f"{entry['id']}: station ordering invalid")
        if any(not 0<=checkpoint['s']<=length+10 for checkpoint in package['testCheckpoints']):errors.append(f"{entry['id']}: checkpoint outside route")
    except Exception as exc:errors.append(f"{entry['id']}: validation exception: {exc}")
    try:
        quality=validate_package(package_dir)
        package['qualityValidation']=quality
        for issue in quality['errors']:errors.append(f"{entry['id']}: {issue['code']}: {issue['detail']}")
    except Exception as exc:errors.append(f"{entry['id']}: quality validation exception: {exc}")
    print(f"{entry['id']}: {package['supportTier']} · {package['routeLengthM']/1000:.2f} km · {len(package.get('testCheckpoints',[]))} checkpoints")
if errors:
    print('\n'.join('ERROR '+error for error in errors),file=sys.stderr);raise SystemExit(1)
print(f'RoutePackage validation PASS ({len(catalog.get("routes",[]))} packages)')
