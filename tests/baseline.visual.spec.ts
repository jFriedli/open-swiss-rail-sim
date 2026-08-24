import {test} from '@playwright/test';

test.skip(!process.env.CAPTURE_BASELINE,'manual deployed baseline capture');
test('captures deployed route diagnostics',async({page})=>{
  await page.clock.install();
  await page.goto('./');
  await page.getByRole('button',{name:'DRIVE'}).click();
  await page.screenshot({path:'test-results/baseline-cab.png'});
  await page.keyboard.press('c');
  await page.clock.runFor(1500);
  await page.screenshot({path:'test-results/baseline-chase.png'});
  for(let i=0;i<5;i++)await page.keyboard.press('w');
  await page.clock.runFor(75000);
  await page.screenshot({path:'test-results/baseline-around-1km.png'});
  await page.clock.runFor(180000);
  await page.screenshot({path:'test-results/baseline-mid-route.png'});
});
