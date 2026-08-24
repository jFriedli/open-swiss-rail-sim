export type SectionState='FREE'|'OCCUPIED'|'RESERVED'|'UNKNOWN';
export type RouteRequest={id:string;owner:string;sections:string[];switches:{id:string;state:'NORMAL'|'REVERSE'}[]};
export class Interlocking{
  readonly occupants=new Map<string,Set<string>>();readonly routes=new Map<string,RouteRequest>();readonly switchState=new Map<string,'NORMAL'|'REVERSE'>();readonly switchLocks=new Map<string,string>();readonly events:string[]=[];
  constructor(sectionIds:string[],switchIds:string[]){sectionIds.forEach(id=>this.occupants.set(id,new Set));switchIds.forEach(id=>this.switchState.set(id,'NORMAL'))}
  setOccupancy(train:string,sections:string[]){for(const occupants of this.occupants.values())occupants.delete(train);for(const id of sections){const occupants=this.occupants.get(id);if(!occupants)throw Error(`unknown section ${id}`);occupants.add(train)}}
  sectionState(id:string){const occupants=this.occupants.get(id);if(!occupants)return 'UNKNOWN' as const;if(occupants.size)return 'OCCUPIED' as const;if([...this.routes.values()].some(route=>route.sections.includes(id)))return 'RESERVED' as const;return 'FREE' as const}
  request(request:RouteRequest){if(request.sections.some(id=>this.sectionState(id)!=='FREE')){this.events.push(`${request.id} denied: section unavailable`);return false}if(request.switches.some(sw=>!this.switchState.has(sw.id)||this.switchLocks.has(sw.id))){this.events.push(`${request.id} denied: switch unavailable`);return false}for(const sw of request.switches){this.switchState.set(sw.id,sw.state);this.switchLocks.set(sw.id,request.id)}this.routes.set(request.id,request);this.events.push(`${request.id} locked`);return true}
  release(id:string){this.routes.delete(id);for(const [sw,owner] of this.switchLocks)if(owner===id)this.switchLocks.delete(sw);this.events.push(`${id} released`)}
  moveSwitch(id:string,state:'NORMAL'|'REVERSE'){if(!this.switchState.has(id)||this.switchLocks.has(id))return false;this.switchState.set(id,state);return true}
  canClear(routeId:string){const route=this.routes.get(routeId);if(!route)return false;return route.sections.every(id=>{const state=this.sectionState(id);return state==='RESERVED'})&&route.switches.every(sw=>this.switchLocks.get(sw.id)===routeId&&this.switchState.get(sw.id)===sw.state)}
  reset(){for(const occupants of this.occupants.values())occupants.clear();this.routes.clear();this.switchLocks.clear();for(const id of this.switchState.keys())this.switchState.set(id,'NORMAL');this.events.length=0}
}
