import { defineConfig } from 'vite';
export default defineConfig({server:{watch:{usePolling:true,interval:500},proxy:{'/api':'http://127.0.0.1:8041'}},preview:{proxy:{'/api':'http://127.0.0.1:8041'}}});
