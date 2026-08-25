export type WeatherPreset='clear'|'overcast'|'rain'|'heavy-rain'|'fog'|'snow'|'heavy-snow';
export type EnvironmentProvenance='OBSERVED'|'FORECAST'|'HISTORICAL'|'CUSTOM'|'DERIVED'|'SIMULATED_VISUAL';
export type DayStage='DAY'|'GOLDEN_HOUR'|'CIVIL_TWILIGHT'|'NIGHT';

export interface SolarState {azimuthDeg:number;elevationDeg:number;sunrise:Date;sunset:Date;stage:DayStage;daylight:number}
export interface WeatherState {preset:WeatherPreset;temperatureC:number;precipitationMmH:number;cloudCover:number;windSpeedMps:number;windDirectionDeg:number;visibilityM:number;relativeHumidity:number;source:EnvironmentProvenance;sourceTimestamp?:string}
export interface EnvironmentState {datetime:Date;latitude:number;longitude:number;elevationM:number;solar:SolarState;weather:WeatherState;wetness:number;snowCoverage:number;rainIntensity:number;snowIntensity:number;windEastMps:number;windNorthMps:number}

const rad=Math.PI/180,deg=180/Math.PI,clamp=(value:number,min=0,max=1)=>Math.max(min,Math.min(max,value));
const dayOfYear=(date:Date)=>Math.floor((Date.UTC(date.getUTCFullYear(),date.getUTCMonth(),date.getUTCDate())-Date.UTC(date.getUTCFullYear(),0,0))/86400000);

// NOAA fractional-year solar equations. Azimuth is clockwise from geographic north.
export function solarPosition(datetime:Date,latitude:number,longitude:number):SolarState{
  const n=dayOfYear(datetime),minutes=datetime.getUTCHours()*60+datetime.getUTCMinutes()+datetime.getUTCSeconds()/60;
  const gamma=2*Math.PI/365*(n-1+(minutes/60-12)/24);
  const eqtime=229.18*(.000075+.001868*Math.cos(gamma)-.032077*Math.sin(gamma)-.014615*Math.cos(2*gamma)-.040849*Math.sin(2*gamma));
  const decl=.006918-.399912*Math.cos(gamma)+.070257*Math.sin(gamma)-.006758*Math.cos(2*gamma)+.000907*Math.sin(2*gamma)-.002697*Math.cos(3*gamma)+.00148*Math.sin(3*gamma);
  const trueSolar=(minutes+eqtime+4*longitude+1440)%1440,hourAngle=(trueSolar/4-180)*rad,lat=latitude*rad;
  const cosZenith=clamp(Math.sin(lat)*Math.sin(decl)+Math.cos(lat)*Math.cos(decl)*Math.cos(hourAngle),-1,1),zenith=Math.acos(cosZenith),elevation=90-zenith*deg;
  const azimuth=(Math.atan2(Math.sin(hourAngle),Math.cos(hourAngle)*Math.sin(lat)-Math.tan(decl)*Math.cos(lat))*deg+180+360)%360;
  const cosH=(Math.cos(90.833*rad)/(Math.cos(lat)*Math.cos(decl))-Math.tan(lat)*Math.tan(decl));
  const solarNoon=720-4*longitude-eqtime,hourMinutes=Math.acos(clamp(cosH,-1,1))*deg*4;
  const midnight=Date.UTC(datetime.getUTCFullYear(),datetime.getUTCMonth(),datetime.getUTCDate());
  const sunrise=new Date(midnight+(solarNoon-hourMinutes)*60000),sunset=new Date(midnight+(solarNoon+hourMinutes)*60000);
  const stage:DayStage=elevation>=6?'DAY':elevation>=-1?'GOLDEN_HOUR':elevation>=-6?'CIVIL_TWILIGHT':'NIGHT';
  return {azimuthDeg:azimuth,elevationDeg:elevation,sunrise,sunset,stage,daylight:clamp((elevation+8)/20)};
}

const presets:Record<WeatherPreset,Omit<WeatherState,'preset'|'source'>>={
  clear:{temperatureC:18,precipitationMmH:0,cloudCover:.08,windSpeedMps:2,windDirectionDeg:240,visibilityM:30000,relativeHumidity:.48},
  overcast:{temperatureC:12,precipitationMmH:0,cloudCover:.92,windSpeedMps:4,windDirectionDeg:250,visibilityM:14000,relativeHumidity:.76},
  rain:{temperatureC:10,precipitationMmH:2.5,cloudCover:.96,windSpeedMps:6,windDirectionDeg:230,visibilityM:6500,relativeHumidity:.91},
  'heavy-rain':{temperatureC:9,precipitationMmH:12,cloudCover:1,windSpeedMps:11,windDirectionDeg:220,visibilityM:2300,relativeHumidity:.97},
  fog:{temperatureC:5,precipitationMmH:0,cloudCover:1,windSpeedMps:.8,windDirectionDeg:80,visibilityM:650,relativeHumidity:.99},
  snow:{temperatureC:-2,precipitationMmH:1.8,cloudCover:.95,windSpeedMps:4,windDirectionDeg:20,visibilityM:4500,relativeHumidity:.91},
  'heavy-snow':{temperatureC:-5,precipitationMmH:7,cloudCover:1,windSpeedMps:8,windDirectionDeg:10,visibilityM:1200,relativeHumidity:.96}
};

export function weatherPreset(preset:WeatherPreset,source:EnvironmentProvenance='CUSTOM'):WeatherState{return {preset,source,...presets[preset]}}
export function precipitationVisual(mmH:number){return clamp(Math.log1p(Math.max(0,mmH))/Math.log(13))}
export function snowTemperatureAtElevation(temperatureC:number,sampleElevationM:number,referenceElevationM:number){return temperatureC-(sampleElevationM-referenceElevationM)*.0065}

export class EnvironmentModel{
  wetness=0;snowCoverage=0;
  constructor(public weather=weatherPreset('clear')){}
  setWeather(weather:WeatherState){this.weather=weather}
  update(dtSeconds:number,datetime:Date,latitude:number,longitude:number,elevationM:number):EnvironmentState{
    const dt=Math.max(0,Math.min(dtSeconds,3600)),atElevation=snowTemperatureAtElevation(this.weather.temperatureC,elevationM,450);
    const snowing=this.weather.precipitationMmH>0&&atElevation<=1.2,raining=this.weather.precipitationMmH>0&&!snowing;
    this.wetness=clamp(this.wetness+(raining?this.weather.precipitationMmH*.00075:-.000035*(1+Math.max(0,atElevation)/15))*dt);
    const accumulate=snowing?this.weather.precipitationMmH*.00012*dt:0,melt=atElevation>1?atElevation*.000008*dt:0,solarMelt=solarPosition(datetime,latitude,longitude).daylight*Math.max(0,atElevation)*.000002*dt;
    this.snowCoverage=clamp(this.snowCoverage+accumulate-melt-solarMelt);
    const wind=this.weather.windDirectionDeg*rad;
    return {datetime,latitude,longitude,elevationM,solar:solarPosition(datetime,latitude,longitude),weather:this.weather,wetness:this.wetness,snowCoverage:this.snowCoverage,rainIntensity:raining?precipitationVisual(this.weather.precipitationMmH):0,snowIntensity:snowing?precipitationVisual(this.weather.precipitationMmH):0,windEastMps:Math.sin(wind)*this.weather.windSpeedMps,windNorthMps:Math.cos(wind)*this.weather.windSpeedMps};
  }
}

export function litWindowFraction(category:'residential'|'office'|'industrial',datetime:Date,buildingSeed:number){
  const hour=datetime.getHours()+datetime.getMinutes()/60,base=category==='office'?(hour>=7&&hour<20?.28:.035):category==='industrial'?(hour>=5&&hour<23?.16:.04):(hour>=17&&hour<22.5?.38:hour>=22.5||hour<5?.07:.025);
  const stable=((Math.imul(buildingSeed|0,1103515245)+12345)>>>16&255)/255;
  return clamp(base*(.72+.56*stable));
}

export function parseWeatherPreset(value:string|null):WeatherPreset{return value&&value in presets?value as WeatherPreset:'clear'}

export function zonedDate(date:string,seconds:number,timeZone='Europe/Zurich'){
  const [year,month,day]=date.split('-').map(Number),hours=Math.floor(seconds/3600)%24,minutes=Math.floor(seconds/60)%60,secs=Math.floor(seconds)%60;
  const intended=Date.UTC(year,month-1,day,hours,minutes,secs);let candidate=intended;
  for(let i=0;i<2;i++){const parts=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date(candidate)).filter(x=>x.type!=='literal').map(x=>[x.type,Number(x.value)]));const represented=Date.UTC(parts.year,parts.month-1,parts.day,parts.hour,parts.minute,parts.second);candidate+=intended-represented}
  return new Date(candidate);
}
