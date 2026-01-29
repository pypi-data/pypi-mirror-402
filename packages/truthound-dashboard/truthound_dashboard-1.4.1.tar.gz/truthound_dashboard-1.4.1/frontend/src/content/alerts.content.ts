/**
 * Unified Alerts page translations.
 *
 * Contains translations for the unified alerts management page.
 */
import { t, type Dictionary } from 'intlayer'

const alertsContent = {
  key: 'alerts',
  content: {
    title: t({ en: 'Alerts', ko: '알림' }),
    subtitle: t({
      en: 'Unified view of all system alerts',
      ko: '모든 시스템 알림 통합 보기',
    }),

    // Summary cards
    summary: {
      totalAlerts: t({ en: 'Total Alerts', ko: '전체 알림' }),
      activeAlerts: t({ en: 'Active Alerts', ko: '활성 알림' }),
      criticalAlerts: t({ en: 'Critical', ko: '심각' }),
      highAlerts: t({ en: 'High', ko: '높음' }),
      mediumAlerts: t({ en: 'Medium', ko: '보통' }),
      lowAlerts: t({ en: 'Low', ko: '낮음' }),
      infoAlerts: t({ en: 'Info', ko: '정보' }),
      trend24h: t({ en: '24h Trend', ko: '24시간 추이' }),
    },

    // Source types
    sources: {
      all: t({ en: 'All Sources', ko: '모든 소스' }),
      model: t({ en: 'Model Monitoring', ko: '모델 모니터링' }),
      drift: t({ en: 'Drift Detection', ko: '드리프트 감지' }),
      anomaly: t({ en: 'Anomaly Detection', ko: '이상 탐지' }),
      validation: t({ en: 'Validation', ko: '검증' }),
    },

    // Severity levels
    severity: {
      critical: t({ en: 'Critical', ko: '심각' }),
      high: t({ en: 'High', ko: '높음' }),
      medium: t({ en: 'Medium', ko: '보통' }),
      low: t({ en: 'Low', ko: '낮음' }),
      info: t({ en: 'Info', ko: '정보' }),
    },

    // Status
    status: {
      all: t({ en: 'All Status', ko: '모든 상태' }),
      open: t({ en: 'Open', ko: '열림' }),
      acknowledged: t({ en: 'Acknowledged', ko: '확인됨' }),
      resolved: t({ en: 'Resolved', ko: '해결됨' }),
      ignored: t({ en: 'Ignored', ko: '무시됨' }),
    },

    // Actions
    actions: {
      acknowledge: t({ en: 'Acknowledge', ko: '확인' }),
      resolve: t({ en: 'Resolve', ko: '해결' }),
      ignore: t({ en: 'Ignore', ko: '무시' }),
      bulkAcknowledge: t({ en: 'Acknowledge Selected', ko: '선택 항목 확인' }),
      bulkResolve: t({ en: 'Resolve Selected', ko: '선택 항목 해결' }),
      viewDetails: t({ en: 'View Details', ko: '상세 보기' }),
      viewSource: t({ en: 'View Source', ko: '소스 보기' }),
      refresh: t({ en: 'Refresh', ko: '새로고침' }),
    },

    // Filters
    filters: {
      source: t({ en: 'Source', ko: '소스' }),
      severity: t({ en: 'Severity', ko: '심각도' }),
      status: t({ en: 'Status', ko: '상태' }),
      timeRange: t({ en: 'Time Range', ko: '시간 범위' }),
      search: t({ en: 'Search alerts...', ko: '알림 검색...' }),
    },

    // Time ranges
    timeRanges: {
      last1h: t({ en: 'Last 1 hour', ko: '최근 1시간' }),
      last6h: t({ en: 'Last 6 hours', ko: '최근 6시간' }),
      last24h: t({ en: 'Last 24 hours', ko: '최근 24시간' }),
      last7d: t({ en: 'Last 7 days', ko: '최근 7일' }),
      last30d: t({ en: 'Last 30 days', ko: '최근 30일' }),
    },

    // Correlation
    correlation: {
      title: t({ en: 'Related Alerts', ko: '관련 알림' }),
      noCorrelations: t({
        en: 'No related alerts found',
        ko: '관련 알림이 없습니다',
      }),
      sameSource: t({ en: 'Same Source', ko: '동일 소스' }),
      temporalSeverity: t({ en: 'Similar Time & Severity', ko: '유사 시간 및 심각도' }),
      correlationScore: t({ en: 'Correlation Score', ko: '상관관계 점수' }),
    },

    // Empty states
    empty: {
      noAlerts: t({ en: 'No alerts found', ko: '알림이 없습니다' }),
      noAlertsDesc: t({
        en: 'There are no alerts matching your filters',
        ko: '필터에 맞는 알림이 없습니다',
      }),
      allClear: t({ en: 'All Clear!', ko: '모두 정상!' }),
      allClearDesc: t({
        en: 'No active alerts in your system',
        ko: '시스템에 활성 알림이 없습니다',
      }),
    },

    // Messages
    messages: {
      acknowledgeSuccess: t({
        en: 'Alert acknowledged successfully',
        ko: '알림이 확인되었습니다',
      }),
      acknowledgeFailed: t({
        en: 'Failed to acknowledge alert',
        ko: '알림 확인에 실패했습니다',
      }),
      resolveSuccess: t({
        en: 'Alert resolved successfully',
        ko: '알림이 해결되었습니다',
      }),
      resolveFailed: t({
        en: 'Failed to resolve alert',
        ko: '알림 해결에 실패했습니다',
      }),
      bulkSuccess: t({
        en: '{count} alerts updated successfully',
        ko: '{count}개 알림이 업데이트되었습니다',
      }),
      bulkPartial: t({
        en: '{success} updated, {failed} failed',
        ko: '{success}개 성공, {failed}개 실패',
      }),
    },

    // Table columns
    columns: {
      severity: t({ en: 'Severity', ko: '심각도' }),
      source: t({ en: 'Source', ko: '소스' }),
      title: t({ en: 'Title', ko: '제목' }),
      status: t({ en: 'Status', ko: '상태' }),
      createdAt: t({ en: 'Created', ko: '생성일' }),
      actions: t({ en: 'Actions', ko: '작업' }),
    },

    // Details panel
    details: {
      title: t({ en: 'Alert Details', ko: '알림 상세' }),
      message: t({ en: 'Message', ko: '메시지' }),
      source: t({ en: 'Source', ko: '소스' }),
      createdAt: t({ en: 'Created At', ko: '생성 시간' }),
      acknowledgedAt: t({ en: 'Acknowledged At', ko: '확인 시간' }),
      acknowledgedBy: t({ en: 'Acknowledged By', ko: '확인자' }),
      resolvedAt: t({ en: 'Resolved At', ko: '해결 시간' }),
      resolvedBy: t({ en: 'Resolved By', ko: '해결자' }),
      additionalDetails: t({ en: 'Additional Details', ko: '추가 정보' }),
    },

    // Acknowledge dialog
    acknowledgeDialog: {
      title: t({ en: 'Acknowledge Alert', ko: '알림 확인' }),
      description: t({
        en: 'Enter your name to acknowledge this alert',
        ko: '알림을 확인하려면 이름을 입력하세요',
      }),
      nameLabel: t({ en: 'Your Name', ko: '이름' }),
      messageLabel: t({ en: 'Message (optional)', ko: '메시지 (선택)' }),
      confirm: t({ en: 'Acknowledge', ko: '확인' }),
      cancel: t({ en: 'Cancel', ko: '취소' }),
    },

    // Resolve dialog
    resolveDialog: {
      title: t({ en: 'Resolve Alert', ko: '알림 해결' }),
      description: t({
        en: 'Enter details to resolve this alert',
        ko: '알림을 해결하려면 상세 정보를 입력하세요',
      }),
      nameLabel: t({ en: 'Your Name', ko: '이름' }),
      messageLabel: t({ en: 'Resolution Message', ko: '해결 메시지' }),
      confirm: t({ en: 'Resolve', ko: '해결' }),
      cancel: t({ en: 'Cancel', ko: '취소' }),
    },
  },
} satisfies Dictionary

export default alertsContent
