import {describe,expect,it} from 'vitest';
import {EnvironmentModel,litWindowFraction,solarPosition,weatherPreset,zonedDate} from './environment';

describe('environment model',()=>{
  it('places the summer midday sun high over Zurich',()=>{const sun=solarPosition(new Date('2026-06-21T11:30:00Z'),47.3769,8.5417);expect(sun.elevationDeg).toBeGreaterThan(60);expect(sun.azimuthDeg).toBeGreaterThan(150);expect(sun.azimuthDeg).toBeLessThan(230)});
  it('distinguishes winter night and valid sunrise/sunset',()=>{const noon=solarPosition(new Date('2026-12-21T11:30:00Z'),47.3769,8.5417),night=solarPosition(new Date('2026-12-21T23:00:00Z'),47.3769,8.5417);expect(noon.elevationDeg).toBeGreaterThan(15);expect(noon.elevationDeg).toBeLessThan(25);expect(night.stage).toBe('NIGHT');expect(noon.sunrise.getTime()).toBeLessThan(noon.sunset.getTime())});
  it('accumulates wetness in rain and dries afterwards',()=>{const model=new EnvironmentModel(weatherPreset('rain')),date=new Date('2026-11-01T08:00:00Z');model.update(600,date,47,8,450);expect(model.wetness).toBeGreaterThan(.5);const wet=model.wetness;model.setWeather(weatherPreset('clear'));model.update(3600,date,47,8,450);expect(model.wetness).toBeLessThan(wet)});
  it('turns cold precipitation into elevation-aware snow and melts it',()=>{const model=new EnvironmentModel(weatherPreset('snow')),date=new Date('2026-01-01T12:00:00Z');model.update(900,date,47,8,1200);expect(model.snowCoverage).toBeGreaterThan(.1);model.setWeather({...weatherPreset('clear'),temperatureC:15});model.update(3600,date,47,8,1200);expect(model.snowCoverage).toBeLessThan(.1)});
  it('keeps facade occupancy deterministic and time dependent',()=>{const evening=litWindowFraction('residential',new Date('2026-01-01T19:00:00'),42),day=litWindowFraction('residential',new Date('2026-01-01T12:00:00'),42);expect(evening).toBe(litWindowFraction('residential',new Date('2026-01-01T19:00:00'),42));expect(evening).toBeGreaterThan(day)});
  it('constructs Swiss civil time with daylight-saving offset',()=>expect(zonedDate('2026-08-22',14*3600).toISOString()).toBe('2026-08-22T12:00:00.000Z'));
});
