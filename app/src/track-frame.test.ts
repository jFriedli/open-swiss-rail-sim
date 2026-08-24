import {describe,it,expect} from 'vitest';import * as THREE from 'three';import {TrackFrameSampler} from './track-frame';
const route=new TrackFrameSampler([new THREE.Vector3(0,0,0),new THREE.Vector3(50,1,20),new THREE.Vector3(100,2,0)]);
describe('canonical track frame',()=>{
  it('keeps gauge and midpoint exact',()=>{for(let s=0;s<=route.length;s+=2){const l=route.offsetPoint(s,-1.435/2),r=route.offsetPoint(s,1.435/2),c=route.sample(s).position;expect(l.distanceTo(r)).toBeCloseTo(1.435,8);expect(l.clone().add(r).multiplyScalar(.5).distanceTo(c)).toBeLessThan(1e-9)}});
  it('is finite, orthonormal and flip-free',()=>{let prior=route.sample(0).right;for(let s=0;s<=route.length;s+=1){const f=route.sample(s);for(const v of [...f.position,...f.tangent,...f.right,...f.up])expect(Number.isFinite(v)).toBe(true);expect(Math.abs(f.tangent.dot(f.right))).toBeLessThan(1e-8);expect(f.right.dot(prior)).toBeGreaterThan(.99);prior=f.right}});
  it('places trackside objects at their requested lateral distance',()=>{for(let s=0;s<route.length;s+=5)expect(route.offsetPoint(s,3).distanceTo(route.sample(s).position)).toBeCloseTo(3,8)});
  it('centres the train and makes sleeper long axes perpendicular',()=>{const localLong=new THREE.Vector3(1,0,0);for(let s=0;s<route.length;s+=3){const f=route.sample(s),sleeperAxis=localLong.clone().applyQuaternion(f.orientation);expect(f.position.distanceTo(route.sample(s).position)).toBe(0);expect(Math.abs(sleeperAxis.dot(f.tangent))).toBeLessThan(1e-8)}});
  it('keeps signals and catenary within their designed envelopes',()=>{for(let s=0;s<route.length;s+=7){expect(route.offsetPoint(s,2.65).distanceTo(route.sample(s).position)).toBeCloseTo(2.65,8);expect(route.offsetPoint(s,3.1).distanceTo(route.sample(s).position)).toBeCloseTo(3.1,8)}});
});
