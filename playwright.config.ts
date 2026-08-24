import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./tests',webServer:{command:'npm run preview -- --host 127.0.0.1 --port 4178',port:4178,reuseExistingServer:false},use:{baseURL:'http://127.0.0.1:4178'},reporter:'line'});
