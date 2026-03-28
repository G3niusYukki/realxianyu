import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import PublishQueueCard from '../PublishQueueCard'

vi.mock('../../../api/listing', () => ({
  getPublishQueue: vi.fn(),
}))

import { getPublishQueue } from '../../../api/listing'

function renderWithRouter(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

describe('PublishQueueCard', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders after data loads and shows count of pending items', async () => {
    vi.mocked(getPublishQueue).mockResolvedValue({
      data: {
        ok: true,
        items: [
          { status: 'draft', id: 1 },
          { status: 'ready', id: 2 },
          { status: 'published', id: 3 },
        ],
      },
    } as any)

    renderWithRouter(<PublishQueueCard />)

    // Should show the card title
    expect(screen.getByText('今日待发布')).toBeInTheDocument()

    // After loading, should show count of draft + ready items (2)
    await waitFor(() => {
      expect(screen.getByText('2 条')).toBeInTheDocument()
    })
  })

  it('handles loading state gracefully (no crash while fetch is pending)', async () => {
    let resolvePromise: (v: any) => void
    const pendingPromise = new Promise(resolve => {
      resolvePromise = resolve
    })
    vi.mocked(getPublishQueue).mockReturnValue(pendingPromise as any)

    renderWithRouter(<PublishQueueCard />)

    // Card title should be visible immediately
    expect(screen.getByText('今日待发布')).toBeInTheDocument()

    // Count badge should NOT be present while loading
    expect(screen.queryByText(/条/)).not.toBeInTheDocument()

    // Resolve to avoid hanging promise
    resolvePromise!({ data: { ok: true, items: [] } })
  })

  it('does not show count when API returns no pending items', async () => {
    vi.mocked(getPublishQueue).mockResolvedValue({
      data: {
        ok: true,
        items: [
          { status: 'published', id: 1 },
          { status: 'published', id: 2 },
        ],
      },
    } as any)

    renderWithRouter(<PublishQueueCard />)

    await waitFor(() => {
      expect(getPublishQueue).toHaveBeenCalled()
    })

    expect(screen.getByText('今日待发布')).toBeInTheDocument()
    expect(screen.queryByText(/条/)).not.toBeInTheDocument()
  })

  it('handles API error without crashing', async () => {
    vi.mocked(getPublishQueue).mockRejectedValue(new Error('Network error'))

    renderWithRouter(<PublishQueueCard />)

    // Component should still render the title
    expect(screen.getByText('今日待发布')).toBeInTheDocument()

    // No count badge
    expect(screen.queryByText(/条/)).not.toBeInTheDocument()
  })
})
