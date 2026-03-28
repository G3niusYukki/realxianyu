import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import XgjControlPanel from '../XgjControlPanel'

vi.mock('../../../api/index', () => ({
  api: {
    post: vi.fn(),
  },
}))

import { api } from '../../../api/index'

describe('XgjControlPanel', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.clearAllMocks()
  })

  it('renders form inputs', () => {
    render(<XgjControlPanel />)

    expect(screen.getByPlaceholderText('填写 AppKey')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('填写 AppSecret')).toBeInTheDocument()
    expect(screen.getByText('自动改价')).toBeInTheDocument()
    expect(screen.getByText('支付后自动发货')).toBeInTheDocument()
    expect(screen.getByText('测试连接')).toBeInTheDocument()
    expect(screen.getByText('保存配置')).toBeInTheDocument()
  })

  it('test connection button triggers API call', async () => {
    vi.mocked(api.post).mockResolvedValue({
      data: { ok: true, message: '连接成功' },
    })

    render(<XgjControlPanel />)

    // Fill in credentials
    fireEvent.change(screen.getByPlaceholderText('填写 AppKey'), {
      target: { value: 'test-key' },
    })
    fireEvent.change(screen.getByPlaceholderText('填写 AppSecret'), {
      target: { value: 'test-secret' },
    })

    // Click test button
    fireEvent.click(screen.getByText('测试连接'))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/xgj/test-connection', {
        app_key: 'test-key',
        app_secret: 'test-secret',
        mode: 'xianguanjia',
      })
    })

    // Should show "已连接" on success
    await waitFor(() => {
      expect(screen.getByText('已连接')).toBeInTheDocument()
    })
  })

  it('save button triggers API call', async () => {
    vi.mocked(api.post).mockResolvedValue({
      data: { success: true },
    })

    render(<XgjControlPanel />)

    fireEvent.change(screen.getByPlaceholderText('填写 AppKey'), {
      target: { value: 'key-123' },
    })
    fireEvent.change(screen.getByPlaceholderText('填写 AppSecret'), {
      target: { value: 'secret-456' },
    })

    fireEvent.click(screen.getByText('保存配置'))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/xgj/settings', {
        app_key: 'key-123',
        app_secret: 'secret-456',
        auto_price_enabled: false,
        auto_ship_enabled: false,
      })
    })
  })

  it('shows loading text on test button while testing', async () => {
    let resolvePromise: (v: any) => void
    vi.mocked(api.post).mockReturnValue(new Promise(resolve => {
      resolvePromise = resolve
    }) as any)

    render(<XgjControlPanel />)

    fireEvent.change(screen.getByPlaceholderText('填写 AppKey'), {
      target: { value: 'k' },
    })
    fireEvent.change(screen.getByPlaceholderText('填写 AppSecret'), {
      target: { value: 's' },
    })

    fireEvent.click(screen.getByText('测试连接'))

    await waitFor(() => {
      expect(screen.getByText('测试中...')).toBeInTheDocument()
    })

    resolvePromise!({ data: { ok: true, message: 'OK' } })
  })

  it('shows loading text on save button while saving', async () => {
    let resolvePromise: (v: any) => void
    vi.mocked(api.post).mockReturnValue(new Promise(resolve => {
      resolvePromise = resolve
    }) as any)

    render(<XgjControlPanel />)

    fireEvent.click(screen.getByText('保存配置'))

    await waitFor(() => {
      expect(screen.getByText('保存中...')).toBeInTheDocument()
    })

    resolvePromise!({ data: { success: true } })
  })

  it('handles test connection failure', async () => {
    vi.mocked(api.post).mockResolvedValue({
      data: { ok: false, message: '认证失败' },
    })

    render(<XgjControlPanel />)

    fireEvent.change(screen.getByPlaceholderText('填写 AppKey'), {
      target: { value: 'bad-key' },
    })
    fireEvent.change(screen.getByPlaceholderText('填写 AppSecret'), {
      target: { value: 'bad-secret' },
    })

    fireEvent.click(screen.getByText('测试连接'))

    await waitFor(() => {
      expect(screen.getByText('连接失败')).toBeInTheDocument()
    })
  })

  it('handles test connection network error', async () => {
    vi.mocked(api.post).mockRejectedValue(new Error('Network error'))

    render(<XgjControlPanel />)

    fireEvent.change(screen.getByPlaceholderText('填写 AppKey'), {
      target: { value: 'k' },
    })
    fireEvent.change(screen.getByPlaceholderText('填写 AppSecret'), {
      target: { value: 's' },
    })

    fireEvent.click(screen.getByText('测试连接'))

    await waitFor(() => {
      expect(screen.getByText('连接失败')).toBeInTheDocument()
    })
  })

  it('shows initial connection status as unconfigured', () => {
    render(<XgjControlPanel />)
    expect(screen.getByText('未配置')).toBeInTheDocument()
  })
})
