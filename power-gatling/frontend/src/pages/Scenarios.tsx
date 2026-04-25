import React, { useEffect, useState } from 'react'
import {
  Button, Card, Col, Row, Tag, Space, Modal, Form, Input, Select,
  InputNumber, message, Popconfirm, Empty, Spin, Typography,
} from 'antd'
import {
  PlusOutlined, DeleteOutlined, EditOutlined, CodeOutlined, PlayCircleOutlined,
} from '@ant-design/icons'
import { listScenarios, createScenario, deleteScenario, getScenarioCode, type Scenario } from '../api/scenarios'
import { startExecution } from '../api/executions'

const { TextArea } = Input
const { Text } = Typography

const Scenarios: React.FC = () => {
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [codeModalOpen, setCodeModalOpen] = useState(false)
  const [codeContent, setCodeContent] = useState('')
  const [form] = Form.useForm()

  const fetchScenarios = async () => {
    setLoading(true)
    try {
      const data = await listScenarios()
      setScenarios(data || [])
    } catch (e) { message.error('Failed to load scenarios') }
    setLoading(false)
  }

  useEffect(() => { fetchScenarios() }, [])

  const handleCreate = async (values: any) => {
    try {
      await createScenario(values)
      message.success('Scenario created')
      setModalOpen(false)
      form.resetFields()
      fetchScenarios()
    } catch (e) { message.error('Failed to create scenario') }
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteScenario(id)
      message.success('Scenario deleted')
      fetchScenarios()
    } catch (e) { message.error('Failed to delete') }
  }

  const handleViewCode = async (id: string) => {
    try {
      const data = await getScenarioCode(id)
      setCodeContent(data?.code || '')
      setCodeModalOpen(true)
    } catch (e) { message.error('Failed to get code') }
  }

  const handleRun = async (id: string) => {
    try {
      await startExecution(id)
      message.success('Test execution started')
    } catch (e) { message.error('Failed to start execution') }
  }

  const methodColors: Record<string, string> = {
    GET: 'green', POST: 'blue', PUT: 'orange', DELETE: 'red',
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Typography.Title level={4} style={{ margin: 0 }}>压测场景管理</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          新建场景
        </Button>
      </div>

      {loading ? <Spin size="large" /> : scenarios.length === 0 ? (
        <Empty description="No scenarios yet. Create one to get started." />
      ) : (
        <Row gutter={[16, 16]}>
          {scenarios.map((s) => (
            <Col xs={24} sm={12} lg={8} key={s.id}>
              <Card
                title={
                  <Space>
                    <Tag color={methodColors[s.method] || 'default'}>{s.method}</Tag>
                    <Text strong>{s.name}</Text>
                  </Space>
                }
                extra={
                  <Space>
                    <Button size="small" icon={<CodeOutlined />} onClick={() => handleViewCode(s.id)} />
                    <Popconfirm title="Delete?" onConfirm={() => handleDelete(s.id)}>
                      <Button size="small" danger icon={<DeleteOutlined />} />
                    </Popconfirm>
                  </Space>
                }
                actions={[
                  <Button type="primary" icon={<PlayCircleOutlined />} onClick={() => handleRun(s.id)}>
                    Run Test
                  </Button>,
                ]}
              >
                <p><Text type="secondary">URL:</Text> {s.target_url}</p>
                <p><Text type="secondary">Users:</Text> {s.concurrent_users} | <Text type="secondary">Duration:</Text> {s.sustained_duration}s | <Text type="secondary">Workers:</Text> {s.workers}</p>
                {s.description && <p style={{ color: '#888', fontSize: 12 }}>{s.description}</p>}
                {s.tags?.length > 0 && (
                  <div>{s.tags.map((t, i) => <Tag key={i}>{t}</Tag>)}</div>
                )}
              </Card>
            </Col>
          ))}
        </Row>
      )}

      <Modal
        title="新建压测场景"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        width={640}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="场景名称" rules={[{ required: true }]}>
            <Input placeholder="e.g. E-commerce Browse Test" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={2} />
          </Form.Item>
          <Row gutter={16}>
            <Col span={16}>
              <Form.Item name="target_url" label="目标 URL" rules={[{ required: true }]}>
                <Input placeholder="http://demo-target:8080/api/products" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="method" label="HTTP 方法" initialValue="GET">
                <Select options={[
                  { value: 'GET', label: 'GET' },
                  { value: 'POST', label: 'POST' },
                  { value: 'PUT', label: 'PUT' },
                  { value: 'DELETE', label: 'DELETE' },
                ]} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="body" label="Request Body (JSON)">
            <TextArea rows={3} placeholder='{"key": "value"}' />
          </Form.Item>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="concurrent_users" label="并发用户数" initialValue={100}>
                <InputNumber min={1} max={100000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="ramp_up_duration" label="Ramp-up (秒)" initialValue={10}>
                <InputNumber min={1} max={3600} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="sustained_duration" label="持续时长 (秒)" initialValue={60}>
                <InputNumber min={1} max={7200} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="workers" label="Worker 数量" initialValue={1}>
            <InputNumber min={1} max={50} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="tags" label="标签">
            <Select mode="tags" placeholder="Type and press Enter" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="Gatling Simulation Code"
        open={codeModalOpen}
        onCancel={() => setCodeModalOpen(false)}
        width={720}
        footer={null}
      >
        <pre style={{ background: '#1e1e1e', color: '#d4d4d4', padding: 16, borderRadius: 8, overflow: 'auto', maxHeight: 500, fontSize: 13 }}>
          {codeContent}
        </pre>
      </Modal>
    </div>
  )
}

export default Scenarios
