import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'mapbox-gl/dist/mapbox-gl.css'
import axios from 'axios'

// Configure axios to use the API server
axios.defaults.baseURL = 'http://localhost:5005'

const app = createApp(App)
app.use(ElementPlus)
app.mount('#app') 