import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { registerSW, initNetworkMonitor } from './utils/sw'

// 初始化应用
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

// 延迟注册 Service Worker，避免阻塞渲染
setTimeout(() => {
  registerSW()
  initNetworkMonitor()
}, 1000)
