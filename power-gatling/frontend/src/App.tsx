import React, { useState } from 'react'
import { Layout, Menu, Typography, theme } from 'antd'
import {
  ThunderboltOutlined,
  PlayCircleOutlined,
  DashboardOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import Scenarios from './pages/Scenarios'
import Executions from './pages/Executions'
import SystemStatus from './pages/SystemStatus'
import './App.css'

const { Header, Content, Footer } = Layout

const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState('scenarios')
  const { token } = theme.useToken()

  const renderContent = () => {
    switch (currentTab) {
      case 'scenarios': return <Scenarios />
      case 'executions': return <Executions />
      case 'system': return <SystemStatus />
      default: return <Scenarios />
    }
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', padding: '0 24px' }}>
        <div className="logo">
          <div className="logo-icon">LF</div>
          <span>LoadForge 压测平台</span>
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[currentTab]}
          onClick={(e) => setCurrentTab(e.key)}
          style={{ flex: 1, marginLeft: 40 }}
          items={[
            { key: 'scenarios', icon: <ThunderboltOutlined />, label: '压测场景' },
            { key: 'executions', icon: <PlayCircleOutlined />, label: '压测执行' },
            { key: 'system', icon: <SettingOutlined />, label: '系统状态' },
          ]}
        />
      </Header>
      <Content style={{ background: token.colorBgLayout }}>
        <div className="site-layout-content">
          {renderContent()}
        </div>
      </Content>
      <Footer style={{ textAlign: 'center', color: '#999' }}>
        LoadForge 压测平台 PoC v1.0
      </Footer>
    </Layout>
  )
}

export default App
