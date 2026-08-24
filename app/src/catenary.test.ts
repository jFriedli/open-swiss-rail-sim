import {describe,expect,it} from 'vitest';
import * as THREE from 'three';
import {TrackFrameSampler} from './track-frame';
import {buildContactWire} from './catenary';

describe('catenary spans',()=>{
  const route=new TrackFrameSampler([new THREE.Vector3(0,0,0),new THREE.Vector3(50,1,0),new THREE.Vector3(100,2,25),new THREE.Vector3(150,2,50)]);
  it('is finite, bounded and route-monotonic',()=>{const result=buildContactWire(route,25);expect([...result.positions].every(Number.isFinite)).toBe(true);expect(result.stats.spanCount).toBeGreaterThan(5);expect(result.stats.maxLength).toBeLessThan(31.25);expect(result.stats.maxVerticalDelta).toBeLessThan(8)});
  it('rejects spacing that could create giant spans',()=>expect(()=>buildContactWire(route,500)).toThrow(/spacing/));
});
