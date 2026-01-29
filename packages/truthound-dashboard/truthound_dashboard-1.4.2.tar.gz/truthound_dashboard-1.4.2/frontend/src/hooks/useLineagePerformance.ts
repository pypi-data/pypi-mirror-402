/**
 * Hook for monitoring and managing lineage graph performance.
 *
 * Tracks FPS, memory usage, and automatically enables optimizations
 * when performance degrades.
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import {
  createPerformanceMonitor,
  getMemoryUsage,
  getRecommendedOptimizations,
  PERFORMANCE_THRESHOLDS,
  type PerformanceMetrics,
} from '@/lib/lineage-performance'

// ============================================================================
// Types
// ============================================================================

interface UseLineagePerformanceReturn {
  /** Current performance metrics */
  metrics: PerformanceMetrics
  /** Whether performance mode is enabled */
  isPerformanceMode: boolean
  /** Toggle performance mode */
  setPerformanceMode: (enabled: boolean) => void
  /** Record a render frame */
  recordFrame: () => void
  /** Whether performance is currently degraded */
  isPerformanceDegraded: boolean
  /** Recommendations based on current state */
  recommendations: ReturnType<typeof getRecommendedOptimizations>
}

// ============================================================================
// Hook
// ============================================================================

export function useLineagePerformance(nodeCount: number): UseLineagePerformanceReturn {
  // Performance mode state
  const [isPerformanceMode, setPerformanceMode] = useState(false)

  // Metrics state
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fps: 60,
    nodeCount: 0,
    edgeCount: 0,
    visibleNodes: 0,
    clusterCount: 0,
    memoryUsage: null,
    renderTime: 0,
  })

  // Performance monitor ref
  const monitorRef = useRef(createPerformanceMonitor())
  const frameCountRef = useRef(0)

  // Get recommendations based on node count
  const recommendations = getRecommendedOptimizations(nodeCount)

  // Auto-enable performance mode for large graphs
  useEffect(() => {
    if (nodeCount >= PERFORMANCE_THRESHOLDS.VIRTUALIZATION_THRESHOLD && !isPerformanceMode) {
      setPerformanceMode(true)
    }
  }, [nodeCount, isPerformanceMode])

  // Record frame for FPS calculation
  const recordFrame = useCallback(() => {
    const monitor = monitorRef.current

    if (frameCountRef.current === 0) {
      monitor.startFrame()
    }

    frameCountRef.current++

    // Update metrics every 30 frames
    if (frameCountRef.current >= 30) {
      monitor.endFrame()
      const { fps, averageRenderTime } = monitor.getMetrics()

      setMetrics((prev) => ({
        ...prev,
        fps,
        renderTime: averageRenderTime,
        memoryUsage: getMemoryUsage(),
        nodeCount,
      }))

      frameCountRef.current = 0
      monitor.reset()
    }
  }, [nodeCount])

  // Update metrics periodically
  useEffect(() => {
    const interval = setInterval(() => {
      const memory = getMemoryUsage()
      setMetrics((prev) => ({
        ...prev,
        memoryUsage: memory,
        nodeCount,
      }))
    }, 5000)

    return () => clearInterval(interval)
  }, [nodeCount])

  // Detect performance degradation
  const isPerformanceDegraded = metrics.fps < PERFORMANCE_THRESHOLDS.TARGET_FPS

  // Auto-enable optimizations when performance degrades
  useEffect(() => {
    if (isPerformanceDegraded && !isPerformanceMode && nodeCount > 50) {
      setPerformanceMode(true)
    }
  }, [isPerformanceDegraded, isPerformanceMode, nodeCount])

  return {
    metrics,
    isPerformanceMode,
    setPerformanceMode,
    recordFrame,
    isPerformanceDegraded,
    recommendations,
  }
}

// ============================================================================
// FPS Monitor Component Hook
// ============================================================================

interface FPSMonitorOptions {
  /** Update interval in milliseconds */
  updateInterval?: number
  /** Whether to log FPS to console */
  debug?: boolean
}

export function useFPSMonitor(options: FPSMonitorOptions = {}) {
  const { updateInterval = 1000, debug = false } = options

  const [fps, setFps] = useState(60)
  const framesRef = useRef(0)
  const lastTimeRef = useRef(performance.now())

  useEffect(() => {
    let animationFrameId: number

    const countFrame = () => {
      framesRef.current++
      animationFrameId = requestAnimationFrame(countFrame)
    }

    const calculateFPS = () => {
      const now = performance.now()
      const elapsed = now - lastTimeRef.current

      if (elapsed >= updateInterval) {
        const currentFps = Math.round((framesRef.current * 1000) / elapsed)
        setFps(currentFps)

        if (debug) {
          console.log(`FPS: ${currentFps}`)
        }

        framesRef.current = 0
        lastTimeRef.current = now
      }
    }

    const intervalId = setInterval(calculateFPS, updateInterval)
    animationFrameId = requestAnimationFrame(countFrame)

    return () => {
      cancelAnimationFrame(animationFrameId)
      clearInterval(intervalId)
    }
  }, [updateInterval, debug])

  return fps
}

// ============================================================================
// Memory Monitor Hook
// ============================================================================

interface MemoryStats {
  usedMB: number | null
  totalMB: number | null
  limitMB: number | null
  usagePercent: number | null
}

export function useMemoryMonitor(updateInterval = 5000): MemoryStats {
  const [memoryStats, setMemoryStats] = useState<MemoryStats>({
    usedMB: null,
    totalMB: null,
    limitMB: null,
    usagePercent: null,
  })

  useEffect(() => {
    const updateMemory = () => {
      const perf = performance as Performance & {
        memory?: {
          usedJSHeapSize: number
          totalJSHeapSize: number
          jsHeapSizeLimit: number
        }
      }

      if (perf.memory) {
        const usedMB = Math.round(perf.memory.usedJSHeapSize / 1024 / 1024)
        const totalMB = Math.round(perf.memory.totalJSHeapSize / 1024 / 1024)
        const limitMB = Math.round(perf.memory.jsHeapSizeLimit / 1024 / 1024)
        const usagePercent = Math.round((usedMB / limitMB) * 100)

        setMemoryStats({ usedMB, totalMB, limitMB, usagePercent })
      }
    }

    updateMemory()
    const intervalId = setInterval(updateMemory, updateInterval)

    return () => clearInterval(intervalId)
  }, [updateInterval])

  return memoryStats
}
