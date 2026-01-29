/**
 * Triggers monitoring page translations.
 *
 * Contains translations for trigger monitoring, status tracking,
 * and webhook trigger management.
 */
import { t, type Dictionary } from 'intlayer'

const triggersContent = {
  key: 'triggers',
  content: {
    // Page header
    title: t({ en: 'Trigger Monitoring', ko: '트리거 모니터링' }),
    subtitle: t({
      en: 'Monitor data change, composite, and webhook triggers',
      ko: '데이터 변경, 복합, 웹훅 트리거 모니터링',
    }),

    // Tabs
    overview: t({ en: 'Overview', ko: '개요' }),
    schedules: t({ en: 'Schedules', ko: '스케줄' }),
    webhooks: t({ en: 'Webhooks', ko: '웹훅' }),
    composite: t({ en: 'Composite', ko: '복합' }),

    // Stats cards
    totalSchedules: t({ en: 'Total Schedules', ko: '전체 스케줄' }),
    dataChangeTriggers: t({ en: 'Data Change Triggers', ko: '데이터 변경 트리거' }),
    webhookTriggers: t({ en: 'Webhook Triggers', ko: '웹훅 트리거' }),
    compositeTriggers: t({ en: 'Composite Triggers', ko: '복합 트리거' }),
    checksLastHour: t({ en: 'Checks (Last Hour)', ko: '확인 (최근 1시간)' }),
    triggersLastHour: t({ en: 'Triggers (Last Hour)', ko: '트리거 (최근 1시간)' }),

    // Checker status
    checkerStatus: t({ en: 'Checker Status', ko: '체커 상태' }),
    checkerRunning: t({ en: 'Running', ko: '실행 중' }),
    checkerStopped: t({ en: 'Stopped', ko: '중지됨' }),
    lastCheckerRun: t({ en: 'Last Checker Run', ko: '마지막 체커 실행' }),
    checkerInterval: t({ en: 'Check Interval', ko: '확인 간격' }),
    nextScheduledCheck: t({ en: 'Next Scheduled Check', ko: '다음 예정 확인' }),

    // Trigger types
    triggerType: t({ en: 'Trigger Type', ko: '트리거 유형' }),
    cron: t({ en: 'Cron', ko: 'Cron' }),
    interval: t({ en: 'Interval', ko: '간격' }),
    dataChange: t({ en: 'Data Change', ko: '데이터 변경' }),
    compositeType: t({ en: 'Composite', ko: '복합' }),
    event: t({ en: 'Event', ko: '이벤트' }),
    manual: t({ en: 'Manual', ko: '수동' }),
    webhook: t({ en: 'Webhook', ko: '웹훅' }),

    // Table columns
    scheduleName: t({ en: 'Schedule Name', ko: '스케줄 이름' }),
    lastCheck: t({ en: 'Last Check', ko: '마지막 확인' }),
    lastTriggered: t({ en: 'Last Triggered', ko: '마지막 트리거' }),
    nextCheck: t({ en: 'Next Check', ko: '다음 확인' }),
    checkCount: t({ en: 'Checks', ko: '확인 횟수' }),
    triggerCount: t({ en: 'Triggers', ko: '트리거 횟수' }),
    priority: t({ en: 'Priority', ko: '우선순위' }),
    cooldown: t({ en: 'Cooldown', ko: '쿨다운' }),
    cooldownRemaining: t({ en: 'Cooldown Remaining', ko: '남은 쿨다운' }),

    // Status
    status: t({ en: 'Status', ko: '상태' }),
    dueForCheck: t({ en: 'Due for Check', ko: '확인 대기' }),
    inCooldown: t({ en: 'In Cooldown', ko: '쿨다운 중' }),
    ready: t({ en: 'Ready', ko: '준비됨' }),
    disabled: t({ en: 'Disabled', ko: '비활성화' }),

    // Evaluation result
    lastEvaluation: t({ en: 'Last Evaluation', ko: '마지막 평가' }),
    shouldTrigger: t({ en: 'Should Trigger', ko: '트리거 여부' }),
    reason: t({ en: 'Reason', ko: '사유' }),
    details: t({ en: 'Details', ko: '상세' }),

    // Data change trigger config
    changeThreshold: t({ en: 'Change Threshold', ko: '변경 임계값' }),
    monitoredMetrics: t({ en: 'Monitored Metrics', ko: '모니터링 메트릭' }),
    baselineProfile: t({ en: 'Baseline Profile', ko: '기준 프로파일' }),
    checkIntervalMinutes: t({ en: 'Check Interval (min)', ko: '확인 간격 (분)' }),
    cooldownMinutes: t({ en: 'Cooldown (min)', ko: '쿨다운 (분)' }),
    autoProfile: t({ en: 'Auto Profile', ko: '자동 프로파일' }),

    // Composite trigger
    operator: t({ en: 'Operator', ko: '연산자' }),
    andOperator: t({ en: 'AND (All conditions)', ko: 'AND (모든 조건)' }),
    orOperator: t({ en: 'OR (Any condition)', ko: 'OR (조건 중 하나)' }),
    nestedTriggers: t({ en: 'Nested Triggers', ko: '중첩 트리거' }),
    addTrigger: t({ en: 'Add Trigger', ko: '트리거 추가' }),
    removeTrigger: t({ en: 'Remove Trigger', ko: '트리거 제거' }),

    // Webhook
    webhookEndpoint: t({ en: 'Webhook Endpoint', ko: '웹훅 엔드포인트' }),
    webhookSecret: t({ en: 'Webhook Secret', ko: '웹훅 시크릿' }),
    allowedSources: t({ en: 'Allowed Sources', ko: '허용된 소스' }),
    requireSignature: t({ en: 'Require Signature', ko: '서명 필요' }),
    testWebhook: t({ en: 'Test Webhook', ko: '웹훅 테스트' }),
    webhookUrl: t({ en: 'Webhook URL', ko: '웹훅 URL' }),
    copyWebhookUrl: t({ en: 'Copy Webhook URL', ko: '웹훅 URL 복사' }),

    // Actions
    refresh: t({ en: 'Refresh', ko: '새로고침' }),
    viewDetails: t({ en: 'View Details', ko: '상세 보기' }),
    editTrigger: t({ en: 'Edit Trigger', ko: '트리거 편집' }),
    forceCheck: t({ en: 'Force Check', ko: '강제 확인' }),
    resetCooldown: t({ en: 'Reset Cooldown', ko: '쿨다운 초기화' }),

    // Empty states
    noTriggers: t({ en: 'No triggers configured', ko: '설정된 트리거가 없습니다' }),
    noTriggersDesc: t({
      en: 'Data change and composite triggers will appear here when configured in schedules',
      ko: '스케줄에서 설정된 데이터 변경 및 복합 트리거가 여기에 표시됩니다',
    }),
    noWebhooks: t({ en: 'No webhook triggers', ko: '웹훅 트리거 없음' }),
    noWebhooksDesc: t({
      en: 'Create a schedule with webhook trigger to enable external triggers',
      ko: '외부 트리거를 활성화하려면 웹훅 트리거가 있는 스케줄을 생성하세요',
    }),

    // Toasts
    refreshed: t({ en: 'Trigger status refreshed', ko: '트리거 상태 새로고침됨' }),
    refreshFailed: t({ en: 'Failed to refresh', ko: '새로고침 실패' }),
    webhookSent: t({ en: 'Webhook sent successfully', ko: '웹훅 전송 성공' }),
    webhookFailed: t({ en: 'Webhook failed', ko: '웹훅 실패' }),
    urlCopied: t({ en: 'URL copied to clipboard', ko: 'URL이 클립보드에 복사됨' }),

    // Time formats
    seconds: t({ en: 'seconds', ko: '초' }),
    minutes: t({ en: 'minutes', ko: '분' }),
    never: t({ en: 'Never', ko: '없음' }),
    ago: t({ en: 'ago', ko: '전' }),
  },
} satisfies Dictionary

export default triggersContent
