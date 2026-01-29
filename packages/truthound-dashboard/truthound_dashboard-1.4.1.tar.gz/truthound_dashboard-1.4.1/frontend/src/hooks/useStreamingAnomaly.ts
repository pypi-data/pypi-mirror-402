/**
 * Hook for managing streaming anomaly detection sessions with WebSocket support.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import type {
  StreamingSession,
  StreamingSessionCreate,
  StreamingAlert,
  StreamingStatusResponse,
  StreamingAlgorithmInfo,
} from '@/api/client'
import {
  startStreamingSession,
  stopStreamingSession,
  getStreamingStatus,
  listStreamingAlgorithms,
  getStreamingWebSocketUrl,
} from '@/api/client'

interface UseStreamingAnomalyOptions {
  /** Auto-reconnect on disconnect */
  autoReconnect?: boolean
  /** Reconnect interval in ms */
  reconnectInterval?: number
  /** Max reconnect attempts */
  maxReconnectAttempts?: number
  /** Poll interval for status updates when not using WebSocket (ms) */
  pollInterval?: number
}

interface UseStreamingAnomalyReturn {
  /** Current session */
  session: StreamingSession | null
  /** Session status with statistics */
  status: StreamingStatusResponse | null
  /** Recent alerts from the session */
  alerts: StreamingAlert[]
  /** Available streaming algorithms */
  algorithms: StreamingAlgorithmInfo[]
  /** Whether currently loading */
  isLoading: boolean
  /** Whether WebSocket is connected */
  isConnected: boolean
  /** Error message if any */
  error: string | null
  /** Start a new streaming session */
  startSession: (config: StreamingSessionCreate) => Promise<StreamingSession | null>
  /** Stop the current session */
  stopSession: () => Promise<void>
  /** Push a data point via WebSocket */
  pushData: (data: Record<string, unknown>) => void
  /** Clear alerts */
  clearAlerts: () => void
  /** Load available algorithms */
  loadAlgorithms: () => Promise<void>
  /** Manually refresh status */
  refreshStatus: () => Promise<void>
}

export function useStreamingAnomaly(
  options: UseStreamingAnomalyOptions = {}
): UseStreamingAnomalyReturn {
  const {
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    pollInterval = 2000,
  } = options

  // State
  const [session, setSession] = useState<StreamingSession | null>(null)
  const [status, setStatus] = useState<StreamingStatusResponse | null>(null)
  const [alerts, setAlerts] = useState<StreamingAlert[]>([])
  const [algorithms, setAlgorithms] = useState<StreamingAlgorithmInfo[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Refs for WebSocket management
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Cleanup function
  const cleanup = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
    setIsConnected(false)
  }, [])

  // Connect WebSocket
  const connectWebSocket = useCallback(
    (sessionId: string) => {
      cleanup()

      const wsUrl = getStreamingWebSocketUrl(sessionId)
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        setIsConnected(true)
        setError(null)
        reconnectAttemptsRef.current = 0
      }

      ws.onclose = () => {
        setIsConnected(false)
        wsRef.current = null

        // Auto-reconnect if enabled and session is still active
        if (
          autoReconnect &&
          session?.status === 'running' &&
          reconnectAttemptsRef.current < maxReconnectAttempts
        ) {
          reconnectAttemptsRef.current++
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket(sessionId)
          }, reconnectInterval)
        }
      }

      ws.onerror = () => {
        setError('WebSocket connection error')
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)

          if (message.type === 'alert') {
            const alert = message.alert as StreamingAlert
            setAlerts((prev) => [alert, ...prev].slice(0, 100))
          } else if (message.type === 'ack') {
            // Acknowledgment received
          } else if (message.type === 'pong') {
            // Pong received (keep-alive)
          }
        } catch {
          // Ignore parse errors
        }
      }

      wsRef.current = ws
    },
    [cleanup, autoReconnect, maxReconnectAttempts, reconnectInterval, session?.status]
  )

  // Load algorithms
  const loadAlgorithms = useCallback(async () => {
    try {
      const response = await listStreamingAlgorithms()
      setAlgorithms(response.algorithms)
    } catch (err) {
      setError('Failed to load algorithms')
    }
  }, [])

  // Refresh status
  const refreshStatus = useCallback(async () => {
    if (!session?.id) return

    try {
      const newStatus = await getStreamingStatus(session.id)
      setStatus(newStatus)

      // Update alerts from status if available
      if (newStatus.recent_alerts && newStatus.recent_alerts.length > 0) {
        setAlerts((prev) => {
          const existingIds = new Set(prev.map((a) => a.id))
          const newAlerts = newStatus.recent_alerts.filter(
            (a) => !existingIds.has(a.id)
          )
          return [...newAlerts, ...prev].slice(0, 100)
        })
      }
    } catch {
      // Ignore errors during polling
    }
  }, [session?.id])

  // Start session
  const startSession = useCallback(
    async (config: StreamingSessionCreate): Promise<StreamingSession | null> => {
      setIsLoading(true)
      setError(null)

      try {
        const newSession = await startStreamingSession(config)
        setSession(newSession)
        setAlerts([])

        // Connect WebSocket
        connectWebSocket(newSession.id)

        // Start polling for status updates
        pollIntervalRef.current = setInterval(refreshStatus, pollInterval)

        return newSession
      } catch (err) {
        setError('Failed to start streaming session')
        return null
      } finally {
        setIsLoading(false)
      }
    },
    [connectWebSocket, refreshStatus, pollInterval]
  )

  // Stop session
  const stopSession = useCallback(async () => {
    if (!session?.id) return

    setIsLoading(true)

    try {
      const stoppedSession = await stopStreamingSession(session.id)
      setSession(stoppedSession)
      cleanup()
    } catch (err) {
      setError('Failed to stop session')
    } finally {
      setIsLoading(false)
    }
  }, [session?.id, cleanup])

  // Push data via WebSocket
  const pushData = useCallback((data: Record<string, unknown>) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return
    }

    wsRef.current.send(
      JSON.stringify({
        type: 'data',
        data,
        timestamp: new Date().toISOString(),
      })
    )
  }, [])

  // Clear alerts
  const clearAlerts = useCallback(() => {
    setAlerts([])
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup()
    }
  }, [cleanup])

  // Keep WebSocket alive with ping
  useEffect(() => {
    if (!isConnected || !wsRef.current) return

    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)

    return () => clearInterval(pingInterval)
  }, [isConnected])

  return {
    session,
    status,
    alerts,
    algorithms,
    isLoading,
    isConnected,
    error,
    startSession,
    stopSession,
    pushData,
    clearAlerts,
    loadAlgorithms,
    refreshStatus,
  }
}
