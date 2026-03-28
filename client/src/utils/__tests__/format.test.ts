import { describe, it, expect } from 'vitest'
import { formatPrice } from '../format'

describe('formatPrice', () => {
  it('formats number to ¥X.XX', () => {
    expect(formatPrice(1000)).toBe('¥10.00')
  })
  it('formats string input', () => {
    expect(formatPrice('1550')).toBe('¥15.50')
  })
  it('returns ¥0.00 for null', () => {
    expect(formatPrice(null)).toBe('¥0.00')
  })
  it('returns ¥0.00 for undefined', () => {
    expect(formatPrice(undefined)).toBe('¥0.00')
  })
  it('handles zero', () => {
    expect(formatPrice(0)).toBe('¥0.00')
  })
  it('handles NaN', () => {
    expect(formatPrice(NaN)).toBe('¥0.00')
  })
})
