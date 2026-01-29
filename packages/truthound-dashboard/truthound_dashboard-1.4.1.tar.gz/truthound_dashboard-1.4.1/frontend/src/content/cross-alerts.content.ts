/**
 * Cross-alerts translations.
 *
 * Contains translations for cross-feature integration between
 * Anomaly Detection and Drift Monitoring.
 */
import { t, type Dictionary } from 'intlayer'

const crossAlertsContent = {
  key: 'crossAlerts',
  content: {
    title: t({ en: 'Cross-Alert Correlations', ko: '교차 알림 상관관계' }),
    subtitle: t({
      en: 'Correlations between anomaly and drift alerts',
      ko: '이상 탐지와 드리프트 알림 간의 상관관계',
    }),

    // Sections
    sections: {
      relatedDriftAlerts: t({ en: 'Related Drift Alerts', ko: '관련 드리프트 알림' }),
      relatedAnomalyAlerts: t({ en: 'Related Anomaly Alerts', ko: '관련 이상 탐지 알림' }),
      correlations: t({ en: 'Alert Correlations', ko: '알림 상관관계' }),
      autoTriggerConfig: t({ en: 'Auto-Trigger Configuration', ko: '자동 트리거 설정' }),
      recentEvents: t({ en: 'Recent Events', ko: '최근 이벤트' }),
    },

    // Correlation strength
    strength: {
      strong: t({ en: 'Strong', ko: '강함' }),
      moderate: t({ en: 'Moderate', ko: '중간' }),
      weak: t({ en: 'Weak', ko: '약함' }),
      none: t({ en: 'None', ko: '없음' }),
    },

    // Alert types
    alertType: {
      anomaly: t({ en: 'Anomaly', ko: '이상' }),
      drift: t({ en: 'Drift', ko: '드리프트' }),
    },

    // Labels
    labels: {
      sourceId: t({ en: 'Source', ko: '소스' }),
      confidence: t({ en: 'Confidence', ko: '신뢰도' }),
      timeDelta: t({ en: 'Time Difference', ko: '시간 차이' }),
      commonColumns: t({ en: 'Common Columns', ko: '공통 컬럼' }),
      suggestedAction: t({ en: 'Suggested Action', ko: '권장 조치' }),
      anomalyRate: t({ en: 'Anomaly Rate', ko: '이상 비율' }),
      anomalyCount: t({ en: 'Anomaly Count', ko: '이상 수' }),
      driftPercentage: t({ en: 'Drift Percentage', ko: '드리프트 비율' }),
      driftedColumns: t({ en: 'Drifted Columns', ko: '드리프트 컬럼' }),
      createdAt: t({ en: 'Created', ko: '생성일' }),
      correlationStrength: t({ en: 'Correlation', ko: '상관관계' }),
    },

    // Auto-trigger config
    config: {
      enabled: t({ en: 'Auto-Trigger Enabled', ko: '자동 트리거 활성화' }),
      triggerDriftOnAnomaly: t({
        en: 'Trigger drift check on anomaly spike',
        ko: '이상 급증 시 드리프트 검사 트리거',
      }),
      triggerAnomalyOnDrift: t({
        en: 'Trigger anomaly check on drift detection',
        ko: '드리프트 감지 시 이상 검사 트리거',
      }),
      notifyOnCorrelation: t({
        en: 'Notify when correlation detected',
        ko: '상관관계 감지 시 알림',
      }),
      cooldownSeconds: t({ en: 'Cooldown (seconds)', ko: '쿨다운 (초)' }),

      // Thresholds
      thresholds: {
        title: t({ en: 'Trigger Thresholds', ko: '트리거 임계값' }),
        anomalyRateThreshold: t({ en: 'Anomaly Rate Threshold', ko: '이상 비율 임계값' }),
        anomalyCountThreshold: t({ en: 'Anomaly Count Threshold', ko: '이상 수 임계값' }),
        driftPercentageThreshold: t({
          en: 'Drift Percentage Threshold',
          ko: '드리프트 비율 임계값',
        }),
        driftColumnsThreshold: t({
          en: 'Drifted Columns Threshold',
          ko: '드리프트 컬럼 수 임계값',
        }),
      },
    },

    // Events
    events: {
      triggerType: {
        anomaly_to_drift: t({ en: 'Anomaly -> Drift', ko: '이상 -> 드리프트' }),
        drift_to_anomaly: t({ en: 'Drift -> Anomaly', ko: '드리프트 -> 이상' }),
        bidirectional: t({ en: 'Bidirectional', ko: '양방향' }),
      },
      status: {
        pending: t({ en: 'Pending', ko: '대기 중' }),
        running: t({ en: 'Running', ko: '실행 중' }),
        completed: t({ en: 'Completed', ko: '완료' }),
        failed: t({ en: 'Failed', ko: '실패' }),
        skipped: t({ en: 'Skipped', ko: '건너뜀' }),
      },
      correlationFound: t({ en: 'Correlation Found', ko: '상관관계 발견' }),
      noCorrelation: t({ en: 'No Correlation', ko: '상관관계 없음' }),
    },

    // Stats
    stats: {
      totalCorrelations: t({ en: 'Total Correlations', ko: '전체 상관관계' }),
      strongCorrelations: t({ en: 'Strong', ko: '강함' }),
      recentCorrelations: t({ en: 'Last 24h', ko: '최근 24시간' }),
      recentTriggers: t({ en: 'Auto-Triggers (24h)', ko: '자동 트리거 (24시간)' }),
    },

    // Actions
    actions: {
      viewDetails: t({ en: 'View Details', ko: '상세 보기' }),
      goToAnomaly: t({ en: 'Go to Anomaly Detection', ko: '이상 탐지로 이동' }),
      goToDrift: t({ en: 'Go to Drift Monitoring', ko: '드리프트 모니터링으로 이동' }),
      refresh: t({ en: 'Refresh', ko: '새로고침' }),
      configure: t({ en: 'Configure', ko: '설정' }),
      triggerNow: t({ en: 'Trigger Now', ko: '지금 트리거' }),
      saveConfig: t({ en: 'Save Configuration', ko: '설정 저장' }),
    },

    // Messages
    messages: {
      configSaved: t({ en: 'Configuration saved', ko: '설정이 저장되었습니다' }),
      triggerStarted: t({ en: 'Trigger started', ko: '트리거가 시작되었습니다' }),
      triggerCompleted: t({ en: 'Trigger completed', ko: '트리거가 완료되었습니다' }),
      triggerFailed: t({ en: 'Trigger failed', ko: '트리거 실패' }),
      noCorrelationsFound: t({ en: 'No correlations found', ko: '상관관계를 찾을 수 없습니다' }),
      loadingCorrelations: t({ en: 'Loading correlations...', ko: '상관관계 로딩 중...' }),
      errorLoadingCorrelations: t({
        en: 'Failed to load correlations',
        ko: '상관관계 로드 실패',
      }),
    },

    // Empty states
    empty: {
      noCorrelations: t({ en: 'No correlations yet', ko: '상관관계 없음' }),
      noCorrelationsDesc: t({
        en: 'Correlations will appear when both anomaly and drift alerts occur for the same source',
        ko: '동일 소스에서 이상 탐지와 드리프트 알림이 발생하면 상관관계가 표시됩니다',
      }),
      noRelatedAlerts: t({ en: 'No related alerts', ko: '관련 알림 없음' }),
      noRelatedAlertsDesc: t({
        en: 'No correlated alerts found for this source in the selected time window',
        ko: '선택한 기간 내에 이 소스에 대한 연관된 알림이 없습니다',
      }),
      noEvents: t({ en: 'No auto-trigger events', ko: '자동 트리거 이벤트 없음' }),
      noEventsDesc: t({
        en: 'Auto-trigger events will appear here when conditions are met',
        ko: '조건이 충족되면 자동 트리거 이벤트가 여기에 표시됩니다',
      }),
    },

    // Time labels
    time: {
      seconds: t({ en: 'seconds', ko: '초' }),
      minutes: t({ en: 'minutes', ko: '분' }),
      hours: t({ en: 'hours', ko: '시간' }),
      ago: t({ en: 'ago', ko: '전' }),
      apart: t({ en: 'apart', ko: '차이' }),
    },
  },
} satisfies Dictionary

export default crossAlertsContent
