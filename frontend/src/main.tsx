import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import App from './App'
import { harvestFlowTheme } from './theme/flow-design-theme'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider theme={harvestFlowTheme}>
      <App />
    </ConfigProvider>
  </React.StrictMode>,
)
