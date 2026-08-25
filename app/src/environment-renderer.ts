import * as THREE from 'three';
import type {EnvironmentState} from './environment';

export type EnvironmentSurface='terrain'|'roof'|'wall'|'road'|'ballast'|'rail'|'vegetation';
export interface EnvironmentUniforms {daylight:{value:number};night:{value:number};wetness:{value:number};snow:{value:number};windowLight:{value:number};wind:{value:THREE.Vector2}}

export function createEnvironmentUniforms():EnvironmentUniforms{return {daylight:{value:1},night:{value:0},wetness:{value:0},snow:{value:0},windowLight:{value:0},wind:{value:new THREE.Vector2()}}}

export function environmentMaterial(material:THREE.MeshStandardMaterial,surface:EnvironmentSurface,uniforms:EnvironmentUniforms){
  const snowFactor={terrain:1,roof:.95,wall:.05,road:.22,ballast:.15,rail:.01,vegetation:.55}[surface],wetFactor={terrain:.3,roof:.55,wall:.2,road:1,ballast:.65,rail:.9,vegetation:.2}[surface];
  material.onBeforeCompile=shader=>{
    Object.assign(shader.uniforms,{envDaylight:uniforms.daylight,envNight:uniforms.night,envWetness:uniforms.wetness,envSnow:uniforms.snow,envWindowLight:uniforms.windowLight});
    shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nvarying vec3 vEnvWorld;').replace('#include <begin_vertex>','#include <begin_vertex>\nvEnvWorld=(modelMatrix*vec4(transformed,1.0)).xyz;');
    shader.fragmentShader=shader.fragmentShader.replace('#include <common>',`#include <common>\nvarying vec3 vEnvWorld;\nuniform float envDaylight;\nuniform float envNight;\nuniform float envWetness;\nuniform float envSnow;\nuniform float envWindowLight;`).replace('#include <dithering_fragment>',`
      float envSnowMask=clamp(envSnow*${snowFactor.toFixed(2)},0.0,1.0);
      gl_FragColor.rgb=mix(gl_FragColor.rgb,vec3(0.90,0.93,0.95),envSnowMask);
      gl_FragColor.rgb*=1.0-envWetness*${(wetFactor*.22).toFixed(3)};
      ${surface==='wall'?`float envFloor=step(0.18,fract((vEnvWorld.y+0.35)/3.05))*step(fract((vEnvWorld.y+0.35)/3.05),0.72);float envBay=step(0.22,fract((vEnvWorld.x+vEnvWorld.z*1.37)/3.4))*step(fract((vEnvWorld.x+vEnvWorld.z*1.37)/3.4),0.72);float envHash=fract(sin(dot(floor(vEnvWorld.xz/3.4),vec2(12.9898,78.233)))*43758.5453);float envWindow=envFloor*envBay*step(envHash,envWindowLight);gl_FragColor.rgb+=vec3(1.0,.66,.28)*envWindow*envNight*1.5;`:''}
      #include <dithering_fragment>`);
  };
  material.customProgramCacheKey=()=>`environment-${surface}-v1`;
  return material;
}

function particleTexture(kind:'rain'|'snow'){
  const canvas=document.createElement('canvas');canvas.width=16;canvas.height=64;const context=canvas.getContext('2d')!;
  const gradient=context.createLinearGradient(8,0,8,64);if(kind==='rain'){gradient.addColorStop(0,'rgba(210,230,255,0)');gradient.addColorStop(.35,'rgba(210,230,255,.8)');gradient.addColorStop(1,'rgba(210,230,255,0)')}else{const radial=context.createRadialGradient(8,32,0,8,32,8);radial.addColorStop(0,'white');radial.addColorStop(1,'rgba(255,255,255,0)');context.fillStyle=radial;context.fillRect(0,0,16,64);return new THREE.CanvasTexture(canvas)}context.fillStyle=gradient;context.fillRect(0,0,16,64);return new THREE.CanvasTexture(canvas)
}

export class EnvironmentRenderer{
  readonly uniforms=createEnvironmentUniforms();readonly sky:THREE.Mesh;readonly rain:THREE.Points;readonly snow:THREE.Points;
  private rainPositions:Float32Array;private snowPositions:Float32Array;private lastState?:EnvironmentState;
  constructor(private scene:THREE.Scene,private camera:THREE.Camera,private renderer:THREE.WebGLRenderer,private sun:THREE.DirectionalLight,private hemisphere:THREE.HemisphereLight){
    const skyMaterial=new THREE.ShaderMaterial({side:THREE.BackSide,depthWrite:false,uniforms:{daylight:this.uniforms.daylight,night:this.uniforms.night,cloud:{value:0},sunset:{value:0}},vertexShader:'varying vec3 vWorld; void main(){vWorld=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',fragmentShader:`varying vec3 vWorld;uniform float daylight;uniform float night;uniform float cloud;uniform float sunset;float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}void main(){float h=normalize(vWorld).y*.5+.5;vec3 nightSky=mix(vec3(.008,.014,.03),vec3(.025,.045,.09),h);vec3 daySky=mix(vec3(.64,.76,.84),vec3(.14,.43,.72),h);vec3 colour=mix(nightSky,daySky,daylight);colour+=vec3(.55,.18,.06)*sunset*(1.0-h)*.7;float stars=step(.9975,hash(floor(vWorld.xz*1.7)))*night*(1.0-cloud);colour+=stars*.42;colour=mix(colour,vec3(.37,.42,.45),cloud*.62);gl_FragColor=vec4(colour,1.0);}`});
    this.sky=new THREE.Mesh(new THREE.SphereGeometry(4500,32,18),skyMaterial);this.sky.frustumCulled=false;scene.add(this.sky);
    [this.rain,this.rainPositions]=this.makeParticles(2400,'rain');[this.snow,this.snowPositions]=this.makeParticles(1500,'snow');scene.add(this.rain,this.snow)
  }
  private makeParticles(count:number,kind:'rain'|'snow'):[THREE.Points,Float32Array]{const positions=new Float32Array(count*3);for(let i=0;i<count;i++){const angle=i*2.3999632297,radius=Math.sqrt((i*.61803398875)%1)*75;positions[i*3]=Math.cos(angle)*radius;positions[i*3+1]=(i*.754877666)%1*55-8;positions[i*3+2]=Math.sin(angle)*radius}const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.BufferAttribute(positions,3));const material=new THREE.PointsMaterial({map:particleTexture(kind),transparent:true,depthWrite:false,size:kind==='rain'?.17:.48,opacity:0,sizeAttenuation:true,blending:THREE.NormalBlending});return [new THREE.Points(geometry,material),positions]}
  update(state:EnvironmentState,dt:number){this.lastState=state;const daylight=state.solar.daylight,night=1-daylight,cloud=state.weather.cloudCover,sunset=Math.max(0,1-Math.abs(state.solar.elevationDeg)/8)*(1-cloud*.6);
    this.uniforms.daylight.value=daylight;this.uniforms.night.value=night;this.uniforms.wetness.value=state.wetness;this.uniforms.snow.value=state.snowCoverage;this.uniforms.windowLight.value=.06+.38*night;this.uniforms.wind.value.set(state.windEastMps,state.windNorthMps);
    const skyMaterial=this.sky.material as THREE.ShaderMaterial;skyMaterial.uniforms.cloud.value=cloud;skyMaterial.uniforms.sunset.value=sunset;this.sky.position.copy(this.camera.position);
    const az=state.solar.azimuthDeg*Math.PI/180,el=state.solar.elevationDeg*Math.PI/180;this.sun.position.set(Math.sin(az)*Math.cos(el)*1200,Math.sin(el)*1200,-Math.cos(az)*Math.cos(el)*1200);this.sun.intensity=Math.max(0,.15+2.5*daylight*(1-cloud*.72));this.sun.color.setRGB(1,.58+.36*daylight,.36+.58*daylight);this.hemisphere.intensity=.12+1.15*daylight*(1-cloud*.25);this.renderer.toneMappingExposure=.52+.58*daylight;
    const fogColour=new THREE.Color().lerpColors(new THREE.Color(0x111827),new THREE.Color(0xa9bec7),daylight).lerp(new THREE.Color(0x778087),cloud*.35);this.scene.fog=new THREE.FogExp2(fogColour,Math.max(.00015,2.7/state.weather.visibilityM));
    this.updateParticles(this.rain,this.rainPositions,state.rainIntensity,dt,state,-55);this.updateParticles(this.snow,this.snowPositions,state.snowIntensity,dt,state,-5)
  }
  private updateParticles(points:THREE.Points,positions:Float32Array,intensity:number,dt:number,state:EnvironmentState,fallSpeed:number){points.visible=intensity>.01;(points.material as THREE.PointsMaterial).opacity=Math.min(.82,intensity*.9);points.position.copy(this.camera.position);const windX=state.windEastMps*dt,windZ=-state.windNorthMps*dt;for(let i=0;i<positions.length;i+=3){positions[i]+=windX;positions[i+1]+=fallSpeed*dt*(.65+(i%17)/34);positions[i+2]+=windZ;if(positions[i+1]<-10){positions[i+1]+=65;positions[i]-=windX*4;positions[i+2]-=windZ*4}if(Math.abs(positions[i])>90)positions[i]*=-.8;if(Math.abs(positions[i+2])>90)positions[i+2]*=-.8}(points.geometry.attributes.position as THREE.BufferAttribute).needsUpdate=true}
  metrics(){return {rainParticles:this.rain.visible?this.rainPositions.length/3:0,snowParticles:this.snow.visible?this.snowPositions.length/3:0,state:this.lastState}}
}
