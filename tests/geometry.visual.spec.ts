import {test,expect} from '@playwright/test';

test.skip(!process.env.CAPTURE_GEOMETRY,'manual geometry capture');
for(const s of [0,1000,6700])for(const camera of ['cab','chase'])test(`geometry s=${s} ${camera}`,async({page})=>{
  const errors:string[]=[];page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
  await page.goto(`./?debug=1&s=${s}&camera=${camera}`);await expect(page.locator('body')).toHaveAttribute('data-building-tiles',/[1-4]/,{timeout:20000});await page.waitForTimeout(500);
  await page.screenshot({path:`test-results/geometry-${s}-${camera}.png`});
  await expect(page.locator('#world canvas')).toBeVisible();expect(errors).toEqual([]);
});
