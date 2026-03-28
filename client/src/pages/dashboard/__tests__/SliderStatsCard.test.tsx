import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import SliderStatsCard from '../SliderStatsCard'

vi.mock('../../../api/dashboard', () => ({
  getSliderStats: vi.fn(),
}))

import { getSliderStats } from '../../../api/dashboard'

describe('SliderStatsCard', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns null when there is no data (handles no-data state)', async () => {
    vi.mocked(getSliderStats).mockResolvedValue({
      data: {
        ok: true,
        total_triggers: 0,
        total_attempts: 0,
        passed: 0,
        failed: 0,
        success_rate: 0,
        nc_attempts: 0,
        nc_passed: 0,
        nc_success_rate: 0,
        puzzle_attempts: 0,
        puzzle_passed: 0,
        puzzle_success_rate: 0,
        avg_cookie_ttl_seconds: null,
        screenshots: [],
      },
    } as any)

    const { container } = render(<SliderStatsCard />)

    await waitFor(() => {
      expect(getSliderStats).toHaveBeenCalled()
    })

    // Component returns null when total_triggers is 0
    expect(container.innerHTML).toBe('')
  })

  it('returns null when API call fails', async () => {
    vi.mocked(getSliderStats).mockRejectedValue(new Error('Network error'))

    const { container } = render(<SliderStatsCard />)

    await waitFor(() => {
      expect(getSliderStats).toHaveBeenCalled()
    })

    expect(container.innerHTML).toBe('')
  })

  it('renders data when available', async () => {
    vi.mocked(getSliderStats).mockResolvedValue({
      data: {
        ok: true,
        total_triggers: 10,
        total_attempts: 12,
        passed: 8,
        failed: 4,
        success_rate: 75,
        nc_attempts: 8,
        nc_passed: 6,
        nc_success_rate: 75,
        puzzle_attempts: 4,
        puzzle_passed: 2,
        puzzle_success_rate: 50,
        avg_cookie_ttl_seconds: 7200,
        screenshots: [],
      },
    } as any)

    render(<SliderStatsCard />)

    // Wait for component to render by checking for the header
    await waitFor(() => {
      expect(screen.getByText('滑块验证')).toBeInTheDocument()
    })

    // Check that success_rate stats are rendered
    // React renders {stats.success_rate}% inside a div, so text is "75%"
    expect(screen.getByText('总成功率')).toBeInTheDocument()
    expect(screen.getByText('触发次数')).toBeInTheDocument()
    expect(screen.getByText('Cookie均寿')).toBeInTheDocument()

    // Check total triggers displayed
    expect(screen.getByText('10')).toBeInTheDocument()

    // Check Cookie TTL displayed (7200s = 2.0h)
    expect(screen.getByText('2.0h')).toBeInTheDocument()

    // Check NC slider section
    expect(screen.getByText('NC 滑块')).toBeInTheDocument()

    // Check puzzle slider section
    expect(screen.getByText('拼图滑块')).toBeInTheDocument()
  })

  it('displays Cookie TTL in minutes when under 1 hour', async () => {
    vi.mocked(getSliderStats).mockResolvedValue({
      data: {
        ok: true,
        total_triggers: 5,
        total_attempts: 5,
        passed: 5,
        failed: 0,
        success_rate: 100,
        nc_attempts: 5,
        nc_passed: 5,
        nc_success_rate: 100,
        puzzle_attempts: 0,
        puzzle_passed: 0,
        puzzle_success_rate: 0,
        avg_cookie_ttl_seconds: 1800,
        screenshots: [],
      },
    } as any)

    render(<SliderStatsCard />)

    await waitFor(() => {
      // 1800s = 30min
      expect(screen.getByText('30min')).toBeInTheDocument()
    })
  })
})
