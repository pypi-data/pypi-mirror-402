/* eslint-disable */
export default {
  "key": "crossAlerts",
  "content": {
    "nodeType": "translation",
    "translation": {
      "en": {
        "title": "Cross-Alert Correlations",
        "subtitle": "Correlations between anomaly and drift alerts",
        "sections": {
          "relatedDriftAlerts": "Related Drift Alerts",
          "relatedAnomalyAlerts": "Related Anomaly Alerts",
          "correlations": "Alert Correlations",
          "autoTriggerConfig": "Auto-Trigger Configuration",
          "recentEvents": "Recent Events"
        },
        "strength": {
          "strong": "Strong",
          "moderate": "Moderate",
          "weak": "Weak",
          "none": "None"
        },
        "alertType": {
          "anomaly": "Anomaly",
          "drift": "Drift"
        },
        "labels": {
          "sourceId": "Source",
          "confidence": "Confidence",
          "timeDelta": "Time Difference",
          "commonColumns": "Common Columns",
          "suggestedAction": "Suggested Action",
          "anomalyRate": "Anomaly Rate",
          "anomalyCount": "Anomaly Count",
          "driftPercentage": "Drift Percentage",
          "driftedColumns": "Drifted Columns",
          "createdAt": "Created",
          "correlationStrength": "Correlation"
        },
        "config": {
          "enabled": "Auto-Trigger Enabled",
          "triggerDriftOnAnomaly": "Trigger drift check on anomaly spike",
          "triggerAnomalyOnDrift": "Trigger anomaly check on drift detection",
          "notifyOnCorrelation": "Notify when correlation detected",
          "cooldownSeconds": "Cooldown (seconds)",
          "thresholds": {
            "title": "Trigger Thresholds",
            "anomalyRateThreshold": "Anomaly Rate Threshold",
            "anomalyCountThreshold": "Anomaly Count Threshold",
            "driftPercentageThreshold": "Drift Percentage Threshold",
            "driftColumnsThreshold": "Drifted Columns Threshold"
          }
        },
        "events": {
          "triggerType": {
            "anomaly_to_drift": "Anomaly -> Drift",
            "drift_to_anomaly": "Drift -> Anomaly",
            "bidirectional": "Bidirectional"
          },
          "status": {
            "pending": "Pending",
            "running": "Running",
            "completed": "Completed",
            "failed": "Failed",
            "skipped": "Skipped"
          },
          "correlationFound": "Correlation Found",
          "noCorrelation": "No Correlation"
        },
        "stats": {
          "totalCorrelations": "Total Correlations",
          "strongCorrelations": "Strong",
          "recentCorrelations": "Last 24h",
          "recentTriggers": "Auto-Triggers (24h)"
        },
        "actions": {
          "viewDetails": "View Details",
          "goToAnomaly": "Go to Anomaly Detection",
          "goToDrift": "Go to Drift Monitoring",
          "refresh": "Refresh",
          "configure": "Configure",
          "triggerNow": "Trigger Now",
          "saveConfig": "Save Configuration"
        },
        "messages": {
          "configSaved": "Configuration saved",
          "triggerStarted": "Trigger started",
          "triggerCompleted": "Trigger completed",
          "triggerFailed": "Trigger failed",
          "noCorrelationsFound": "No correlations found",
          "loadingCorrelations": "Loading correlations...",
          "errorLoadingCorrelations": "Failed to load correlations"
        },
        "empty": {
          "noCorrelations": "No correlations yet",
          "noCorrelationsDesc": "Correlations will appear when both anomaly and drift alerts occur for the same source",
          "noRelatedAlerts": "No related alerts",
          "noRelatedAlertsDesc": "No correlated alerts found for this source in the selected time window",
          "noEvents": "No auto-trigger events",
          "noEventsDesc": "Auto-trigger events will appear here when conditions are met"
        },
        "time": {
          "seconds": "seconds",
          "minutes": "minutes",
          "hours": "hours",
          "ago": "ago",
          "apart": "apart"
        }
      },
      "ko": {
        "title": "교차 알림 상관관계",
        "subtitle": "이상 탐지와 드리프트 알림 간의 상관관계",
        "sections": {
          "relatedDriftAlerts": "관련 드리프트 알림",
          "relatedAnomalyAlerts": "관련 이상 탐지 알림",
          "correlations": "알림 상관관계",
          "autoTriggerConfig": "자동 트리거 설정",
          "recentEvents": "최근 이벤트"
        },
        "strength": {
          "strong": "강함",
          "moderate": "중간",
          "weak": "약함",
          "none": "없음"
        },
        "alertType": {
          "anomaly": "이상",
          "drift": "드리프트"
        },
        "labels": {
          "sourceId": "소스",
          "confidence": "신뢰도",
          "timeDelta": "시간 차이",
          "commonColumns": "공통 컬럼",
          "suggestedAction": "권장 조치",
          "anomalyRate": "이상 비율",
          "anomalyCount": "이상 수",
          "driftPercentage": "드리프트 비율",
          "driftedColumns": "드리프트 컬럼",
          "createdAt": "생성일",
          "correlationStrength": "상관관계"
        },
        "config": {
          "enabled": "자동 트리거 활성화",
          "triggerDriftOnAnomaly": "이상 급증 시 드리프트 검사 트리거",
          "triggerAnomalyOnDrift": "드리프트 감지 시 이상 검사 트리거",
          "notifyOnCorrelation": "상관관계 감지 시 알림",
          "cooldownSeconds": "쿨다운 (초)",
          "thresholds": {
            "title": "트리거 임계값",
            "anomalyRateThreshold": "이상 비율 임계값",
            "anomalyCountThreshold": "이상 수 임계값",
            "driftPercentageThreshold": "드리프트 비율 임계값",
            "driftColumnsThreshold": "드리프트 컬럼 수 임계값"
          }
        },
        "events": {
          "triggerType": {
            "anomaly_to_drift": "이상 -> 드리프트",
            "drift_to_anomaly": "드리프트 -> 이상",
            "bidirectional": "양방향"
          },
          "status": {
            "pending": "대기 중",
            "running": "실행 중",
            "completed": "완료",
            "failed": "실패",
            "skipped": "건너뜀"
          },
          "correlationFound": "상관관계 발견",
          "noCorrelation": "상관관계 없음"
        },
        "stats": {
          "totalCorrelations": "전체 상관관계",
          "strongCorrelations": "강함",
          "recentCorrelations": "최근 24시간",
          "recentTriggers": "자동 트리거 (24시간)"
        },
        "actions": {
          "viewDetails": "상세 보기",
          "goToAnomaly": "이상 탐지로 이동",
          "goToDrift": "드리프트 모니터링으로 이동",
          "refresh": "새로고침",
          "configure": "설정",
          "triggerNow": "지금 트리거",
          "saveConfig": "설정 저장"
        },
        "messages": {
          "configSaved": "설정이 저장되었습니다",
          "triggerStarted": "트리거가 시작되었습니다",
          "triggerCompleted": "트리거가 완료되었습니다",
          "triggerFailed": "트리거 실패",
          "noCorrelationsFound": "상관관계를 찾을 수 없습니다",
          "loadingCorrelations": "상관관계 로딩 중...",
          "errorLoadingCorrelations": "상관관계 로드 실패"
        },
        "empty": {
          "noCorrelations": "상관관계 없음",
          "noCorrelationsDesc": "동일 소스에서 이상 탐지와 드리프트 알림이 발생하면 상관관계가 표시됩니다",
          "noRelatedAlerts": "관련 알림 없음",
          "noRelatedAlertsDesc": "선택한 기간 내에 이 소스에 대한 연관된 알림이 없습니다",
          "noEvents": "자동 트리거 이벤트 없음",
          "noEventsDesc": "조건이 충족되면 자동 트리거 이벤트가 여기에 표시됩니다"
        },
        "time": {
          "seconds": "초",
          "minutes": "분",
          "hours": "시간",
          "ago": "전",
          "apart": "차이"
        }
      }
    }
  },
  "localIds": [
    "crossAlerts::local::src/content/cross-alerts.content.ts"
  ]
} as const;
