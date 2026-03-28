import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, act, cleanup } from '@testing-library/react'
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

  it('starts in loading state when enabled', () => {
    vi.spyOn(api, 'get').mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useHealthCheck(true))
    expect(result.current.loading).toBe(true)
    expect(result.current.python).toEqual({ ok: false, message: '检查中...' })
    expect(result.current.cookie).toEqual({ ok: false, message: '检查中...' })
    expect(result.current.ai).toEqual({ ok: false, message: '检查中...' })
    expect(result.current.xgj).toEqual({ ok: false, message: '检查中...' })
  })

  it('calls refresh() triggers re-fetch', async () => {
    const spy = vi.spyOn(api, 'get').mockResolvedValue({
      data: {
        services: {
          python: { ok: true, message: 'OK' },
        },
        xgj: { ok: true, message: 'OK' },
        cookie: { ok: true, message: 'OK' },
        ai: { ok: true, message: 'OK' },
      },
    })
    const { result } = renderHook(() => useHealthCheck())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
    expect(spy).toHaveBeenCalledTimes(1)

    spy.mockResolvedValue({
      data: {
        services: {
          python: { ok: false, message: 'Down' },
        },
        xgj: { ok: false, message: 'Down' },
        cookie: { ok: false, message: 'Down' },
        ai: { ok: false, message: 'Down' },
      },
    })

    await act(async () => {
      await result.current.refresh()
    })

    expect(spy).toHaveBeenCalledTimes(2)
    expect(result.current.python.ok).toBe(false)
    expect(result.current.python.message).toBe('Down')
  })

  it('handles error gracefully', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.spyOn(api, 'get').mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useHealthCheck())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.python).toEqual({ ok: false, message: '不可达' })
    expect(result.current.xgj).toEqual({ ok: false, message: '未知' })
    expect(result.current.cookie).toEqual({ ok: false, message: '后端不可达' })
    expect(result.current.ai).toEqual({ ok: false, message: '后端不可达' })

    consoleError.mockRestore()
  })
})
