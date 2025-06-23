import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './polyfills/crypto-polyfill.js'  // Полифилл для crypto.randomUUID
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
