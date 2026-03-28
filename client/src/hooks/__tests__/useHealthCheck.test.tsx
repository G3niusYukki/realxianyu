import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, cleanup } from '@testing-library/react'
import { api } from '../../api/index'
import useHealthCheck from '../useHealthCheck'

describe('useHealthCheck', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
  })

  it('returns initial loading state', () => {
    const { result } = renderHook(() => useHealthCheck())
    expect(result.current.loading).toBe(true)
    expect(result.current.python).toEqual({ ok: false, message: '检查中...' })
  })

  it('updates state on successful health check', async () => {
    vi.spyOn(api, 'get').mockResolvedValue({
      data: {
        services: {
          python: { ok: true, message: 'OK' },
        },
        xgj: { ok: true, message: 'OK' },
        cookie: { ok: false, message: 'Invalid' },
        ai: { ok: false, message: 'Invalid' },
      },
    })
    const { result } = renderHook(() => useHealthCheck())
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
    expect(result.current.python.ok).toBe(true)
    expect(result.current.cookie.ok).toBe(false)
  })

  it('updates state on API error', async () => {
    vi.spyOn(api, 'get').mockRejectedValue(new Error('Network error'))
    const { result } = renderHook(() => useHealthCheck())
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
    expect(result.current.python.message).toBe('不可达')
  })

  it('returns a refresh function', () => {
    const { result } = renderHook(() => useHealthCheck())
    expect(typeof result.current.refresh).toBe('function')
  })
})
