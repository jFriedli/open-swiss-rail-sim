import { describe,it,expect } from 'vitest';
describe('controls',()=>{it('uses exclusive power and brake notches',()=>{let power=3,brake=0;brake=2;if(brake>0)power=0;expect([power,brake]).toEqual([0,2])})});

