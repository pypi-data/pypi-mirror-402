/**
 * WebSocket hook for real-time updates
 *
 * Features:
 * - Auto-reconnect with exponential backoff
 * - Connection status tracking
 * - Ping/pong heartbeat
 * - Type-safe message handling
 */

import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * WebSocket connection states
 */
export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error'

/**
 * WebSocket message types for escalation incidents
 */
export type WebSocketMessageType =
  | 'connected'
  | 'disconnected'
  | 'ping'
  | 'pong'
  | 'error'
  | 'incident_created'
  | 'incident_updated'
  | 'incident_state_changed'
  | 'incident_resolved'
  | 'incident_acknowledged'
  | 'incident_escalated'

/**
 * Base WebSocket message structure
 */
export interface WebSocketMessage<T = Record<string, unknown>> {
  type: WebSocketMessageType
  timestamp: string
  data: T
}

/**
 * Incident event data structure
 */
export interface IncidentEventData {
  incident_id: string
  incident_ref: string
  policy_id: string
  state?: string
  current_level?: number
  from_state?: string
  to_state?: string
  actor?: string | null
  message?: string | null
  context?: Record<string, unknown>
  changes?: Record<string, unknown>
  resolved_by?: string | null
}

/**
 * WebSocket hook options
 */
export interface UseWebSocketOptions {
  /** WebSocket URL (defaults to /api/v1/ws/notifications/incidents) */
  url?: string
  /** Optional authentication token */
  token?: string
  /** Enable auto-reconnect (default: true) */
  autoReconnect?: boolean
  /** Maximum reconnect attempts (default: 10) */
  maxReconnectAttempts?: number
  /** Initial reconnect delay in ms (default: 1000) */
  initialReconnectDelay?: number
  /** Maximum reconnect delay in ms (default: 30000) */
  maxReconnectDelay?: number
  /** Ping interval in ms (default: 30000) */
  pingInterval?: number
  /** Connection timeout in ms (default: 10000) */
  connectionTimeout?: number
  /** Callback when message is received */
  onMessage?: (message: WebSocketMessage) => void
  /** Callback when connection status changes */
  onStatusChange?: (status: WebSocketStatus) => void
  /** Callback when error occurs */
  onError?: (error: Event | Error) => void
}

/**
 * WebSocket hook return value
 */
export interface UseWebSocketReturn {
  /** Current connection status */
  status: WebSocketStatus
  /** Whether WebSocket is connected */
  isConnected: boolean
  /** Last received message */
  lastMessage: WebSocketMessage | null
  /** Number of reconnect attempts */
  reconnectAttempts: number
  /** Send a message through the WebSocket */
  send: (data: Record<string, unknown>) => boolean
  /** Manually connect */
  connect: () => void
  /** Manually disconnect */
  disconnect: () => void
  /** Get connection info */
  connectionInfo: {
    url: string
    connectedAt: Date | null
    lastPingAt: Date | null
    lastPongAt: Date | null
  }
}

/**
 * Default WebSocket URL based on current location
 */
function getDefaultWebSocketUrl(path: string, token?: string): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  let url = `${protocol}//${host}${path}`
  if (token) {
    url += `?token=${encodeURIComponent(token)}`
  }
  return url
}

/**
 * Custom hook for WebSocket connection with auto-reconnect
 *
 * @example
 * ```tsx
 * const { status, isConnected, lastMessage } = useWebSocket({
 *   onMessage: (msg) => {
 *     if (msg.type === 'incident_state_changed') {
 *       // Handle incident state change
 *     }
 *   },
 * })
 * ```
 */
export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    url: customUrl,
    token,
    autoReconnect = true,
    maxReconnectAttempts = 10,
    initialReconnectDelay = 1000,
    maxReconnectDelay = 30000,
    pingInterval = 30000,
    connectionTimeout = 10000,
    onMessage,
    onStatusChange,
    onError,
  } = options

  const [status, setStatus] = useState<WebSocketStatus>('disconnected')
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  const [connectionInfo, setConnectionInfo] = useState({
    url: '',
    connectedAt: null as Date | null,
    lastPingAt: null as Date | null,
    lastPongAt: null as Date | null,
  })

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const connectionTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isMountedRef = useRef(true)

  // Store callbacks in refs to avoid reconnection on callback changes
  const onMessageRef = useRef(onMessage)
  const onStatusChangeRef = useRef(onStatusChange)
  const onErrorRef = useRef(onError)

  useEffect(() => {
    onMessageRef.current = onMessage
    onStatusChangeRef.current = onStatusChange
    onErrorRef.current = onError
  }, [onMessage, onStatusChange, onError])

  const updateStatus = useCallback((newStatus: WebSocketStatus) => {
    if (!isMountedRef.current) return
    setStatus(newStatus)
    onStatusChangeRef.current?.(newStatus)
  }, [])

  const clearTimers = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }
    if (connectionTimeoutRef.current) {
      clearTimeout(connectionTimeoutRef.current)
      connectionTimeoutRef.current = null
    }
  }, [])

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'ping' }))
      setConnectionInfo((prev) => ({ ...prev, lastPingAt: new Date() }))
    }
  }, [])

  const startPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
    }
    pingIntervalRef.current = setInterval(sendPing, pingInterval)
  }, [sendPing, pingInterval])

  const calculateReconnectDelay = useCallback(
    (attempt: number): number => {
      // Exponential backoff with jitter
      const delay = Math.min(
        initialReconnectDelay * Math.pow(2, attempt),
        maxReconnectDelay
      )
      // Add jitter (0-20% of delay)
      const jitter = delay * 0.2 * Math.random()
      return delay + jitter
    },
    [initialReconnectDelay, maxReconnectDelay]
  )

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    clearTimers()

    const wsUrl = customUrl || getDefaultWebSocketUrl('/api/v1/ws/notifications/incidents', token)
    setConnectionInfo((prev) => ({ ...prev, url: wsUrl }))

    updateStatus('connecting')

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      // Set connection timeout
      connectionTimeoutRef.current = setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          ws.close()
          updateStatus('error')
          onErrorRef.current?.(new Error('Connection timeout'))
        }
      }, connectionTimeout)

      ws.onopen = () => {
        if (!isMountedRef.current) return
        clearTimeout(connectionTimeoutRef.current!)
        connectionTimeoutRef.current = null

        updateStatus('connected')
        setReconnectAttempts(0)
        setConnectionInfo((prev) => ({ ...prev, connectedAt: new Date() }))
        startPingInterval()
      }

      ws.onclose = (event) => {
        if (!isMountedRef.current) return
        clearTimers()

        const wasConnected = status === 'connected'

        if (event.wasClean) {
          updateStatus('disconnected')
        } else if (autoReconnect && reconnectAttempts < maxReconnectAttempts) {
          updateStatus('reconnecting')
          const delay = calculateReconnectDelay(reconnectAttempts)
          setReconnectAttempts((prev) => prev + 1)

          reconnectTimeoutRef.current = setTimeout(() => {
            if (isMountedRef.current) {
              connect()
            }
          }, delay)
        } else {
          updateStatus(wasConnected ? 'disconnected' : 'error')
        }
      }

      ws.onerror = (event) => {
        if (!isMountedRef.current) return
        onErrorRef.current?.(event)
      }

      ws.onmessage = (event) => {
        if (!isMountedRef.current) return

        try {
          const message = JSON.parse(event.data) as WebSocketMessage

          // Handle pong response
          if (message.type === 'pong') {
            setConnectionInfo((prev) => ({ ...prev, lastPongAt: new Date() }))
            return
          }

          setLastMessage(message)
          onMessageRef.current?.(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
    } catch (error) {
      updateStatus('error')
      onErrorRef.current?.(error as Error)
    }
  }, [
    customUrl,
    token,
    autoReconnect,
    maxReconnectAttempts,
    connectionTimeout,
    reconnectAttempts,
    status,
    clearTimers,
    updateStatus,
    startPingInterval,
    calculateReconnectDelay,
  ])

  const disconnect = useCallback(() => {
    clearTimers()
    setReconnectAttempts(0)

    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnect')
      wsRef.current = null
    }

    updateStatus('disconnected')
  }, [clearTimers, updateStatus])

  const send = useCallback((data: Record<string, unknown>): boolean => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
      return true
    }
    return false
  }, [])

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    isMountedRef.current = true
    connect()

    return () => {
      isMountedRef.current = false
      clearTimers()
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmount')
        wsRef.current = null
      }
    }
  }, []) // Only run on mount/unmount

  // Reconnect when token changes
  useEffect(() => {
    if (token !== undefined) {
      disconnect()
      connect()
    }
  }, [token])

  return {
    status,
    isConnected: status === 'connected',
    lastMessage,
    reconnectAttempts,
    send,
    connect,
    disconnect,
    connectionInfo,
  }
}

export default useWebSocket
