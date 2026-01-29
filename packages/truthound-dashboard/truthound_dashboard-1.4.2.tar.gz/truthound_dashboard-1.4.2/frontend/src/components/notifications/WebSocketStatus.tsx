/**
 * WebSocket Connection Status Indicator
 *
 * Displays the current WebSocket connection status with visual feedback
 * and optional reconnect button.
 */

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Wifi, WifiOff, Loader2, AlertCircle, RefreshCw } from 'lucide-react'
import type { WebSocketStatus } from '@/hooks/useWebSocket'

interface WebSocketStatusIndicatorProps {
  /** Current WebSocket status */
  status: WebSocketStatus
  /** Number of reconnect attempts */
  reconnectAttempts?: number
  /** Callback to manually reconnect */
  onReconnect?: () => void
  /** Show reconnect button when disconnected */
  showReconnectButton?: boolean
  /** Additional CSS classes */
  className?: string
  /** Compact mode (icon only) */
  compact?: boolean
}

const STATUS_CONFIG: Record<
  WebSocketStatus,
  {
    icon: typeof Wifi
    label: string
    colorClass: string
    bgClass: string
    animate?: boolean
  }
> = {
  connected: {
    icon: Wifi,
    label: 'Real-time updates active',
    colorClass: 'text-green-500',
    bgClass: 'bg-green-500/10',
  },
  connecting: {
    icon: Loader2,
    label: 'Connecting...',
    colorClass: 'text-blue-500',
    bgClass: 'bg-blue-500/10',
    animate: true,
  },
  disconnected: {
    icon: WifiOff,
    label: 'Real-time updates disconnected',
    colorClass: 'text-muted-foreground',
    bgClass: 'bg-muted/50',
  },
  reconnecting: {
    icon: RefreshCw,
    label: 'Reconnecting...',
    colorClass: 'text-yellow-500',
    bgClass: 'bg-yellow-500/10',
    animate: true,
  },
  error: {
    icon: AlertCircle,
    label: 'Connection error',
    colorClass: 'text-red-500',
    bgClass: 'bg-red-500/10',
  },
}

export function WebSocketStatusIndicator({
  status,
  reconnectAttempts = 0,
  onReconnect,
  showReconnectButton = true,
  className,
  compact = false,
}: WebSocketStatusIndicatorProps) {
  const config = STATUS_CONFIG[status]
  const Icon = config.icon

  const tooltipContent = (
    <div className="space-y-1">
      <div className="font-medium">{config.label}</div>
      {status === 'reconnecting' && reconnectAttempts > 0 && (
        <div className="text-xs text-muted-foreground">
          Attempt {reconnectAttempts}
        </div>
      )}
      {(status === 'disconnected' || status === 'error') && onReconnect && (
        <div className="text-xs text-muted-foreground">Click to reconnect</div>
      )}
    </div>
  )

  const indicator = (
    <div
      className={cn(
        'flex items-center gap-2 rounded-full px-3 py-1.5 transition-colors',
        config.bgClass,
        className
      )}
    >
      <Icon
        className={cn(
          'h-4 w-4',
          config.colorClass,
          config.animate && 'animate-spin'
        )}
      />
      {!compact && (
        <span className={cn('text-sm', config.colorClass)}>
          {status === 'connected'
            ? 'Live'
            : status === 'connecting'
              ? 'Connecting'
              : status === 'reconnecting'
                ? `Reconnecting${reconnectAttempts > 0 ? ` (${reconnectAttempts})` : ''}`
                : status === 'error'
                  ? 'Error'
                  : 'Offline'}
        </span>
      )}
    </div>
  )

  const showButton =
    showReconnectButton &&
    (status === 'disconnected' || status === 'error') &&
    onReconnect

  return (
    <TooltipProvider>
      <div className="flex items-center gap-2">
        <Tooltip>
          <TooltipTrigger asChild>
            {showButton ? (
              <button
                onClick={onReconnect}
                className="cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded-full"
              >
                {indicator}
              </button>
            ) : (
              <div>{indicator}</div>
            )}
          </TooltipTrigger>
          <TooltipContent>{tooltipContent}</TooltipContent>
        </Tooltip>

        {showButton && !compact && (
          <Button
            variant="outline"
            size="sm"
            onClick={onReconnect}
            className="h-7 px-2"
          >
            <RefreshCw className="h-3 w-3 mr-1" />
            Reconnect
          </Button>
        )}
      </div>
    </TooltipProvider>
  )
}

/**
 * Simple dot indicator for WebSocket status
 * For use in compact spaces like table headers
 */
export function WebSocketStatusDot({
  status,
  className,
}: {
  status: WebSocketStatus
  className?: string
}) {
  const config = STATUS_CONFIG[status]

  const dotColor = {
    connected: 'bg-green-500',
    connecting: 'bg-blue-500',
    disconnected: 'bg-gray-400',
    reconnecting: 'bg-yellow-500',
    error: 'bg-red-500',
  }[status]

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            className={cn(
              'relative inline-flex h-2 w-2 rounded-full',
              dotColor,
              className
            )}
          >
            {(status === 'connecting' || status === 'reconnecting') && (
              <span
                className={cn(
                  'absolute inline-flex h-full w-full animate-ping rounded-full opacity-75',
                  dotColor
                )}
              />
            )}
          </span>
        </TooltipTrigger>
        <TooltipContent>{config.label}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

export default WebSocketStatusIndicator
