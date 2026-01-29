/* eslint-disable */
export default {
  "key": "modelMonitoring",
  "content": {
    "nodeType": "translation",
    "translation": {
      "en": {
        "title": "Model Monitoring",
        "subtitle": "Monitor ML model performance, drift, and data quality",
        "tabs": {
          "overview": "Overview",
          "models": "Models",
          "metrics": "Metrics",
          "alerts": "Alerts",
          "rules": "Alert Rules",
          "handlers": "Handlers"
        },
        "overview": {
          "totalModels": "Total Models",
          "activeModels": "Active Models",
          "degradedModels": "Degraded",
          "predictions24h": "Predictions (24h)",
          "activeAlerts": "Active Alerts",
          "modelsWithDrift": "Models with Drift",
          "avgLatency": "Avg Latency"
        },
        "models": {
          "title": "Registered Models",
          "registerModel": "Register Model",
          "editModel": "Edit Model",
          "noModels": "No models registered yet",
          "name": "Model Name",
          "version": "Version",
          "status": "Status",
          "predictions": "Predictions",
          "lastPrediction": "Last Prediction",
          "driftScore": "Drift Score",
          "healthScore": "Health Score"
        },
        "status": {
          "active": "Active",
          "paused": "Paused",
          "degraded": "Degraded",
          "error": "Error"
        },
        "config": {
          "title": "Monitoring Configuration",
          "enableDrift": "Enable Drift Detection",
          "enableQuality": "Enable Quality Metrics",
          "enablePerformance": "Enable Performance Metrics",
          "sampleRate": "Sample Rate",
          "driftThreshold": "Drift Threshold",
          "driftWindowSize": "Drift Window Size"
        },
        "metrics": {
          "title": "Model Metrics",
          "selectModel": "Select Model",
          "timeRange": "Time Range",
          "latency": "Latency",
          "throughput": "Throughput",
          "errorRate": "Error Rate",
          "nullRate": "Null Rate",
          "typeViolation": "Type Violations",
          "driftScore": "Drift Score",
          "min": "Min",
          "max": "Max",
          "avg": "Avg",
          "p50": "P50",
          "p95": "P95",
          "p99": "P99"
        },
        "timeRanges": {
          "1h": "Last 1 Hour",
          "6h": "Last 6 Hours",
          "24h": "Last 24 Hours",
          "7d": "Last 7 Days"
        },
        "alerts": {
          "title": "Active Alerts",
          "noAlerts": "No active alerts",
          "acknowledge": "Acknowledge",
          "resolve": "Resolve",
          "severity": "Severity",
          "message": "Message",
          "triggeredAt": "Triggered At",
          "acknowledgedBy": "Acknowledged By"
        },
        "severity": {
          "critical": "Critical",
          "warning": "Warning",
          "info": "Info"
        },
        "rules": {
          "title": "Alert Rules",
          "addRule": "Add Rule",
          "editRule": "Edit Rule",
          "noRules": "No alert rules configured",
          "ruleType": "Rule Type",
          "triggerCount": "Triggers",
          "lastTriggered": "Last Triggered"
        },
        "ruleTypes": {
          "threshold": "Threshold",
          "statistical": "Statistical",
          "trend": "Trend"
        },
        "thresholdConfig": {
          "metric": "Metric",
          "threshold": "Threshold",
          "comparison": "Comparison",
          "duration": "Duration (seconds)",
          "gt": "Greater than",
          "lt": "Less than",
          "gte": "Greater or equal",
          "lte": "Less or equal",
          "eq": "Equal"
        },
        "handlers": {
          "title": "Alert Handlers",
          "addHandler": "Add Handler",
          "editHandler": "Edit Handler",
          "noHandlers": "No handlers configured",
          "handlerType": "Handler Type",
          "sendCount": "Sent",
          "failureCount": "Failures",
          "lastSent": "Last Sent"
        },
        "handlerTypes": {
          "slack": "Slack",
          "webhook": "Webhook",
          "email": "Email"
        },
        "handlerConfig": {
          "webhookUrl": "Webhook URL",
          "channel": "Channel",
          "username": "Username",
          "url": "URL",
          "method": "HTTP Method",
          "headers": "Custom Headers"
        },
        "empty": {
          "noData": "No data available",
          "noMetrics": "No metrics recorded yet"
        },
        "messages": {
          "modelRegistered": "Model registered successfully",
          "modelUpdated": "Model updated successfully",
          "modelDeleted": "Model deleted successfully",
          "ruleCreated": "Alert rule created",
          "ruleUpdated": "Alert rule updated",
          "ruleDeleted": "Alert rule deleted",
          "handlerCreated": "Handler created",
          "handlerUpdated": "Handler updated",
          "handlerDeleted": "Handler deleted",
          "alertAcknowledged": "Alert acknowledged",
          "alertResolved": "Alert resolved"
        },
        "errors": {
          "loadFailed": "Failed to load data",
          "createFailed": "Failed to create",
          "updateFailed": "Failed to update",
          "deleteFailed": "Failed to delete"
        },
        "confirm": {
          "deleteModel": "Are you sure you want to delete this model? This action cannot be undone.",
          "deleteRule": "Are you sure you want to delete this rule?",
          "deleteHandler": "Are you sure you want to delete this handler?"
        }
      },
      "ko": {
        "title": "모델 모니터링",
        "subtitle": "ML 모델 성능, 드리프트, 데이터 품질 모니터링",
        "tabs": {
          "overview": "개요",
          "models": "모델",
          "metrics": "메트릭",
          "alerts": "알림",
          "rules": "알림 규칙",
          "handlers": "핸들러"
        },
        "overview": {
          "totalModels": "전체 모델",
          "activeModels": "활성 모델",
          "degradedModels": "성능 저하",
          "predictions24h": "예측 (24시간)",
          "activeAlerts": "활성 알림",
          "modelsWithDrift": "드리프트 감지",
          "avgLatency": "평균 지연"
        },
        "models": {
          "title": "등록된 모델",
          "registerModel": "모델 등록",
          "editModel": "모델 편집",
          "noModels": "등록된 모델이 없습니다",
          "name": "모델 이름",
          "version": "버전",
          "status": "상태",
          "predictions": "예측 수",
          "lastPrediction": "마지막 예측",
          "driftScore": "드리프트 점수",
          "healthScore": "헬스 점수"
        },
        "status": {
          "active": "활성",
          "paused": "일시중지",
          "degraded": "성능 저하",
          "error": "오류"
        },
        "config": {
          "title": "모니터링 설정",
          "enableDrift": "드리프트 감지 활성화",
          "enableQuality": "품질 메트릭 활성화",
          "enablePerformance": "성능 메트릭 활성화",
          "sampleRate": "샘플링 비율",
          "driftThreshold": "드리프트 임계값",
          "driftWindowSize": "드리프트 윈도우 크기"
        },
        "metrics": {
          "title": "모델 메트릭",
          "selectModel": "모델 선택",
          "timeRange": "시간 범위",
          "latency": "지연 시간",
          "throughput": "처리량",
          "errorRate": "오류율",
          "nullRate": "Null 비율",
          "typeViolation": "타입 위반",
          "driftScore": "드리프트 점수",
          "min": "최소",
          "max": "최대",
          "avg": "평균",
          "p50": "P50",
          "p95": "P95",
          "p99": "P99"
        },
        "timeRanges": {
          "1h": "최근 1시간",
          "6h": "최근 6시간",
          "24h": "최근 24시간",
          "7d": "최근 7일"
        },
        "alerts": {
          "title": "활성 알림",
          "noAlerts": "활성 알림이 없습니다",
          "acknowledge": "확인",
          "resolve": "해결",
          "severity": "심각도",
          "message": "메시지",
          "triggeredAt": "발생 시간",
          "acknowledgedBy": "확인자"
        },
        "severity": {
          "critical": "심각",
          "warning": "경고",
          "info": "정보"
        },
        "rules": {
          "title": "알림 규칙",
          "addRule": "규칙 추가",
          "editRule": "규칙 편집",
          "noRules": "설정된 알림 규칙이 없습니다",
          "ruleType": "규칙 유형",
          "triggerCount": "트리거 횟수",
          "lastTriggered": "마지막 트리거"
        },
        "ruleTypes": {
          "threshold": "임계값",
          "statistical": "통계적",
          "trend": "추세"
        },
        "thresholdConfig": {
          "metric": "메트릭",
          "threshold": "임계값",
          "comparison": "비교 연산",
          "duration": "지속 시간 (초)",
          "gt": "초과",
          "lt": "미만",
          "gte": "이상",
          "lte": "이하",
          "eq": "같음"
        },
        "handlers": {
          "title": "알림 핸들러",
          "addHandler": "핸들러 추가",
          "editHandler": "핸들러 편집",
          "noHandlers": "설정된 핸들러가 없습니다",
          "handlerType": "핸들러 유형",
          "sendCount": "전송 수",
          "failureCount": "실패 수",
          "lastSent": "마지막 전송"
        },
        "handlerTypes": {
          "slack": "Slack",
          "webhook": "Webhook",
          "email": "이메일"
        },
        "handlerConfig": {
          "webhookUrl": "Webhook URL",
          "channel": "채널",
          "username": "사용자명",
          "url": "URL",
          "method": "HTTP 메서드",
          "headers": "커스텀 헤더"
        },
        "empty": {
          "noData": "데이터가 없습니다",
          "noMetrics": "기록된 메트릭이 없습니다"
        },
        "messages": {
          "modelRegistered": "모델이 등록되었습니다",
          "modelUpdated": "모델이 수정되었습니다",
          "modelDeleted": "모델이 삭제되었습니다",
          "ruleCreated": "알림 규칙이 생성되었습니다",
          "ruleUpdated": "알림 규칙이 수정되었습니다",
          "ruleDeleted": "알림 규칙이 삭제되었습니다",
          "handlerCreated": "핸들러가 생성되었습니다",
          "handlerUpdated": "핸들러가 수정되었습니다",
          "handlerDeleted": "핸들러가 삭제되었습니다",
          "alertAcknowledged": "알림이 확인되었습니다",
          "alertResolved": "알림이 해결되었습니다"
        },
        "errors": {
          "loadFailed": "데이터 로드에 실패했습니다",
          "createFailed": "생성에 실패했습니다",
          "updateFailed": "수정에 실패했습니다",
          "deleteFailed": "삭제에 실패했습니다"
        },
        "confirm": {
          "deleteModel": "이 모델을 삭제하시겠습니까? 이 작업은 취소할 수 없습니다.",
          "deleteRule": "이 규칙을 삭제하시겠습니까?",
          "deleteHandler": "이 핸들러를 삭제하시겠습니까?"
        }
      }
    }
  },
  "localIds": [
    "modelMonitoring::local::src/content/model-monitoring.content.ts"
  ]
} as const;
