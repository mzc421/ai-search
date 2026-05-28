import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import './style.css'
import 'highlight.js/styles/github.css'
import App from './App.vue'
import Home from './pages/Home.vue'
import Search from './pages/Search.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/search', component: Search }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)
app.use(router)
app.mount('#app')
