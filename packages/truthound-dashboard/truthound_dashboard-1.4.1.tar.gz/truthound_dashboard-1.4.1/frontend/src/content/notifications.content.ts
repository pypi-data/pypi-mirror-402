/**
 * Notifications page translations.
 *
 * Contains translations for the notification management page
 * including all 9 channel types and their configurations.
 */
import { t, type Dictionary } from 'intlayer'

const notificationsContent = {
  key: 'notifications',
  content: {
    title: t({ en: 'Notifications', ko: '알림' }),
    subtitle: t({
      en: 'Configure notification channels and rules',
      ko: '알림 채널 및 규칙 설정',
    }),

    // Tabs
    channels: t({ en: 'Channels', ko: '채널' }),
    rules: t({ en: 'Rules', ko: '규칙' }),
    logs: t({ en: 'Logs', ko: '로그' }),

    // Actions
    addChannel: t({ en: 'Add Channel', ko: '채널 추가' }),
    addRule: t({ en: 'Add Rule', ko: '규칙 추가' }),
    editChannel: t({ en: 'Edit Channel', ko: '채널 편집' }),
    editRule: t({ en: 'Edit Rule', ko: '규칙 편집' }),
    testChannel: t({ en: 'Test', ko: '테스트' }),

    // Empty states
    noChannels: t({
      en: 'No notification channels configured',
      ko: '설정된 알림 채널이 없습니다',
    }),
    noRules: t({
      en: 'No notification rules configured',
      ko: '설정된 알림 규칙이 없습니다',
    }),
    noLogs: t({ en: 'No notification logs', ko: '알림 로그가 없습니다' }),

    // Channel types
    channelTypes: {
      slack: t({ en: 'Slack', ko: 'Slack' }),
      email: t({ en: 'Email', ko: '이메일' }),
      webhook: t({ en: 'Webhook', ko: '웹훅' }),
      discord: t({ en: 'Discord', ko: 'Discord' }),
      telegram: t({ en: 'Telegram', ko: 'Telegram' }),
      pagerduty: t({ en: 'PagerDuty', ko: 'PagerDuty' }),
      opsgenie: t({ en: 'OpsGenie', ko: 'OpsGenie' }),
      teams: t({ en: 'Microsoft Teams', ko: 'Microsoft Teams' }),
      github: t({ en: 'GitHub', ko: 'GitHub' }),
    },

    // Channel type descriptions
    channelDescriptions: {
      slack: t({
        en: 'Send notifications to Slack channels via webhooks',
        ko: 'Slack 웹훅을 통해 채널에 알림 전송',
      }),
      email: t({
        en: 'Send notifications via SMTP email',
        ko: 'SMTP 이메일로 알림 전송',
      }),
      webhook: t({
        en: 'Send notifications to custom HTTP endpoints',
        ko: '커스텀 HTTP 엔드포인트로 알림 전송',
      }),
      discord: t({
        en: 'Send notifications to Discord channels via webhooks',
        ko: 'Discord 웹훅을 통해 채널에 알림 전송',
      }),
      telegram: t({
        en: 'Send notifications via Telegram Bot API',
        ko: 'Telegram Bot API로 알림 전송',
      }),
      pagerduty: t({
        en: 'Create incidents in PagerDuty for critical alerts',
        ko: 'PagerDuty에 인시던트 생성',
      }),
      opsgenie: t({
        en: 'Create alerts in OpsGenie for incident management',
        ko: 'OpsGenie에 알림 생성',
      }),
      teams: t({
        en: 'Send notifications to Microsoft Teams channels',
        ko: 'Microsoft Teams 채널에 알림 전송',
      }),
      github: t({
        en: 'Create issues in GitHub repositories for tracking',
        ko: 'GitHub 저장소에 이슈 생성',
      }),
    },

    // Channel categories
    channelCategories: {
      basic: t({ en: 'Basic', ko: '기본' }),
      chat: t({ en: 'Chat', ko: '채팅' }),
      incident: t({ en: 'Incident Management', ko: '인시던트 관리' }),
      devops: t({ en: 'DevOps', ko: 'DevOps' }),
    },

    // Field labels for channel configs
    channelFields: {
      // Common
      webhookUrl: t({ en: 'Webhook URL', ko: '웹훅 URL' }),
      apiKey: t({ en: 'API Key', ko: 'API 키' }),
      token: t({ en: 'Token', ko: '토큰' }),

      // Slack
      slackChannel: t({ en: 'Channel', ko: '채널' }),
      slackUsername: t({ en: 'Bot Username', ko: '봇 사용자명' }),
      slackIconEmoji: t({ en: 'Icon Emoji', ko: '아이콘 이모지' }),

      // Email
      smtpHost: t({ en: 'SMTP Host', ko: 'SMTP 호스트' }),
      smtpPort: t({ en: 'SMTP Port', ko: 'SMTP 포트' }),
      smtpUser: t({ en: 'SMTP Username', ko: 'SMTP 사용자명' }),
      smtpPassword: t({ en: 'SMTP Password', ko: 'SMTP 비밀번호' }),
      fromEmail: t({ en: 'From Email', ko: '발신자 이메일' }),
      recipients: t({ en: 'Recipients', ko: '수신자' }),
      useTls: t({ en: 'Use TLS', ko: 'TLS 사용' }),

      // Webhook
      url: t({ en: 'URL', ko: 'URL' }),
      method: t({ en: 'HTTP Method', ko: 'HTTP 메서드' }),
      headers: t({ en: 'Custom Headers', ko: '커스텀 헤더' }),
      includeEventData: t({ en: 'Include Event Data', ko: '이벤트 데이터 포함' }),

      // Discord
      discordUsername: t({ en: 'Bot Username', ko: '봇 사용자명' }),
      avatarUrl: t({ en: 'Avatar URL', ko: '아바타 URL' }),

      // Telegram
      botToken: t({ en: 'Bot Token', ko: '봇 토큰' }),
      chatId: t({ en: 'Chat ID', ko: '채팅 ID' }),
      parseMode: t({ en: 'Parse Mode', ko: '파싱 모드' }),
      disableNotification: t({ en: 'Silent Mode', ko: '무음 모드' }),

      // PagerDuty
      routingKey: t({ en: 'Routing Key', ko: '라우팅 키' }),
      severity: t({ en: 'Default Severity', ko: '기본 심각도' }),
      component: t({ en: 'Component', ko: '컴포넌트' }),
      group: t({ en: 'Group', ko: '그룹' }),
      classType: t({ en: 'Class Type', ko: '클래스 타입' }),

      // OpsGenie
      priority: t({ en: 'Default Priority', ko: '기본 우선순위' }),
      tags: t({ en: 'Tags', ko: '태그' }),
      team: t({ en: 'Team', ko: '팀' }),
      responders: t({ en: 'Responders', ko: '응답자' }),

      // Teams
      themeColor: t({ en: 'Theme Color', ko: '테마 색상' }),

      // GitHub
      owner: t({ en: 'Repository Owner', ko: '저장소 소유자' }),
      repo: t({ en: 'Repository Name', ko: '저장소 이름' }),
      labels: t({ en: 'Labels', ko: '레이블' }),
      assignees: t({ en: 'Assignees', ko: '담당자' }),
    },

    // Conditions
    conditions: {
      validation_failed: t({ en: 'Validation Failed', ko: '검증 실패' }),
      critical_issues: t({
        en: 'Critical Issues Detected',
        ko: '심각한 이슈 발견',
      }),
      high_issues: t({ en: 'High Severity Issues', ko: '높은 심각도 이슈' }),
      schedule_failed: t({ en: 'Schedule Failed', ko: '스케줄 실패' }),
      drift_detected: t({ en: 'Drift Detected', ko: '드리프트 감지' }),
      schema_changed: t({ en: 'Schema Changed', ko: '스키마 변경' }),
    },

    // Status messages
    testSuccess: t({
      en: 'Test notification sent successfully',
      ko: '테스트 알림이 성공적으로 전송되었습니다',
    }),
    testFailed: t({
      en: 'Failed to send test notification',
      ko: '테스트 알림 전송에 실패했습니다',
    }),
    sent: t({ en: 'Sent', ko: '전송됨' }),
    failed: t({ en: 'Failed', ko: '실패' }),
    pending: t({ en: 'Pending', ko: '대기 중' }),

    // Channel CRUD messages
    channelCreated: t({
      en: 'Channel created successfully',
      ko: '채널이 생성되었습니다',
    }),
    channelUpdated: t({
      en: 'Channel updated successfully',
      ko: '채널이 업데이트되었습니다',
    }),
    channelDeleted: t({
      en: 'Channel deleted successfully',
      ko: '채널이 삭제되었습니다',
    }),
    createChannelFailed: t({
      en: 'Failed to create channel',
      ko: '채널 생성에 실패했습니다',
    }),
    updateChannelFailed: t({
      en: 'Failed to update channel',
      ko: '채널 업데이트에 실패했습니다',
    }),
    deleteChannelFailed: t({
      en: 'Failed to delete channel',
      ko: '채널 삭제에 실패했습니다',
    }),

    // Delete channel
    deleteChannel: t({ en: 'Delete Channel', ko: '채널 삭제' }),
    deleteChannelConfirm: t({
      en: 'Are you sure you want to delete this channel? This action cannot be undone.',
      ko: '이 채널을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.',
    }),

    // Rule CRUD messages
    ruleCreated: t({
      en: 'Rule created successfully',
      ko: '규칙이 생성되었습니다',
    }),
    ruleUpdated: t({
      en: 'Rule updated successfully',
      ko: '규칙이 업데이트되었습니다',
    }),
    ruleDeleted: t({
      en: 'Rule deleted successfully',
      ko: '규칙이 삭제되었습니다',
    }),
    createRuleFailed: t({
      en: 'Failed to create rule',
      ko: '규칙 생성에 실패했습니다',
    }),
    updateRuleFailed: t({
      en: 'Failed to update rule',
      ko: '규칙 업데이트에 실패했습니다',
    }),
    deleteRuleFailed: t({
      en: 'Failed to delete rule',
      ko: '규칙 삭제에 실패했습니다',
    }),

    // Delete rule
    deleteRule: t({ en: 'Delete Rule', ko: '규칙 삭제' }),
    deleteRuleConfirm: t({
      en: 'Are you sure you want to delete this rule? This action cannot be undone.',
      ko: '이 규칙을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.',
    }),

    // Dialog labels
    selectChannelType: t({
      en: 'Select a notification channel type',
      ko: '알림 채널 유형을 선택하세요',
    }),
    configureChannel: t({
      en: 'Configure your channel settings',
      ko: '채널 설정을 구성하세요',
    }),
    channelName: t({ en: 'Channel Name', ko: '채널 이름' }),
    ruleName: t({ en: 'Rule Name', ko: '규칙 이름' }),
    triggerCondition: t({ en: 'Trigger Condition', ko: '트리거 조건' }),
    sendToChannels: t({ en: 'Send To Channels', ko: '알림 전송 채널' }),

    // Severity levels
    severityLevels: {
      critical: t({ en: 'Critical', ko: '심각' }),
      error: t({ en: 'Error', ko: '오류' }),
      warning: t({ en: 'Warning', ko: '경고' }),
      info: t({ en: 'Info', ko: '정보' }),
    },

    // Priority levels (OpsGenie)
    priorityLevels: {
      p1: t({ en: 'P1 - Critical', ko: 'P1 - 심각' }),
      p2: t({ en: 'P2 - High', ko: 'P2 - 높음' }),
      p3: t({ en: 'P3 - Moderate', ko: 'P3 - 보통' }),
      p4: t({ en: 'P4 - Low', ko: 'P4 - 낮음' }),
      p5: t({ en: 'P5 - Informational', ko: 'P5 - 정보' }),
    },

    // Parse modes (Telegram)
    parseModes: {
      html: t({ en: 'HTML', ko: 'HTML' }),
      markdown: t({ en: 'Markdown V2', ko: 'Markdown V2' }),
    },

    // HTTP methods
    httpMethods: {
      post: t({ en: 'POST', ko: 'POST' }),
      put: t({ en: 'PUT', ko: 'PUT' }),
      get: t({ en: 'GET', ko: 'GET' }),
    },

    // Form validation
    required: t({ en: 'Required', ko: '필수' }),
    optional: t({ en: 'Optional', ko: '선택' }),
    invalidFormat: t({ en: 'Invalid format', ko: '잘못된 형식' }),
    fieldRequired: t({ en: 'This field is required', ko: '이 필드는 필수입니다' }),

    // Help text
    helpText: {
      slack: {
        webhookUrl: t({
          en: 'Slack Incoming Webhook URL from your app settings',
          ko: 'Slack 앱 설정의 수신 웹훅 URL',
        }),
        channel: t({
          en: 'Override the default channel (e.g., #alerts)',
          ko: '기본 채널 재정의 (예: #alerts)',
        }),
      },
      email: {
        recipients: t({
          en: 'One email address per line',
          ko: '한 줄에 하나의 이메일 주소',
        }),
      },
      pagerduty: {
        routingKey: t({
          en: 'Events API v2 Integration Key from your service',
          ko: '서비스의 Events API v2 통합 키',
        }),
      },
      opsgenie: {
        responders: t({
          en: 'JSON array of responders',
          ko: '응답자 JSON 배열',
        }),
      },
      telegram: {
        botToken: t({
          en: 'Token from @BotFather',
          ko: '@BotFather에서 받은 토큰',
        }),
        chatId: t({
          en: 'User, group, or channel ID',
          ko: '사용자, 그룹 또는 채널 ID',
        }),
      },
      github: {
        token: t({
          en: 'Personal Access Token with repo scope',
          ko: 'repo 권한이 있는 개인 액세스 토큰',
        }),
      },
      webhook: {
        headers: t({
          en: 'Custom headers in JSON format',
          ko: 'JSON 형식의 커스텀 헤더',
        }),
      },
    },
  },
} satisfies Dictionary

export default notificationsContent
