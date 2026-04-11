import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { WeekSelector } from '../src/components/WeekSelector'
import { WEEK_SELECTOR_LABELS, FINALIZED_INDICATOR } from '../src/constants/week-selector'
import type { MenuPeriod } from '../src/types/domain'

describe('WeekSelector Component', () => {
  const mockPeriods: MenuPeriod[] = [
    {
      period_id: '2026-04-16',
      start_date: '2026-04-16',
      end_date: '2026-04-23',
      display_label: '16/04 - 23/04',
      created_at: '2026-04-16T00:00:00Z',
      finalized_at: null,
    },
    {
      period_id: '2026-04-09',
      start_date: '2026-04-09',
      end_date: '2026-04-16',
      display_label: '09/04 - 16/04',
      created_at: '2026-04-09T00:00:00Z',
      finalized_at: '2026-04-14T10:00:00Z',
    },
  ]

  it('should render with default selection', () => {
    const handleSelect = vi.fn()
    render(
      <WeekSelector
        periods={mockPeriods}
        selectedPeriod={null}
        onSelect={handleSelect}
      />
    )

    expect(screen.getByLabelText('Semaine')).toBeInTheDocument()
    expect(screen.getByRole('combobox')).toHaveValue('current')
  })

  it('should display all periods in dropdown', () => {
    const handleSelect = vi.fn()
    render(
      <WeekSelector
        periods={mockPeriods}
        selectedPeriod={null}
        onSelect={handleSelect}
      />
    )

    expect(screen.getByText(WEEK_SELECTOR_LABELS.currentWeek)).toBeInTheDocument()
    expect(screen.getByText('16/04 - 23/04')).toBeInTheDocument()
    expect(screen.getByText(`09/04 - 16/04${FINALIZED_INDICATOR}`)).toBeInTheDocument()
  })

  it('should call onSelect with null when "current" is selected', () => {
    const handleSelect = vi.fn()
    render(
      <WeekSelector
        periods={mockPeriods}
        selectedPeriod={null}
        onSelect={handleSelect}
      />
    )

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'current' } })

    expect(handleSelect).toHaveBeenCalledWith(null)
  })

  it('should call onSelect with periodId when a period is selected', () => {
    const handleSelect = vi.fn()
    render(
      <WeekSelector
        periods={mockPeriods}
        selectedPeriod={null}
        onSelect={handleSelect}
      />
    )

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: '2026-04-16' } })

    expect(handleSelect).toHaveBeenCalledWith('2026-04-16')
  })

  it('should reflect selected period in dropdown', () => {
    const handleSelect = vi.fn()
    render(
      <WeekSelector
        periods={mockPeriods}
        selectedPeriod="2026-04-09"
        onSelect={handleSelect}
      />
    )

    const select = screen.getByRole('combobox')
    expect(select).toHaveValue('2026-04-09')
  })

  it('should show checkmark for finalized periods', () => {
    const handleSelect = vi.fn()
    render(
      <WeekSelector
        periods={mockPeriods}
        selectedPeriod={null}
        onSelect={handleSelect}
      />
    )

    // Second period is finalized
    expect(screen.getByText(`09/04 - 16/04${FINALIZED_INDICATOR}`)).toBeInTheDocument()
    // First period is not finalized
    expect(screen.getByText('16/04 - 23/04')).toBeInTheDocument()
  })

  it('should render with empty periods list', () => {
    const handleSelect = vi.fn()
    render(
      <WeekSelector
        periods={[]}
        selectedPeriod={null}
        onSelect={handleSelect}
      />
    )

    expect(screen.getByText(WEEK_SELECTOR_LABELS.currentWeek)).toBeInTheDocument()
    const select = screen.getByRole('combobox')
    expect(select).toHaveValue('current')
  })
})
