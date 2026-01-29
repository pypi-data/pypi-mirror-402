/* eslint-disable */
export default {
  "key": "notifications",
  "content": {
    "nodeType": "translation",
    "translation": {
      "en": {
        "title": "Notifications",
        "subtitle": "Configure notification channels and rules",
        "channels": "Channels",
        "rules": "Rules",
        "logs": "Logs",
        "addChannel": "Add Channel",
        "addRule": "Add Rule",
        "editChannel": "Edit Channel",
        "editRule": "Edit Rule",
        "testChannel": "Test",
        "noChannels": "No notification channels configured",
        "noRules": "No notification rules configured",
        "noLogs": "No notification logs",
        "channelTypes": {
          "slack": "Slack",
          "email": "Email",
          "webhook": "Webhook",
          "discord": "Discord",
          "telegram": "Telegram",
          "pagerduty": "PagerDuty",
          "opsgenie": "OpsGenie",
          "teams": "Microsoft Teams",
          "github": "GitHub"
        },
        "channelDescriptions": {
          "slack": "Send notifications to Slack channels via webhooks",
          "email": "Send notifications via SMTP email",
          "webhook": "Send notifications to custom HTTP endpoints",
          "discord": "Send notifications to Discord channels via webhooks",
          "telegram": "Send notifications via Telegram Bot API",
          "pagerduty": "Create incidents in PagerDuty for critical alerts",
          "opsgenie": "Create alerts in OpsGenie for incident management",
          "teams": "Send notifications to Microsoft Teams channels",
          "github": "Create issues in GitHub repositories for tracking"
        },
        "channelCategories": {
          "basic": "Basic",
          "chat": "Chat",
          "incident": "Incident Management",
          "devops": "DevOps"
        },
        "channelFields": {
          "webhookUrl": "Webhook URL",
          "apiKey": "API Key",
          "token": "Token",
          "slackChannel": "Channel",
          "slackUsername": "Bot Username",
          "slackIconEmoji": "Icon Emoji",
          "smtpHost": "SMTP Host",
          "smtpPort": "SMTP Port",
          "smtpUser": "SMTP Username",
          "smtpPassword": "SMTP Password",
          "fromEmail": "From Email",
          "recipients": "Recipients",
          "useTls": "Use TLS",
          "url": "URL",
          "method": "HTTP Method",
          "headers": "Custom Headers",
          "includeEventData": "Include Event Data",
          "discordUsername": "Bot Username",
          "avatarUrl": "Avatar URL",
          "botToken": "Bot Token",
          "chatId": "Chat ID",
          "parseMode": "Parse Mode",
          "disableNotification": "Silent Mode",
          "routingKey": "Routing Key",
          "severity": "Default Severity",
          "component": "Component",
          "group": "Group",
          "classType": "Class Type",
          "priority": "Default Priority",
          "tags": "Tags",
          "team": "Team",
          "responders": "Responders",
          "themeColor": "Theme Color",
          "owner": "Repository Owner",
          "repo": "Repository Name",
          "labels": "Labels",
          "assignees": "Assignees"
        },
        "conditions": {
          "validation_failed": "Validation Failed",
          "critical_issues": "Critical Issues Detected",
          "high_issues": "High Severity Issues",
          "schedule_failed": "Schedule Failed",
          "drift_detected": "Drift Detected",
          "schema_changed": "Schema Changed"
        },
        "testSuccess": "Test notification sent successfully",
        "testFailed": "Failed to send test notification",
        "sent": "Sent",
        "failed": "Failed",
        "pending": "Pending",
        "channelCreated": "Channel created successfully",
        "channelUpdated": "Channel updated successfully",
        "channelDeleted": "Channel deleted successfully",
        "createChannelFailed": "Failed to create channel",
        "updateChannelFailed": "Failed to update channel",
        "deleteChannelFailed": "Failed to delete channel",
        "deleteChannel": "Delete Channel",
        "deleteChannelConfirm": "Are you sure you want to delete this channel? This action cannot be undone.",
        "ruleCreated": "Rule created successfully",
        "ruleUpdated": "Rule updated successfully",
        "ruleDeleted": "Rule deleted successfully",
        "createRuleFailed": "Failed to create rule",
        "updateRuleFailed": "Failed to update rule",
        "deleteRuleFailed": "Failed to delete rule",
        "deleteRule": "Delete Rule",
        "deleteRuleConfirm": "Are you sure you want to delete this rule? This action cannot be undone.",
        "selectChannelType": "Select a notification channel type",
        "configureChannel": "Configure your channel settings",
        "channelName": "Channel Name",
        "ruleName": "Rule Name",
        "triggerCondition": "Trigger Condition",
        "sendToChannels": "Send To Channels",
        "severityLevels": {
          "critical": "Critical",
          "error": "Error",
          "warning": "Warning",
          "info": "Info"
        },
        "priorityLevels": {
          "p1": "P1 - Critical",
          "p2": "P2 - High",
          "p3": "P3 - Moderate",
          "p4": "P4 - Low",
          "p5": "P5 - Informational"
        },
        "parseModes": {
          "html": "HTML",
          "markdown": "Markdown V2"
        },
        "httpMethods": {
          "post": "POST",
          "put": "PUT",
          "get": "GET"
        },
        "required": "Required",
        "optional": "Optional",
        "invalidFormat": "Invalid format",
        "fieldRequired": "This field is required",
        "helpText": {
          "slack": {
            "webhookUrl": "Slack Incoming Webhook URL from your app settings",
            "channel": "Override the default channel (e.g., #alerts)"
          },
          "email": {
            "recipients": "One email address per line"
          },
          "pagerduty": {
            "routingKey": "Events API v2 Integration Key from your service"
          },
          "opsgenie": {
            "responders": "JSON array of responders"
          },
          "telegram": {
            "botToken": "Token from @BotFather",
            "chatId": "User, group, or channel ID"
          },
          "github": {
            "token": "Personal Access Token with repo scope"
          },
          "webhook": {
            "headers": "Custom headers in JSON format"
          }
        }
      },
      "ko": {
        "title": "알림",
        "subtitle": "알림 채널 및 규칙 설정",
        "channels": "채널",
        "rules": "규칙",
        "logs": "로그",
        "addChannel": "채널 추가",
        "addRule": "규칙 추가",
        "editChannel": "채널 편집",
        "editRule": "규칙 편집",
        "testChannel": "테스트",
        "noChannels": "설정된 알림 채널이 없습니다",
        "noRules": "설정된 알림 규칙이 없습니다",
        "noLogs": "알림 로그가 없습니다",
        "channelTypes": {
          "slack": "Slack",
          "email": "이메일",
          "webhook": "웹훅",
          "discord": "Discord",
          "telegram": "Telegram",
          "pagerduty": "PagerDuty",
          "opsgenie": "OpsGenie",
          "teams": "Microsoft Teams",
          "github": "GitHub"
        },
        "channelDescriptions": {
          "slack": "Slack 웹훅을 통해 채널에 알림 전송",
          "email": "SMTP 이메일로 알림 전송",
          "webhook": "커스텀 HTTP 엔드포인트로 알림 전송",
          "discord": "Discord 웹훅을 통해 채널에 알림 전송",
          "telegram": "Telegram Bot API로 알림 전송",
          "pagerduty": "PagerDuty에 인시던트 생성",
          "opsgenie": "OpsGenie에 알림 생성",
          "teams": "Microsoft Teams 채널에 알림 전송",
          "github": "GitHub 저장소에 이슈 생성"
        },
        "channelCategories": {
          "basic": "기본",
          "chat": "채팅",
          "incident": "인시던트 관리",
          "devops": "DevOps"
        },
        "channelFields": {
          "webhookUrl": "웹훅 URL",
          "apiKey": "API 키",
          "token": "토큰",
          "slackChannel": "채널",
          "slackUsername": "봇 사용자명",
          "slackIconEmoji": "아이콘 이모지",
          "smtpHost": "SMTP 호스트",
          "smtpPort": "SMTP 포트",
          "smtpUser": "SMTP 사용자명",
          "smtpPassword": "SMTP 비밀번호",
          "fromEmail": "발신자 이메일",
          "recipients": "수신자",
          "useTls": "TLS 사용",
          "url": "URL",
          "method": "HTTP 메서드",
          "headers": "커스텀 헤더",
          "includeEventData": "이벤트 데이터 포함",
          "discordUsername": "봇 사용자명",
          "avatarUrl": "아바타 URL",
          "botToken": "봇 토큰",
          "chatId": "채팅 ID",
          "parseMode": "파싱 모드",
          "disableNotification": "무음 모드",
          "routingKey": "라우팅 키",
          "severity": "기본 심각도",
          "component": "컴포넌트",
          "group": "그룹",
          "classType": "클래스 타입",
          "priority": "기본 우선순위",
          "tags": "태그",
          "team": "팀",
          "responders": "응답자",
          "themeColor": "테마 색상",
          "owner": "저장소 소유자",
          "repo": "저장소 이름",
          "labels": "레이블",
          "assignees": "담당자"
        },
        "conditions": {
          "validation_failed": "검증 실패",
          "critical_issues": "심각한 이슈 발견",
          "high_issues": "높은 심각도 이슈",
          "schedule_failed": "스케줄 실패",
          "drift_detected": "드리프트 감지",
          "schema_changed": "스키마 변경"
        },
        "testSuccess": "테스트 알림이 성공적으로 전송되었습니다",
        "testFailed": "테스트 알림 전송에 실패했습니다",
        "sent": "전송됨",
        "failed": "실패",
        "pending": "대기 중",
        "channelCreated": "채널이 생성되었습니다",
        "channelUpdated": "채널이 업데이트되었습니다",
        "channelDeleted": "채널이 삭제되었습니다",
        "createChannelFailed": "채널 생성에 실패했습니다",
        "updateChannelFailed": "채널 업데이트에 실패했습니다",
        "deleteChannelFailed": "채널 삭제에 실패했습니다",
        "deleteChannel": "채널 삭제",
        "deleteChannelConfirm": "이 채널을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.",
        "ruleCreated": "규칙이 생성되었습니다",
        "ruleUpdated": "규칙이 업데이트되었습니다",
        "ruleDeleted": "규칙이 삭제되었습니다",
        "createRuleFailed": "규칙 생성에 실패했습니다",
        "updateRuleFailed": "규칙 업데이트에 실패했습니다",
        "deleteRuleFailed": "규칙 삭제에 실패했습니다",
        "deleteRule": "규칙 삭제",
        "deleteRuleConfirm": "이 규칙을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.",
        "selectChannelType": "알림 채널 유형을 선택하세요",
        "configureChannel": "채널 설정을 구성하세요",
        "channelName": "채널 이름",
        "ruleName": "규칙 이름",
        "triggerCondition": "트리거 조건",
        "sendToChannels": "알림 전송 채널",
        "severityLevels": {
          "critical": "심각",
          "error": "오류",
          "warning": "경고",
          "info": "정보"
        },
        "priorityLevels": {
          "p1": "P1 - 심각",
          "p2": "P2 - 높음",
          "p3": "P3 - 보통",
          "p4": "P4 - 낮음",
          "p5": "P5 - 정보"
        },
        "parseModes": {
          "html": "HTML",
          "markdown": "Markdown V2"
        },
        "httpMethods": {
          "post": "POST",
          "put": "PUT",
          "get": "GET"
        },
        "required": "필수",
        "optional": "선택",
        "invalidFormat": "잘못된 형식",
        "fieldRequired": "이 필드는 필수입니다",
        "helpText": {
          "slack": {
            "webhookUrl": "Slack 앱 설정의 수신 웹훅 URL",
            "channel": "기본 채널 재정의 (예: #alerts)"
          },
          "email": {
            "recipients": "한 줄에 하나의 이메일 주소"
          },
          "pagerduty": {
            "routingKey": "서비스의 Events API v2 통합 키"
          },
          "opsgenie": {
            "responders": "응답자 JSON 배열"
          },
          "telegram": {
            "botToken": "@BotFather에서 받은 토큰",
            "chatId": "사용자, 그룹 또는 채널 ID"
          },
          "github": {
            "token": "repo 권한이 있는 개인 액세스 토큰"
          },
          "webhook": {
            "headers": "JSON 형식의 커스텀 헤더"
          }
        }
      }
    }
  },
  "localIds": [
    "notifications::local::src/content/notifications.content.ts"
  ]
} as const;
