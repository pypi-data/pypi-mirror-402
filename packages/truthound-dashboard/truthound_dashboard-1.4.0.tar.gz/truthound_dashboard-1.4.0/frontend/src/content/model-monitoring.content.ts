/**
 * Model Monitoring content translations.
 *
 * Contains translations for ML model monitoring features including
 * performance metrics, drift detection, and alerting.
 */
import { t, type Dictionary } from 'intlayer'

const modelMonitoringContent = {
  key: 'modelMonitoring',
  content: {
    title: t({ en: 'Model Monitoring', ko: '모델 모니터링' }),
    subtitle: t({
      en: 'Monitor ML model performance, drift, and data quality',
      ko: 'ML 모델 성능, 드리프트, 데이터 품질 모니터링',
    }),

    // Tabs
    tabs: {
      overview: t({ en: 'Overview', ko: '개요' }),
      models: t({ en: 'Models', ko: '모델' }),
      metrics: t({ en: 'Metrics', ko: '메트릭' }),
      alerts: t({ en: 'Alerts', ko: '알림' }),
      rules: t({ en: 'Alert Rules', ko: '알림 규칙' }),
      handlers: t({ en: 'Handlers', ko: '핸들러' }),
    },

    // Overview stats
    overview: {
      totalModels: t({ en: 'Total Models', ko: '전체 모델' }),
      activeModels: t({ en: 'Active Models', ko: '활성 모델' }),
      degradedModels: t({ en: 'Degraded', ko: '성능 저하' }),
      predictions24h: t({ en: 'Predictions (24h)', ko: '예측 (24시간)' }),
      activeAlerts: t({ en: 'Active Alerts', ko: '활성 알림' }),
      modelsWithDrift: t({ en: 'Models with Drift', ko: '드리프트 감지' }),
      avgLatency: t({ en: 'Avg Latency', ko: '평균 지연' }),
    },

    // Model management
    models: {
      title: t({ en: 'Registered Models', ko: '등록된 모델' }),
      registerModel: t({ en: 'Register Model', ko: '모델 등록' }),
      editModel: t({ en: 'Edit Model', ko: '모델 편집' }),
      noModels: t({
        en: 'No models registered yet',
        ko: '등록된 모델이 없습니다',
      }),
      name: t({ en: 'Model Name', ko: '모델 이름' }),
      version: t({ en: 'Version', ko: '버전' }),
      status: t({ en: 'Status', ko: '상태' }),
      predictions: t({ en: 'Predictions', ko: '예측 수' }),
      lastPrediction: t({ en: 'Last Prediction', ko: '마지막 예측' }),
      driftScore: t({ en: 'Drift Score', ko: '드리프트 점수' }),
      healthScore: t({ en: 'Health Score', ko: '헬스 점수' }),
    },

    // Model status
    status: {
      active: t({ en: 'Active', ko: '활성' }),
      paused: t({ en: 'Paused', ko: '일시중지' }),
      degraded: t({ en: 'Degraded', ko: '성능 저하' }),
      error: t({ en: 'Error', ko: '오류' }),
    },

    // Model config
    config: {
      title: t({ en: 'Monitoring Configuration', ko: '모니터링 설정' }),
      enableDrift: t({ en: 'Enable Drift Detection', ko: '드리프트 감지 활성화' }),
      enableQuality: t({ en: 'Enable Quality Metrics', ko: '품질 메트릭 활성화' }),
      enablePerformance: t({ en: 'Enable Performance Metrics', ko: '성능 메트릭 활성화' }),
      sampleRate: t({ en: 'Sample Rate', ko: '샘플링 비율' }),
      driftThreshold: t({ en: 'Drift Threshold', ko: '드리프트 임계값' }),
      driftWindowSize: t({ en: 'Drift Window Size', ko: '드리프트 윈도우 크기' }),
    },

    // Metrics
    metrics: {
      title: t({ en: 'Model Metrics', ko: '모델 메트릭' }),
      selectModel: t({ en: 'Select Model', ko: '모델 선택' }),
      timeRange: t({ en: 'Time Range', ko: '시간 범위' }),
      latency: t({ en: 'Latency', ko: '지연 시간' }),
      throughput: t({ en: 'Throughput', ko: '처리량' }),
      errorRate: t({ en: 'Error Rate', ko: '오류율' }),
      nullRate: t({ en: 'Null Rate', ko: 'Null 비율' }),
      typeViolation: t({ en: 'Type Violations', ko: '타입 위반' }),
      driftScore: t({ en: 'Drift Score', ko: '드리프트 점수' }),
      // Stats
      min: t({ en: 'Min', ko: '최소' }),
      max: t({ en: 'Max', ko: '최대' }),
      avg: t({ en: 'Avg', ko: '평균' }),
      p50: t({ en: 'P50', ko: 'P50' }),
      p95: t({ en: 'P95', ko: 'P95' }),
      p99: t({ en: 'P99', ko: 'P99' }),
    },

    // Time ranges
    timeRanges: {
      '1h': t({ en: 'Last 1 Hour', ko: '최근 1시간' }),
      '6h': t({ en: 'Last 6 Hours', ko: '최근 6시간' }),
      '24h': t({ en: 'Last 24 Hours', ko: '최근 24시간' }),
      '7d': t({ en: 'Last 7 Days', ko: '최근 7일' }),
    },

    // Alerts
    alerts: {
      title: t({ en: 'Active Alerts', ko: '활성 알림' }),
      noAlerts: t({
        en: 'No active alerts',
        ko: '활성 알림이 없습니다',
      }),
      acknowledge: t({ en: 'Acknowledge', ko: '확인' }),
      resolve: t({ en: 'Resolve', ko: '해결' }),
      severity: t({ en: 'Severity', ko: '심각도' }),
      message: t({ en: 'Message', ko: '메시지' }),
      triggeredAt: t({ en: 'Triggered At', ko: '발생 시간' }),
      acknowledgedBy: t({ en: 'Acknowledged By', ko: '확인자' }),
    },

    // Alert severity
    severity: {
      critical: t({ en: 'Critical', ko: '심각' }),
      warning: t({ en: 'Warning', ko: '경고' }),
      info: t({ en: 'Info', ko: '정보' }),
    },

    // Alert rules
    rules: {
      title: t({ en: 'Alert Rules', ko: '알림 규칙' }),
      addRule: t({ en: 'Add Rule', ko: '규칙 추가' }),
      editRule: t({ en: 'Edit Rule', ko: '규칙 편집' }),
      noRules: t({
        en: 'No alert rules configured',
        ko: '설정된 알림 규칙이 없습니다',
      }),
      ruleType: t({ en: 'Rule Type', ko: '규칙 유형' }),
      triggerCount: t({ en: 'Triggers', ko: '트리거 횟수' }),
      lastTriggered: t({ en: 'Last Triggered', ko: '마지막 트리거' }),
    },

    // Rule types
    ruleTypes: {
      threshold: t({ en: 'Threshold', ko: '임계값' }),
      statistical: t({ en: 'Statistical', ko: '통계적' }),
      trend: t({ en: 'Trend', ko: '추세' }),
    },

    // Threshold rule config
    thresholdConfig: {
      metric: t({ en: 'Metric', ko: '메트릭' }),
      threshold: t({ en: 'Threshold', ko: '임계값' }),
      comparison: t({ en: 'Comparison', ko: '비교 연산' }),
      duration: t({ en: 'Duration (seconds)', ko: '지속 시간 (초)' }),
      gt: t({ en: 'Greater than', ko: '초과' }),
      lt: t({ en: 'Less than', ko: '미만' }),
      gte: t({ en: 'Greater or equal', ko: '이상' }),
      lte: t({ en: 'Less or equal', ko: '이하' }),
      eq: t({ en: 'Equal', ko: '같음' }),
    },

    // Alert handlers
    handlers: {
      title: t({ en: 'Alert Handlers', ko: '알림 핸들러' }),
      addHandler: t({ en: 'Add Handler', ko: '핸들러 추가' }),
      editHandler: t({ en: 'Edit Handler', ko: '핸들러 편집' }),
      noHandlers: t({
        en: 'No handlers configured',
        ko: '설정된 핸들러가 없습니다',
      }),
      handlerType: t({ en: 'Handler Type', ko: '핸들러 유형' }),
      sendCount: t({ en: 'Sent', ko: '전송 수' }),
      failureCount: t({ en: 'Failures', ko: '실패 수' }),
      lastSent: t({ en: 'Last Sent', ko: '마지막 전송' }),
    },

    // Handler types
    handlerTypes: {
      slack: t({ en: 'Slack', ko: 'Slack' }),
      webhook: t({ en: 'Webhook', ko: 'Webhook' }),
      email: t({ en: 'Email', ko: '이메일' }),
    },

    // Handler config
    handlerConfig: {
      webhookUrl: t({ en: 'Webhook URL', ko: 'Webhook URL' }),
      channel: t({ en: 'Channel', ko: '채널' }),
      username: t({ en: 'Username', ko: '사용자명' }),
      url: t({ en: 'URL', ko: 'URL' }),
      method: t({ en: 'HTTP Method', ko: 'HTTP 메서드' }),
      headers: t({ en: 'Custom Headers', ko: '커스텀 헤더' }),
    },

    // Empty states
    empty: {
      noData: t({
        en: 'No data available',
        ko: '데이터가 없습니다',
      }),
      noMetrics: t({
        en: 'No metrics recorded yet',
        ko: '기록된 메트릭이 없습니다',
      }),
    },

    // Messages
    messages: {
      modelRegistered: t({ en: 'Model registered successfully', ko: '모델이 등록되었습니다' }),
      modelUpdated: t({ en: 'Model updated successfully', ko: '모델이 수정되었습니다' }),
      modelDeleted: t({ en: 'Model deleted successfully', ko: '모델이 삭제되었습니다' }),
      ruleCreated: t({ en: 'Alert rule created', ko: '알림 규칙이 생성되었습니다' }),
      ruleUpdated: t({ en: 'Alert rule updated', ko: '알림 규칙이 수정되었습니다' }),
      ruleDeleted: t({ en: 'Alert rule deleted', ko: '알림 규칙이 삭제되었습니다' }),
      handlerCreated: t({ en: 'Handler created', ko: '핸들러가 생성되었습니다' }),
      handlerUpdated: t({ en: 'Handler updated', ko: '핸들러가 수정되었습니다' }),
      handlerDeleted: t({ en: 'Handler deleted', ko: '핸들러가 삭제되었습니다' }),
      alertAcknowledged: t({ en: 'Alert acknowledged', ko: '알림이 확인되었습니다' }),
      alertResolved: t({ en: 'Alert resolved', ko: '알림이 해결되었습니다' }),
    },

    // Errors
    errors: {
      loadFailed: t({ en: 'Failed to load data', ko: '데이터 로드에 실패했습니다' }),
      createFailed: t({ en: 'Failed to create', ko: '생성에 실패했습니다' }),
      updateFailed: t({ en: 'Failed to update', ko: '수정에 실패했습니다' }),
      deleteFailed: t({ en: 'Failed to delete', ko: '삭제에 실패했습니다' }),
    },

    // Confirmations
    confirm: {
      deleteModel: t({
        en: 'Are you sure you want to delete this model? This action cannot be undone.',
        ko: '이 모델을 삭제하시겠습니까? 이 작업은 취소할 수 없습니다.',
      }),
      deleteRule: t({
        en: 'Are you sure you want to delete this rule?',
        ko: '이 규칙을 삭제하시겠습니까?',
      }),
      deleteHandler: t({
        en: 'Are you sure you want to delete this handler?',
        ko: '이 핸들러를 삭제하시겠습니까?',
      }),
    },
  },
} satisfies Dictionary

export default modelMonitoringContent
