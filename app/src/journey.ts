export type StopDefinition={id:string;name:string;s:number;platformIndex:number;platformStartS:number;platformEndS:number;targetS:number;scheduledArrival:string;scheduledDeparture:string;dwellSeconds:number;locationSource:string;platformSource:string;targetClassification:string};
export type StopStatus='departed'|'pending'|'dwelling'|'completed'|'missed';
export type JourneyEvent={type:'SignalPassed'|'StationApproach'|'StationArrival'|'StationMissed'|'DwellComplete'|'RouteComplete';id:string;s:number;detail?:Record<string,number|string>};
export type SignalDefinition={id:number|string;s:number;tags:Record<string,string>};

const seconds=(clock:string)=>{const [h,m,s]=clock.split(':').map(Number);return h*3600+m*60+s};
export const clock=(value:number)=>{const v=(Math.round(value)%86400+86400)%86400;return [Math.floor(v/3600),Math.floor(v/60)%60,v%60].map(x=>String(x).padStart(2,'0')).join(':')};
export const deltaClock=(value:number)=>`${value>=0?'+':'−'}${String(Math.floor(Math.abs(value)/60)).padStart(2,'0')}:${String(Math.round(Math.abs(value))%60).padStart(2,'0')}`;

export class SignalProgression{
  readonly signals:SignalDefinition[];private passed=new Set<string>();
  constructor(signals:SignalDefinition[]){this.signals=[...signals].sort((a,b)=>a.s-b.s);for(let i=1;i<this.signals.length;i++)if(this.signals[i].s-this.signals[i-1].s<.5)throw Error('duplicate/unsorted signals')}
  advance(previousS:number,currentS:number){const events:JourneyEvent[]=[];if(currentS<previousS)return events;for(const signal of this.signals)if(signal.s>previousS&&signal.s<=currentS&&!this.passed.has(String(signal.id))){this.passed.add(String(signal.id));events.push({type:'SignalPassed',id:String(signal.id),s:signal.s,detail:{provenance:signal.tags.provenance??'UNKNOWN'}})}return events}
  next(s:number){return this.signals.find(signal=>signal.s>s+2)}
  isPassed(id:number|string){return this.passed.has(String(id))}
}

export class JourneyState{
  readonly stops:StopDefinition[];readonly statuses:StopStatus[];readonly events:JourneyEvent[]=[];currentIndex=1;elapsed=0;dwellRemaining=0;completed=false;score=0;lastStationScore=0;lastStopError=0;lastScheduleDelta=0;private approached=new Set<string>();
  constructor(stops:StopDefinition[],readonly startClock:number){if(stops.length<2)throw Error('journey requires start and destination');this.stops=stops;this.statuses=stops.map((_,i)=>i?'pending':'departed')}
  get nextStop(){return this.stops[this.currentIndex]};get tractionLocked(){return this.dwellRemaining>0||this.completed};get clockSeconds(){return this.startClock+this.elapsed}
  update(_previousS:number,currentS:number,speedKmh:number,dt:number){this.elapsed+=dt;const emitted:JourneyEvent[]=[];let stop=this.nextStop;if(!stop||this.completed)return emitted;
    // Process every crossed platform, so low frame rates and deterministic debug jumps cannot skip events.
    while(stop&&this.statuses[this.currentIndex]!=='dwelling'&&currentS>(this.currentIndex===this.stops.length-1?stop.platformEndS-2:stop.platformEndS+15)){this.statuses[this.currentIndex]='missed';this.lastStationScore=0;emitted.push({type:'StationMissed',id:stop.id,s:currentS});this.currentIndex++;stop=this.nextStop;if(!stop){this.completed=true;emitted.push({type:'RouteComplete',id:this.stops.at(-1)!.id,s:currentS,detail:{missed:'true'}});break}}
    if(!stop||this.completed){this.events.push(...emitted);return emitted}const distance=stop.targetS-currentS;if(distance<=1500&&!this.approached.has(stop.id)){this.approached.add(stop.id);emitted.push({type:'StationApproach',id:stop.id,s:stop.targetS})}
    if(this.statuses[this.currentIndex]==='dwelling'){
      this.dwellRemaining=Math.max(0,this.dwellRemaining-dt);if(this.dwellRemaining===0){this.statuses[this.currentIndex]='completed';emitted.push({type:'DwellComplete',id:stop.id,s:currentS});this.currentIndex++;if(this.currentIndex>=this.stops.length){this.completed=true;emitted.push({type:'RouteComplete',id:stop.id,s:currentS})}}
    }else if(Math.abs(currentS-stop.targetS)<=10&&speedKmh<.5){
      this.lastStopError=currentS-stop.targetS;this.lastScheduleDelta=this.clockSeconds-seconds(stop.scheduledArrival);this.lastStationScore=Math.max(0,Math.round(1000-Math.abs(this.lastStopError)*20-Math.abs(this.lastScheduleDelta)*1.5));this.score+=this.lastStationScore;this.statuses[this.currentIndex]='dwelling';this.dwellRemaining=stop.dwellSeconds;emitted.push({type:'StationArrival',id:stop.id,s:currentS,detail:{stoppingErrorM:this.lastStopError,scheduleDeltaS:this.lastScheduleDelta,score:this.lastStationScore}})}
    this.events.push(...emitted);return emitted
  }
}

export function interpolateGeo(points:{s:number;lat:number;lon:number}[],s:number){let i=0;while(i<points.length-2&&points[i+1].s<s)i++;const a=points[i],b=points[Math.min(points.length-1,i+1)],t=b.s===a.s?0:Math.max(0,Math.min(1,(s-a.s)/(b.s-a.s)));return {lat:a.lat+(b.lat-a.lat)*t,lon:a.lon+(b.lon-a.lon)*t}}
export const parseClock=seconds;
