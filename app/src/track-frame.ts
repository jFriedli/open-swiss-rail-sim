import * as THREE from 'three';

export type TrackFrame={
  s:number; position:THREE.Vector3; tangent:THREE.Vector3;
  right:THREE.Vector3; up:THREE.Vector3; orientation:THREE.Quaternion;
  gradientPermille:number;
};

/** Stable no-cant railway frame. Local +Z is forward, +X is right, +Y is up. */
export class TrackFrameSampler{
  readonly curve:THREE.CatmullRomCurve3;
  readonly length:number;
  private readonly worldUp=new THREE.Vector3(0,1,0);
  constructor(points:THREE.Vector3[]){
    if(points.length<2)throw new Error('route requires at least two points');
    this.curve=new THREE.CatmullRomCurve3(points,false,'centripetal',0.15);
    this.curve.arcLengthDivisions=Math.max(2000,points.length*20);
    this.curve.updateArcLengths(); this.length=this.curve.getLength();
  }
  sample(distance:number):TrackFrame{
    const s=THREE.MathUtils.clamp(distance,0,this.length),u=this.length?s/this.length:0;
    const position=this.curve.getPointAt(u),tangent=this.curve.getTangentAt(u).normalize();
    const horizontal=new THREE.Vector3(tangent.x,0,tangent.z);
    if(horizontal.lengthSq()<1e-10)throw new Error(`vertical/zero route tangent at ${s}`);
    horizontal.normalize();
    const right=new THREE.Vector3().crossVectors(this.worldUp,horizontal).normalize();
    const up=new THREE.Vector3().crossVectors(tangent,right).normalize();
    const orientation=new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(right,up,tangent));
    return {s,position,tangent,right,up,orientation,gradientPermille:tangent.y/Math.hypot(tangent.x,tangent.z)*1000};
  }
  offsetPoint(s:number,lateral:number,vertical=0){const f=this.sample(s);return f.position.clone().addScaledVector(f.right,lateral).addScaledVector(f.up,vertical)}
}
