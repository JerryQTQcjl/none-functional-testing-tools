import React, { useEffect, useState } from 'react'
import { Card, Col, Row, Statistic, Table, Tag, Button, Typography, Spin, message } from 'antd'
import {
  CheckCircleOutlined, CloseCircleOutlined, ReloadOutlined,
  CloudServerOutlined, ThunderboltOutlined,
} from '@ant-design/icons'
import { getSystemStatus, type SystemStatus } from '../api/system'

const SystemStatusPage: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchStatus = async () => {
    setLoading(true)
    try {
      const data = await getSystemStatus()
      setStatus(data)
    } catch (e) { message.error('Failed to load system status') }
    setLoading(false)
  }

  useEffect(() => { fetchStatus() }, [])

  const columns = [
    { title: 'Worker ID', dataIndex: 'worker_id', key: 'worker_id' },
    {
      title: 'Status', dataIndex: 'status', key: 'status',
      render: (s: string) => <Tag color={s === 'running' ? 'green' : s === 'idle' ? 'blue' : 'default'}>{s}</Tag>,
    },
    { title: 'Execution', dataIndex: 'execution_id', key: 'execution_id', render: (v: string) => v || '-' },
    { title: 'Last Heartbeat', dataIndex: 'last_heartbeat', key: 'last_heartbeat' },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>System Status</Typography.Title>
        <Button icon={<ReloadOutlined />} onClick={fetchStatus}>Refresh</Button>
      </div>

      {loading ? <Spin size="large" /> : status && (
        <>
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Redis"
                  value={status.redis_connected ? 'Connected' : 'Disconnected'}
                  prefix={status.redis_connected ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                  valueStyle={{ color: status.redis_connected ? '#3f8600' : '#cf1322' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic title="Active Workers" value={status.active_workers} prefix={<CloudServerOutlined />} />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic title="Registered Workers" value={status.registered_workers} prefix={<CloudServerOutlined />} />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic title="Active Executions" value={status.active_executions} prefix={<ThunderboltOutlined />} />
              </Card>
            </Col>
          </Row>

          <Card title="Workers">
            <Table
              columns={columns}
              dataSource={status.workers || []}
              rowKey="worker_id"
              pagination={false}
              size="small"
            />
          </Card>
        </>
      )}
    </div>
  )
}

export default SystemStatusPage
