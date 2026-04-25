import React, { useEffect, useState, useRef, useCallback } from 'react'
import {
  Button, Card, Col, Row, Statistic, Table, Tag, Space, Typography, Select,
  message, Spin, Empty,
} from 'antd'
import {
  PlayCircleOutlined, StopOutlined, ReloadOutlined,
  ArrowUpOutlined, ArrowDownOutlined,
} from '@ant-design/icons'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, AreaChart, Area,
} from 'recharts'
import { listScenarios, type Scenario } from '../api/scenarios'
import { listExecutions, startExecution, stopExecution, getExecution, type Execution, type MetricPoint } from '../api/executions'

const { Text } = Typography

const Executions: React.FC = () => {
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [executions, setExecutions] = useState<Execution[]>([])
  const [selectedScenario, setSelectedScenario] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [activeExecution, setActiveExecution] = useState<Execution | null>(null)
  const [metrics, setMetrics] = useState<MetricPoint[]>([])
  const wsRef = useRef<WebSocket | null>(null)

  const fetchData = async () => {
    setLoading(true)
    try {
      const [sc, ex] = await Promise.all([listScenarios(), listExecutions()])
      setScenarios(sc || [])
      setExecutions(ex || [])
      const running = (ex || []).find((e: Execution) => e.status === 'running')
      if (running) {
        setActiveExecution(running)
        connectWS(running.id)
      }
    } catch (e) { message.error('Failed to load data') }
    setLoading(false)
  }

  useEffect(() => { fetchData() }, [])

  const connectWS = (executionId: string) => {
    if (wsRef.current) wsRef.current.close()
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/api/executions/${executionId}/realtime`)
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.event === 'execution_end') {
          setActiveExecution(null)
          ws.close()
          fetchData()
          return
        }
        setMetrics(prev => [...prev.slice(-120), data])
        if (activeExecution) {
          getExecution(executionId).then(ex => { if (ex) setActiveExecution(ex) })
        }
      } catch (err) { /* ignore */ }
    }
    wsRef.current = ws
  }

  const handleStart = async () => {
    if (!selectedScenario) { message.warning('Select a scenario first'); return }
    try {
      const ex = await startExecution(selectedScenario)
      message.success('Test started')
      setActiveExecution(ex)
      setMetrics([])
      connectWS(ex.id)
      fetchData()
    } catch (e) { message.error('Failed to start') }
  }

  const handleStop = async () => {
    if (!activeExecution) return
    try {
      await stopExecution(activeExecution.id)
      message.success('Test stopped')
      if (wsRef.current) wsRef.current.close()
      setActiveExecution(null)
      fetchData()
    } catch (e) { message.error('Failed to stop') }
  }

  const statusColor: Record<string, string> = {
    running: 'green', completed: 'blue', failed: 'red', stopped: 'orange', pending: 'default',
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', render: (id: string) => id.slice(0, 8) },
    { title: 'Scenario', dataIndex: 'scenario_name', key: 'name' },
    {
      title: 'Status', dataIndex: 'status', key: 'status',
      render: (s: string) => <Tag color={statusColor[s]}>{s.toUpperCase()}</Tag>,
    },
    { title: 'RPS', dataIndex: 'rps', key: 'rps', render: (v: number) => v?.toFixed(1) },
    { title: 'Mean RT (ms)', dataIndex: 'mean_rt', key: 'mean_rt', render: (v: number) => v?.toFixed(1) },
    { title: 'P99 RT (ms)', dataIndex: 'p99_rt', key: 'p99_rt', render: (v: number) => v?.toFixed(1) },
    { title: 'Errors', dataIndex: 'error_rate', key: 'error_rate', render: (v: number) => `${((v || 0) * 100).toFixed(2)}%` },
    { title: 'Requests', dataIndex: 'total_requests', key: 'total_requests' },
  ]

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Typography.Title level={4} style={{ marginBottom: 16 }}>Quick Start</Typography.Title>
        <Space>
          <Select
            style={{ width: 300 }}
            placeholder="Select a scenario"
            value={selectedScenario || undefined}
            onChange={setSelectedScenario}
            options={scenarios.map(s => ({ value: s.id, label: s.name }))}
          />
          <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleStart} disabled={!selectedScenario || !!activeExecution}>
            Start Test
          </Button>
          <Button icon={<ReloadOutlined />} onClick={fetchData}>Refresh</Button>
        </Space>
      </div>

      {activeExecution && (
        <Card title={`Running Test: ${activeExecution.scenario_name || activeExecution.scenario_id?.slice(0, 8)}`}
          extra={<Button danger icon={<StopOutlined />} onClick={handleStop}>Stop</Button>}
          style={{ marginBottom: 24 }}>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={4}><Statistic title="RPS" value={activeExecution.rps?.toFixed(1)} /></Col>
            <Col span={4}><Statistic title="Mean RT (ms)" value={activeExecution.mean_rt?.toFixed(1)} /></Col>
            <Col span={4}><Statistic title="P99 RT (ms)" value={activeExecution.p99_rt?.toFixed(1)} /></Col>
            <Col span={4}><Statistic title="Total Requests" value={activeExecution.total_requests} /></Col>
            <Col span={4}><Statistic title="Error Rate" value={`${((activeExecution.error_rate || 0) * 100).toFixed(2)}%`}
              valueStyle={{ color: (activeExecution.error_rate || 0) > 0.05 ? '#cf1322' : '#3f8600' }} /></Col>
            <Col span={4}><Statistic title="Workers" value={activeExecution.workers} /></Col>
          </Row>

          {metrics.length > 0 && (
            <Row gutter={16}>
              <Col span={12}>
                <Typography.Text strong>RPS Over Time</Typography.Text>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={metrics}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" tick={false} />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="rps" stroke="#1677ff" fill="#1677ff" fillOpacity={0.2} />
                  </AreaChart>
                </ResponsiveContainer>
              </Col>
              <Col span={12}>
                <Typography.Text strong>Response Time (ms)</Typography.Text>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={metrics}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" tick={false} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="p50_rt" stroke="#52c41a" name="P50" dot={false} />
                    <Line type="monotone" dataKey="p90_rt" stroke="#faad14" name="P90" dot={false} />
                    <Line type="monotone" dataKey="p99_rt" stroke="#ff4d4f" name="P99" dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </Col>
            </Row>
          )}
        </Card>
      )}

      <Card title="Execution History">
        <Table
          columns={columns}
          dataSource={executions}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          size="small"
        />
      </Card>
    </div>
  )
}

export default Executions
