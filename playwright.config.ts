import {defineConfig} from '@playwright/test';
const deployed=process.env.PLAYWRIGHT_BASE_URL;
export default defineConfig({testDir:'./tests',webServer:deployed?undefined:{command:'npm run preview -- --host 127.0.0.1 --port 4178',port:4178,reuseExistingServer:false},use:{baseURL:deployed??'http://127.0.0.1:4178'},reporter:'line'});
