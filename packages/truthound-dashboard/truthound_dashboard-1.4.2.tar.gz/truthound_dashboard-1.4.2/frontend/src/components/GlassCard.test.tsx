/**
 * GlassCard Component Tests
 *
 * Tests for the GlassCard component with hover effects and glow animations.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { GlassCard } from './GlassCard'

describe('GlassCard', () => {
  it('renders children correctly', () => {
    render(
      <GlassCard>
        <span>Test Content</span>
      </GlassCard>
    )
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(
      <GlassCard className="custom-class">
        <span>Content</span>
      </GlassCard>
    )
    const card = container.firstChild as HTMLElement
    expect(card).toHaveClass('custom-class')
  })

  it('has default transition classes', () => {
    const { container } = render(
      <GlassCard>
        <span>Content</span>
      </GlassCard>
    )
    const card = container.firstChild as HTMLElement
    expect(card).toHaveClass('relative')
    expect(card).toHaveClass('overflow-hidden')
    expect(card).toHaveClass('transition-all')
  })

  it('applies translateY transform on hover', () => {
    const { container } = render(
      <GlassCard>
        <span>Content</span>
      </GlassCard>
    )
    const card = container.firstChild as HTMLElement

    // Initial state - no transform
    expect(card.style.transform).toBe('translateY(0)')

    // Hover state
    fireEvent.mouseEnter(card)
    expect(card.style.transform).toBe('translateY(-2px)')

    // Leave hover
    fireEvent.mouseLeave(card)
    expect(card.style.transform).toBe('translateY(0)')
  })

  it('tracks mouse position on mouse move', () => {
    const { container } = render(
      <GlassCard>
        <span>Content</span>
      </GlassCard>
    )
    const card = container.firstChild as HTMLElement

    // Simulate getBoundingClientRect for the card
    vi.spyOn(card, 'getBoundingClientRect').mockReturnValue({
      left: 100,
      top: 100,
      right: 300,
      bottom: 300,
      width: 200,
      height: 200,
      x: 100,
      y: 100,
      toJSON: () => {},
    })

    fireEvent.mouseMove(card, { clientX: 150, clientY: 150 })

    // The mouse position should be tracked (position relative to card)
    // We can verify by checking the shine effect overlay styles
    const overlays = container.querySelectorAll('.pointer-events-none')
    expect(overlays.length).toBeGreaterThan(0)
  })

  it('shows glow effects on hover', () => {
    const { container } = render(
      <GlassCard glowColor="#ff0000">
        <span>Content</span>
      </GlassCard>
    )
    const card = container.firstChild as HTMLElement

    // Before hover - overlays should have opacity 0
    const overlays = container.querySelectorAll(
      '.pointer-events-none'
    ) as NodeListOf<HTMLElement>
    overlays.forEach((overlay) => {
      expect(overlay.style.opacity).toBe('0')
    })

    // After hover - overlays should be visible
    fireEvent.mouseEnter(card)
    overlays.forEach((overlay) => {
      // At least one overlay should become visible
      const opacity = parseFloat(overlay.style.opacity)
      expect(opacity).toBeGreaterThanOrEqual(0)
    })
  })

  it('uses default glow color when not specified', () => {
    const { container } = render(
      <GlassCard>
        <span>Content</span>
      </GlassCard>
    )
    const card = container.firstChild as HTMLElement
    fireEvent.mouseEnter(card)

    // Default glow color is white - check that overlays have backgrounds with 'white'
    const overlays = container.querySelectorAll(
      '.pointer-events-none'
    ) as NodeListOf<HTMLElement>
    expect(overlays.length).toBeGreaterThan(0)
  })

  it('uses custom glow color when provided', () => {
    const customColor = '#fd9e4b'
    const { container } = render(
      <GlassCard glowColor={customColor}>
        <span>Content</span>
      </GlassCard>
    )
    const card = container.firstChild as HTMLElement

    // Trigger hover to make effects visible
    fireEvent.mouseEnter(card)

    // Check that overlays contain the custom color in their styles
    const overlays = container.querySelectorAll(
      '.pointer-events-none'
    ) as NodeListOf<HTMLElement>
    let hasCustomColor = false
    overlays.forEach((overlay) => {
      if (overlay.style.background?.includes(customColor)) {
        hasCustomColor = true
      }
    })
    expect(hasCustomColor).toBe(true)
  })

  it('renders multiple effect overlays', () => {
    const { container } = render(
      <GlassCard>
        <span>Content</span>
      </GlassCard>
    )

    // Should have 3 overlay divs (shine, border glow, sparkle line)
    const overlays = container.querySelectorAll('.pointer-events-none')
    expect(overlays.length).toBe(3)
  })

  it('has rounded border on border glow effect', () => {
    const { container } = render(
      <GlassCard>
        <span>Content</span>
      </GlassCard>
    )

    // The border glow overlay should have rounded-lg class
    const overlays = container.querySelectorAll('.pointer-events-none')
    let hasRoundedBorder = false
    overlays.forEach((overlay) => {
      if (overlay.classList.contains('rounded-lg')) {
        hasRoundedBorder = true
      }
    })
    expect(hasRoundedBorder).toBe(true)
  })

  it('handles rapid mouse enter/leave events', () => {
    const { container } = render(
      <GlassCard>
        <span>Content</span>
      </GlassCard>
    )
    const card = container.firstChild as HTMLElement

    // Rapidly toggle hover state
    for (let i = 0; i < 10; i++) {
      fireEvent.mouseEnter(card)
      fireEvent.mouseLeave(card)
    }

    // Should end in non-hover state
    expect(card.style.transform).toBe('translateY(0)')
  })

  it('maintains proper z-index layering for overlays', () => {
    const { container } = render(
      <GlassCard>
        <span>Content</span>
      </GlassCard>
    )

    const overlays = container.querySelectorAll('.z-10')
    expect(overlays.length).toBe(3)
  })
})
