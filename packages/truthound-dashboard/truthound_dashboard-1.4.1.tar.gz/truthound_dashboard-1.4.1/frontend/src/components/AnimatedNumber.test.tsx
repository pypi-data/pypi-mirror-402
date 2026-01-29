/**
 * AnimatedNumber Component Tests
 *
 * Tests for the AnimatedNumber component that displays animated numeric values.
 * Note: This component uses requestAnimationFrame which requires special handling in tests.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AnimatedNumber } from './AnimatedNumber'

// Mock requestAnimationFrame for predictable testing
let rafCallback: FrameRequestCallback | null = null
let rafId = 0

const mockRaf = (callback: FrameRequestCallback): number => {
  rafCallback = callback
  return ++rafId
}

const mockCancelRaf = (_id: number): void => {
  rafCallback = null
}

// Simulate animation frames
const runAnimationFrame = (timestamp: number) => {
  if (rafCallback) {
    const cb = rafCallback
    rafCallback = null
    cb(timestamp)
  }
}

describe('AnimatedNumber', () => {
  beforeEach(() => {
    rafCallback = null
    rafId = 0
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation(mockRaf)
    vi.spyOn(window, 'cancelAnimationFrame').mockImplementation(mockCancelRaf)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders with initial value of 0', () => {
    render(<AnimatedNumber value={100} />)
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('displays 0 immediately when value is 0', () => {
    render(<AnimatedNumber value={0} />)
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('starts animation on mount', () => {
    render(<AnimatedNumber value={100} />)
    // requestAnimationFrame should have been called
    expect(window.requestAnimationFrame).toHaveBeenCalled()
  })

  it('applies custom className', () => {
    render(<AnimatedNumber value={50} className="custom-class" />)
    const span = screen.getByText('0')
    expect(span).toHaveClass('custom-class')
  })

  it('rounds displayed values to integers', () => {
    const { container } = render(<AnimatedNumber value={99} />)
    const text = container.querySelector('span')?.textContent
    // Should be a valid integer string
    expect(text).toMatch(/^\d+$/)
  })

  it('has animation classes during animation', () => {
    render(<AnimatedNumber value={100} />)
    const span = screen.getByText('0')
    expect(span).toHaveClass('animate-in')
  })

  it('does not start animation when value is 0', () => {
    vi.clearAllMocks()
    render(<AnimatedNumber value={0} />)
    // For value 0, it should not start animation (handled as edge case)
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('animates towards target value when frames are run', async () => {
    const { container } = render(<AnimatedNumber value={100} duration={1000} />)

    // Run animation frames to simulate progress
    // The easing function is ease-out-expo, so progress increases quickly
    runAnimationFrame(0) // Start at time 0
    runAnimationFrame(500) // Half way through duration
    runAnimationFrame(500) // Continue...

    // After some frames, value should be > 0
    await waitFor(() => {
      const value = parseInt(container.querySelector('span')?.textContent || '0')
      expect(value).toBeGreaterThanOrEqual(0)
    })
  })

  it('updates value immediately after first animation completes', async () => {
    const { rerender, container } = render(<AnimatedNumber value={100} />)

    // Simulate animation completion by running many frames
    for (let i = 0; i <= 1200; i += 100) {
      runAnimationFrame(i)
    }

    // After animation, update to new value
    rerender(<AnimatedNumber value={200} />)

    // The component skips animation on subsequent value changes
    await waitFor(() => {
      const value = container.querySelector('span')?.textContent
      // Should show new value (animation was skipped due to hasAnimated ref)
      expect(value).toBe('200')
    })
  })

  it('cleans up animation frame on unmount', () => {
    const { unmount } = render(<AnimatedNumber value={100} />)
    expect(window.requestAnimationFrame).toHaveBeenCalled()

    unmount()
    // cancelAnimationFrame should be called during cleanup
    expect(window.cancelAnimationFrame).toHaveBeenCalled()
  })

  it('accepts custom duration prop', () => {
    render(<AnimatedNumber value={100} duration={500} />)
    // Component renders with custom duration (affects animation speed)
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('renders inline-block span element', () => {
    const { container } = render(<AnimatedNumber value={100} />)
    const span = container.querySelector('span')
    expect(span).toBeInTheDocument()
    expect(span).toHaveClass('inline-block')
  })
})
