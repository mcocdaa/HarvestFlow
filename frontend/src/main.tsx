import React from 'react'
import ReactDOM from 'react-dom/client'
import '@ant-design/v5-patch-for-react-19'
import { App as AntdApp } from 'antd'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import 'dayjs/locale/en'
import 'antd/dist/reset.css'
import App from './App'
import { LanguageProvider, getStoredLocale } from './i18n'
import './index.css'
import './styles/components.css'

dayjs.locale(getStoredLocale() === 'zh' ? 'zh-cn' : 'en')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <LanguageProvider>
      <AntdApp>
        <App />
      </AntdApp>
    </LanguageProvider>
  </React.StrictMode>,
)
