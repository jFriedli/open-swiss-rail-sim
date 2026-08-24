import * as THREE from 'three';
import type {TrackFrameSampler} from './track-frame';

export type CatenaryStats={spanCount:number;maxLength:number;maxVerticalDelta:number;maxHorizontalDelta:number};

/** Build independent, lightly sagged contact-wire spans. No curve joins span boundaries. */
export function buildContactWire(route:TrackFrameSampler,spacing=55,height=5.65){
  if(!(spacing>0&&spacing<=80))throw Error(`invalid catenary spacing ${spacing}`);
  const anchors:{s:number;p:THREE.Vector3}[]=[];
  for(let s=0;s<route.length;s+=spacing)anchors.push({s,p:route.sample(s).position.clone().add(new THREE.Vector3(0,height,0))});
  anchors.push({s:route.length,p:route.sample(route.length).position.clone().add(new THREE.Vector3(0,height,0))});
  const positions:number[]=[];let maxLength=0,maxVerticalDelta=0,maxHorizontalDelta=0;
  for(let i=0;i<anchors.length-1;i++){
    const a=anchors[i],b=anchors[i+1],ds=b.s-a.s,vertical=Math.abs(b.p.y-a.p.y),horizontal=Math.hypot(b.p.x-a.p.x,b.p.z-a.p.z),length=a.p.distanceTo(b.p);
    if(![...a.p.toArray(),...b.p.toArray(),ds,length].every(Number.isFinite))throw Error(`non-finite catenary span ${i}`);
    if(ds<=0||ds>spacing+1e-6||length>spacing*1.25||vertical>8)throw Error(`implausible catenary span ${i}: ds=${ds}, length=${length}, dy=${vertical}`);
    maxLength=Math.max(maxLength,length);maxVerticalDelta=Math.max(maxVerticalDelta,vertical);maxHorizontalDelta=Math.max(maxHorizontalDelta,horizontal);
    let previous=a.p;
    for(let step=1;step<=4;step++){const t=step/4,current=a.p.clone().lerp(b.p,t);current.y-=Math.sin(Math.PI*t)*.12;positions.push(...previous.toArray(),...current.toArray());previous=current}
  }
  return {positions:new Float32Array(positions),stats:{spanCount:anchors.length-1,maxLength,maxVerticalDelta,maxHorizontalDelta}};
}
