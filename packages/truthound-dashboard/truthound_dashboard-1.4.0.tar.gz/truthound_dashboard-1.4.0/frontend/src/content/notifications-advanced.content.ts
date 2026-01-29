/**
 * Advanced Notifications content translations.
 *
 * Contains translations for routing, deduplication, throttling, and escalation features.
 */
import { t, type Dictionary } from 'intlayer'

const notificationsAdvancedContent = {
  key: 'notificationsAdvanced',
  content: {
    // Tab labels
    tabs: {
      routing: t({ en: 'Routing', ko: '라우팅' }),
      routingRules: t({ en: 'Routing Rules', ko: '라우팅 규칙' }),
      deduplication: t({ en: 'Deduplication', ko: '중복 제거' }),
      throttling: t({ en: 'Throttling', ko: '스로틀링' }),
      escalation: t({ en: 'Escalation', ko: '에스컬레이션' }),
      incidents: t({ en: 'Incidents', ko: '인시던트' }),
    },

    // Routing Rules
    routing: {
      title: t({ en: 'Routing Rules', ko: '라우팅 규칙' }),
      subtitle: t({
        en: 'Define rules to route notifications to specific channels',
        ko: '알림을 특정 채널로 라우팅하는 규칙 정의',
      }),
      addRule: t({ en: 'Add Routing Rule', ko: '라우팅 규칙 추가' }),
      editRule: t({ en: 'Edit Routing Rule', ko: '라우팅 규칙 편집' }),
      noRules: t({
        en: 'No routing rules configured',
        ko: '설정된 라우팅 규칙이 없습니다',
      }),
      priority: t({ en: 'Priority', ko: '우선순위' }),
      stopOnMatch: t({ en: 'Stop on Match', ko: '매칭 시 중단' }),
      actions: t({ en: 'Target Channels', ko: '대상 채널' }),
      ruleConfig: t({ en: 'Rule Configuration', ko: '규칙 설정' }),
    },

    // Rule Types
    ruleTypes: {
      severity: t({ en: 'Severity', ko: '심각도' }),
      issue_count: t({ en: 'Issue Count', ko: '이슈 수' }),
      pass_rate: t({ en: 'Pass Rate', ko: '통과율' }),
      time_window: t({ en: 'Time Window', ko: '시간 윈도우' }),
      tag: t({ en: 'Tag', ko: '태그' }),
      data_asset: t({ en: 'Data Asset', ko: '데이터 자산' }),
      metadata: t({ en: 'Metadata', ko: '메타데이터' }),
      status: t({ en: 'Status', ko: '상태' }),
      error: t({ en: 'Error Pattern', ko: '에러 패턴' }),
      always: t({ en: 'Always Match', ko: '항상 매칭' }),
      never: t({ en: 'Never Match', ko: '절대 아님' }),
      all_of: t({ en: 'All Of (AND)', ko: 'All Of (AND)' }),
      any_of: t({ en: 'Any Of (OR)', ko: 'Any Of (OR)' }),
      not: t({ en: 'Not (Negate)', ko: 'Not (부정)' }),
    },

    // Rule Type Descriptions
    ruleTypeDescriptions: {
      severity: t({
        en: 'Match notifications by minimum severity level',
        ko: '최소 심각도 수준으로 알림 매칭',
      }),
      issue_count: t({
        en: 'Match when issue count exceeds threshold',
        ko: '이슈 수가 임계값을 초과할 때 매칭',
      }),
      pass_rate: t({
        en: 'Match when pass rate is below threshold',
        ko: '통과율이 임계값 미만일 때 매칭',
      }),
      time_window: t({
        en: 'Match during specific hours and days',
        ko: '특정 시간과 요일에 매칭',
      }),
      tag: t({
        en: 'Match by notification tags',
        ko: '알림 태그로 매칭',
      }),
      data_asset: t({
        en: 'Match by data asset name or pattern',
        ko: '데이터 자산 이름 또는 패턴으로 매칭',
      }),
      metadata: t({
        en: 'Match by metadata field value',
        ko: '메타데이터 필드 값으로 매칭',
      }),
      status: t({
        en: 'Match by validation status',
        ko: '검증 상태로 매칭',
      }),
      error: t({
        en: 'Match by error message pattern',
        ko: '에러 메시지 패턴으로 매칭',
      }),
      always: t({
        en: 'Always matches (catch-all rule)',
        ko: '항상 매칭 (기본 규칙)',
      }),
      never: t({
        en: 'Never matches (disabled rule)',
        ko: '매칭하지 않음 (비활성화 규칙)',
      }),
      all_of: t({
        en: 'Match when ALL sub-rules match',
        ko: '모든 하위 규칙이 매칭될 때 매칭',
      }),
      any_of: t({
        en: 'Match when ANY sub-rule matches',
        ko: '하나의 하위 규칙이라도 매칭될 때 매칭',
      }),
      not: t({
        en: 'Negate the sub-rule result',
        ko: '하위 규칙 결과를 반전',
      }),
    },

    // Rule Builder UI
    ruleBuilder: {
      ruleType: t({ en: 'Rule Type', ko: '규칙 유형' }),
      ruleConfiguration: t({ en: 'Rule Configuration', ko: '규칙 설정' }),
      subRules: t({ en: 'Sub-rules', ko: '하위 규칙' }),
      ruleToNegate: t({ en: 'Rule to Negate', ko: '반전할 규칙' }),
      addRule: t({ en: 'Add Rule', ko: '규칙 추가' }),
      noSubRules: t({
        en: 'No sub-rules. Click "Add Rule" to add at least one rule.',
        ko: '하위 규칙이 없습니다. "규칙 추가"를 클릭하여 규칙을 추가하세요.',
      }),
      maxDepthReached: t({
        en: 'Maximum nesting depth reached. Cannot add more combinators.',
        ko: '최대 중첩 깊이에 도달했습니다. 더 이상 조합기를 추가할 수 없습니다.',
      }),
      configurationIncomplete: t({
        en: 'Configuration incomplete',
        ko: '설정이 불완전합니다',
      }),
      copyRuleConfiguration: t({
        en: 'Copy rule configuration',
        ko: '규칙 설정 복사',
      }),
      alwaysMatchMessage: t({
        en: 'This rule always matches. Use as a catch-all or fallback rule.',
        ko: '이 규칙은 항상 매칭됩니다. 기본 규칙으로 사용하세요.',
      }),
      neverMatchMessage: t({
        en: 'This rule never matches. Use to temporarily disable routing without deleting.',
        ko: '이 규칙은 매칭되지 않습니다. 삭제하지 않고 일시적으로 비활성화할 때 사용하세요.',
      }),
      visualMode: t({ en: 'Visual', ko: '시각적' }),
      jsonMode: t({ en: 'JSON', ko: 'JSON' }),
      copyJson: t({ en: 'Copy JSON', ko: 'JSON 복사' }),
      invalidJson: t({ en: 'Invalid JSON', ko: '유효하지 않은 JSON' }),
      categories: {
        basic: t({ en: 'Basic', ko: '기본' }),
        condition: t({ en: 'Condition', ko: '조건' }),
        combinator: t({ en: 'Combinator', ko: '조합기' }),
        static: t({ en: 'Static', ko: '정적' }),
      },
    },

    // Rule Parameters
    ruleParams: {
      minSeverity: t({ en: 'Minimum Severity', ko: '최소 심각도' }),
      minCount: t({ en: 'Minimum Count', ko: '최소 개수' }),
      maxPassRate: t({ en: 'Maximum Pass Rate', ko: '최대 통과율' }),
      startHour: t({ en: 'Start Hour', ko: '시작 시간' }),
      endHour: t({ en: 'End Hour', ko: '종료 시간' }),
      weekdays: t({ en: 'Weekdays', ko: '요일' }),
      timezone: t({ en: 'Timezone', ko: '시간대' }),
      tags: t({ en: 'Tags', ko: '태그' }),
      matchAll: t({ en: 'Match All', ko: '모두 매칭' }),
      pattern: t({ en: 'Asset Pattern', ko: '자산 패턴' }),
      fieldName: t({ en: 'Field Name', ko: '필드명' }),
      expectedValue: t({ en: 'Expected Value', ko: '기대값' }),
      operator: t({ en: 'Operator', ko: '연산자' }),
      statuses: t({ en: 'Statuses', ko: '상태' }),
      errorPattern: t({ en: 'Error Pattern', ko: '에러 패턴' }),
      operators: {
        eq: t({ en: 'Equals (=)', ko: '같음 (=)' }),
        ne: t({ en: 'Not Equals (!=)', ko: '같지 않음 (!=)' }),
        contains: t({ en: 'Contains', ko: '포함' }),
        regex: t({ en: 'Regex Match', ko: '정규식 매칭' }),
        gt: t({ en: 'Greater Than (>)', ko: '보다 큼 (>)' }),
        lt: t({ en: 'Less Than (<)', ko: '보다 작음 (<)' }),
        gte: t({ en: 'Greater or Equal (>=)', ko: '크거나 같음 (>=)' }),
        lte: t({ en: 'Less or Equal (<=)', ko: '작거나 같음 (<=)' }),
      },
      severityLevels: {
        info: t({ en: 'Info', ko: '정보' }),
        low: t({ en: 'Low', ko: '낮음' }),
        medium: t({ en: 'Medium', ko: '중간' }),
        high: t({ en: 'High', ko: '높음' }),
        critical: t({ en: 'Critical', ko: '심각' }),
      },
      statusValues: {
        success: t({ en: 'Success', ko: '성공' }),
        warning: t({ en: 'Warning', ko: '경고' }),
        failure: t({ en: 'Failure', ko: '실패' }),
        error: t({ en: 'Error', ko: '에러' }),
      },
      weekdayNames: {
        mon: t({ en: 'Mon', ko: '월' }),
        tue: t({ en: 'Tue', ko: '화' }),
        wed: t({ en: 'Wed', ko: '수' }),
        thu: t({ en: 'Thu', ko: '목' }),
        fri: t({ en: 'Fri', ko: '금' }),
        sat: t({ en: 'Sat', ko: '토' }),
        sun: t({ en: 'Sun', ko: '일' }),
      },
      weekdayFullNames: {
        mon: t({ en: 'Monday', ko: '월요일' }),
        tue: t({ en: 'Tuesday', ko: '화요일' }),
        wed: t({ en: 'Wednesday', ko: '수요일' }),
        thu: t({ en: 'Thursday', ko: '목요일' }),
        fri: t({ en: 'Friday', ko: '금요일' }),
        sat: t({ en: 'Saturday', ko: '토요일' }),
        sun: t({ en: 'Sunday', ko: '일요일' }),
      },
      // Time window picker labels
      timeRange: t({ en: 'Time Range', ko: '시간 범위' }),
      to: t({ en: 'to', ko: '~' }),
      optional: t({ en: 'optional', ko: '선택사항' }),
      // Quick selection buttons
      weekdaysOnly: t({ en: 'Weekdays', ko: '평일' }),
      weekendsOnly: t({ en: 'Weekend', ko: '주말' }),
      allDays: t({ en: 'All', ko: '전체' }),
      clearDays: t({ en: 'Clear', ko: '초기화' }),
      // Selection feedback
      noDaysSelected: t({ en: 'No days selected', ko: '선택된 요일 없음' }),
      everyDay: t({ en: 'Every day', ko: '매일' }),
      daysSelected: t({ en: 'days selected', ko: '일 선택됨' }),
      // Time format labels
      activeHours: t({ en: 'Active hours', ko: '활성 시간' }),
      overnightRange: t({ en: 'Overnight range', ko: '야간 범위' }),
      nextDay: t({ en: 'next day', ko: '다음 날' }),
      // Timezone picker
      browserTimezone: t({ en: 'Browser timezone', ko: '브라우저 시간대' }),
      timezoneNote: t({
        en: 'Times will be evaluated in the selected timezone',
        ko: '시간은 선택한 시간대로 평가됩니다',
      }),
      timezoneGroups: {
        utc: t({ en: 'UTC', ko: 'UTC' }),
        americas: t({ en: 'Americas', ko: '아메리카' }),
        europe: t({ en: 'Europe', ko: '유럽' }),
        asia: t({ en: 'Asia', ko: '아시아' }),
        pacific: t({ en: 'Pacific', ko: '태평양' }),
      },
    },

    // Deduplication
    deduplication: {
      title: t({ en: 'Deduplication', ko: '중복 제거' }),
      subtitle: t({
        en: 'Configure notification deduplication to reduce noise',
        ko: '노이즈 감소를 위한 알림 중복 제거 설정',
      }),
      addConfig: t({ en: 'Add Config', ko: '설정 추가' }),
      editConfig: t({ en: 'Edit Config', ko: '설정 편집' }),
      noConfigs: t({
        en: 'No deduplication configs',
        ko: '설정된 중복 제거 설정이 없습니다',
      }),
      strategy: t({ en: 'Strategy', ko: '전략' }),
      policy: t({ en: 'Policy', ko: '정책' }),
      windowSeconds: t({ en: 'Window (seconds)', ko: '윈도우 (초)' }),
      stats: {
        title: t({ en: 'Deduplication Stats', ko: '중복 제거 통계' }),
        totalReceived: t({ en: 'Total Received', ko: '총 수신' }),
        totalDeduplicated: t({ en: 'Deduplicated', ko: '중복 제거됨' }),
        totalPassed: t({ en: 'Passed Through', ko: '통과됨' }),
        dedupRate: t({ en: 'Dedup Rate', ko: '중복 제거율' }),
        activeFingerprints: t({ en: 'Active Fingerprints', ko: '활성 핑거프린트' }),
      },
    },

    // Deduplication Strategies
    strategies: {
      sliding: t({ en: 'Sliding Window', ko: '슬라이딩 윈도우' }),
      tumbling: t({ en: 'Tumbling Window', ko: '텀블링 윈도우' }),
      session: t({ en: 'Session Window', ko: '세션 윈도우' }),
      adaptive: t({ en: 'Adaptive Window', ko: '적응형 윈도우' }),
    },

    // Deduplication Policies
    policies: {
      none: t({ en: 'None', ko: '없음' }),
      basic: t({ en: 'Basic', ko: '기본' }),
      severity: t({ en: 'By Severity', ko: '심각도 기반' }),
      issue_based: t({ en: 'Issue Based', ko: '이슈 기반' }),
      strict: t({ en: 'Strict', ko: '엄격' }),
      custom: t({ en: 'Custom', ko: '사용자 정의' }),
    },

    // Throttling
    throttling: {
      title: t({ en: 'Throttling', ko: '스로틀링' }),
      subtitle: t({
        en: 'Control notification rate limits',
        ko: '알림 속도 제한 설정',
      }),
      addConfig: t({ en: 'Add Config', ko: '설정 추가' }),
      editConfig: t({ en: 'Edit Config', ko: '설정 편집' }),
      noConfigs: t({
        en: 'No throttling configs',
        ko: '설정된 스로틀링 설정이 없습니다',
      }),
      perMinute: t({ en: 'Per Minute', ko: '분당' }),
      perHour: t({ en: 'Per Hour', ko: '시간당' }),
      perDay: t({ en: 'Per Day', ko: '일당' }),
      burstAllowance: t({ en: 'Burst Allowance', ko: '버스트 허용치' }),
      global: t({ en: 'Global', ko: '전역' }),
      stats: {
        title: t({ en: 'Throttling Stats', ko: '스로틀링 통계' }),
        totalReceived: t({ en: 'Total Received', ko: '총 수신' }),
        totalThrottled: t({ en: 'Throttled', ko: '스로틀됨' }),
        totalPassed: t({ en: 'Passed Through', ko: '통과됨' }),
        throttleRate: t({ en: 'Throttle Rate', ko: '스로틀률' }),
        currentWindowCount: t({ en: 'Current Window', ko: '현재 윈도우' }),
      },
    },

    // Escalation
    escalation: {
      title: t({ en: 'Escalation Policies', ko: '에스컬레이션 정책' }),
      subtitle: t({
        en: 'Configure multi-level escalation for critical alerts',
        ko: '중요 알림에 대한 다단계 에스컬레이션 설정',
      }),
      addPolicy: t({ en: 'Add Policy', ko: '정책 추가' }),
      editPolicy: t({ en: 'Edit Policy', ko: '정책 편집' }),
      noPolicies: t({
        en: 'No escalation policies',
        ko: '설정된 에스컬레이션 정책이 없습니다',
      }),
      levels: t({ en: 'Levels', ko: '레벨' }),
      addLevel: t({ en: 'Add Level', ko: '레벨 추가' }),
      delayMinutes: t({ en: 'Delay (minutes)', ko: '지연 (분)' }),
      targets: t({ en: 'Targets', ko: '대상' }),
      addTarget: t({ en: 'Add Target', ko: '대상 추가' }),
      autoResolve: t({ en: 'Auto-resolve on Success', ko: '성공 시 자동 해결' }),
      maxEscalations: t({ en: 'Max Escalations', ko: '최대 에스컬레이션' }),
      stats: {
        title: t({ en: 'Escalation Stats', ko: '에스컬레이션 통계' }),
        totalIncidents: t({ en: 'Total Incidents', ko: '전체 인시던트' }),
        activeCount: t({ en: 'Active', ko: '활성' }),
        avgResolutionTime: t({ en: 'Avg Resolution Time', ko: '평균 해결 시간' }),
      },
      // Level Builder UI
      levelBuilder: {
        description: t({
          en: 'Configure notification targets and delays for each escalation level',
          ko: '각 에스컬레이션 레벨에 대한 알림 대상 및 지연 시간 설정',
        }),
        levelLabel: t({ en: 'Level', ko: '레벨' }),
        noLevels: t({
          en: 'No escalation levels configured. Add at least one level.',
          ko: '에스컬레이션 레벨이 설정되지 않았습니다. 최소 하나의 레벨을 추가하세요.',
        }),
        addFirstLevel: t({ en: 'Add First Level', ko: '첫 번째 레벨 추가' }),
        noTargets: t({
          en: 'No notification targets. Add users, groups, on-call schedules, or channels.',
          ko: '알림 대상이 없습니다. 사용자, 그룹, 온콜 스케줄 또는 채널을 추가하세요.',
        }),
        immediate: t({ en: 'Immediate', ko: '즉시' }),
        minutes: t({ en: 'minutes', ko: '분' }),
        immediateNote: t({
          en: 'This level will trigger immediately when an incident is created',
          ko: '이 레벨은 인시던트 생성 시 즉시 트리거됩니다',
        }),
        selectChannel: t({ en: 'Channel', ko: '채널' }),
        noChannels: t({
          en: 'No channels configured',
          ko: '설정된 채널이 없습니다',
        }),
        messageTemplate: t({ en: 'Custom Message Template', ko: '사용자 정의 메시지 템플릿' }),
        messageTemplatePlaceholder: t({
          en: 'Optional: Custom message template for this level. Use {incident_ref}, {level}, {policy_name} as variables.',
          ko: '선택사항: 이 레벨에 대한 사용자 정의 메시지 템플릿. {incident_ref}, {level}, {policy_name}을 변수로 사용하세요.',
        }),
        timelinePreview: t({ en: 'Escalation Timeline Preview', ko: '에스컬레이션 타임라인 미리보기' }),
        totalTime: t({ en: 'Total escalation time', ko: '총 에스컬레이션 시간' }),
        validationWarning: t({
          en: 'Some levels have no targets or empty identifiers',
          ko: '일부 레벨에 대상이 없거나 식별자가 비어 있습니다',
        }),
        placeholders: {
          user: t({ en: 'user@example.com', ko: 'user@example.com' }),
          group: t({ en: 'Group name or ID', ko: '그룹 이름 또는 ID' }),
          oncall: t({ en: 'On-call schedule ID', ko: '온콜 스케줄 ID' }),
          channel: t({ en: '#channel-name', ko: '#채널-이름' }),
        },
        moveUp: t({ en: 'Move up', ko: '위로 이동' }),
        moveDown: t({ en: 'Move down', ko: '아래로 이동' }),
      },
    },

    // Target Types
    targetTypes: {
      user: t({ en: 'User', ko: '사용자' }),
      group: t({ en: 'Group', ko: '그룹' }),
      oncall: t({ en: 'On-Call', ko: '온콜' }),
      channel: t({ en: 'Channel', ko: '채널' }),
    },

    // Incidents
    incidents: {
      title: t({ en: 'Escalation Incidents', ko: '에스컬레이션 인시던트' }),
      subtitle: t({
        en: 'Active and recent escalation incidents',
        ko: '활성 및 최근 에스컬레이션 인시던트',
      }),
      noIncidents: t({
        en: 'No incidents',
        ko: '인시던트가 없습니다',
      }),
      incidentRef: t({ en: 'Reference', ko: '참조' }),
      currentLevel: t({ en: 'Current Level', ko: '현재 레벨' }),
      escalationCount: t({ en: 'Escalation Count', ko: '에스컬레이션 횟수' }),
      nextEscalation: t({ en: 'Next Escalation', ko: '다음 에스컬레이션' }),
      acknowledgedBy: t({ en: 'Acknowledged By', ko: '확인자' }),
      resolvedBy: t({ en: 'Resolved By', ko: '해결자' }),
      timeline: t({ en: 'Timeline', ko: '타임라인' }),
      actions: {
        acknowledge: t({ en: 'Acknowledge', ko: '확인' }),
        resolve: t({ en: 'Resolve', ko: '해결' }),
      },
    },

    // Escalation States
    states: {
      pending: t({ en: 'Pending', ko: '대기 중' }),
      triggered: t({ en: 'Triggered', ko: '트리거됨' }),
      acknowledged: t({ en: 'Acknowledged', ko: '확인됨' }),
      escalated: t({ en: 'Escalated', ko: '에스컬레이션됨' }),
      resolved: t({ en: 'Resolved', ko: '해결됨' }),
    },

    // Timeline visualization
    timeline: {
      // Event types
      created: t({ en: 'Created', ko: '생성됨' }),
      noEvents: t({ en: 'No events recorded', ko: '기록된 이벤트가 없습니다' }),
      events: t({ en: 'events', ko: '개 이벤트' }),
      currentState: t({ en: 'Current State', ko: '현재 상태' }),

      // Dialog and sections
      incidentDetails: t({ en: 'Incident Details', ko: '인시던트 상세' }),
      status: t({ en: 'Status', ko: '상태' }),
      policySummary: t({ en: 'Escalation Policy', ko: '에스컬레이션 정책' }),
      technicalDetails: t({ en: 'Technical Details', ko: '기술적 세부사항' }),
      close: t({ en: 'Close', ko: '닫기' }),

      // Policy summary
      currentLevel: t({ en: 'Current Level', ko: '현재 레벨' }),
      maxLevel: t({ en: 'Max', ko: '최대' }),
      escalationLevels: t({ en: 'Escalation Levels', ko: '에스컬레이션 레벨' }),

      // Countdown
      toLevel: t({ en: 'To Level', ko: '레벨로' }),
      remaining: t({ en: 'remaining', ko: '남음' }),

      // Quick actions
      quickActions: t({ en: 'Quick Actions', ko: '빠른 작업' }),
      acknowledging: t({ en: 'Acknowledging...', ko: '확인 중...' }),
      acknowledgeHint: t({
        en: 'Mark this incident as seen and being handled',
        ko: '이 인시던트를 확인하고 처리 중으로 표시',
      }),
      resolveHint: t({
        en: 'Mark this incident as resolved',
        ko: '이 인시던트를 해결됨으로 표시',
      }),
      resolutionNote: t({
        en: 'Resolution Note (optional)',
        ko: '해결 메모 (선택사항)',
      }),
      resolutionPlaceholder: t({
        en: 'Describe how the incident was resolved...',
        ko: '인시던트가 어떻게 해결되었는지 설명...',
      }),
      cancelResolve: t({ en: 'Cancel', ko: '취소' }),
      confirmResolve: t({ en: 'Confirm Resolve', ko: '해결 확인' }),
      resolving: t({ en: 'Resolving...', ko: '해결 중...' }),

      // Technical details
      incidentId: t({ en: 'Incident ID', ko: '인시던트 ID' }),
      policyId: t({ en: 'Policy ID', ko: '정책 ID' }),
      notificationId: t({ en: 'Notification ID', ko: '알림 ID' }),

      // Duration labels
      duration: t({ en: 'Duration', ko: '소요 시간' }),
      timeBetween: t({ en: 'Time between events', ko: '이벤트 간 시간' }),
    },

    // Config Export
    configExport: {
      title: t({ en: 'Config Import/Export', ko: '설정 가져오기/내보내기' }),
      description: t({
        en: 'Export or import notification configurations as JSON files',
        ko: '알림 설정을 JSON 파일로 내보내거나 가져오기',
      }),
      exportTitle: t({ en: 'Export Configuration', ko: '설정 내보내기' }),
      exportButton: t({ en: 'Export as JSON', ko: 'JSON으로 내보내기' }),
      exporting: t({ en: 'Exporting...', ko: '내보내는 중...' }),
      exportSuccess: t({ en: 'Configuration exported', ko: '설정이 내보내졌습니다' }),
      exportSuccessDesc: t({
        en: 'Download started successfully',
        ko: '다운로드가 시작되었습니다',
      }),
      exportError: t({ en: 'Export failed', ko: '내보내기 실패' }),
    },

    // Config Import
    configImport: {
      importTitle: t({ en: 'Import Configuration', ko: '설정 가져오기' }),
      importDescription: t({
        en: 'Import notification configurations from a previously exported JSON file',
        ko: '이전에 내보낸 JSON 파일에서 알림 설정 가져오기',
      }),
      importButton: t({ en: 'Import from File', ko: '파일에서 가져오기' }),
      dialogTitle: t({ en: 'Import Configuration', ko: '설정 가져오기' }),
      dialogDescriptionSelect: t({
        en: 'Select a JSON configuration file to import',
        ko: '가져올 JSON 설정 파일을 선택하세요',
      }),
      dialogDescriptionPreview: t({
        en: 'Review the configurations before importing',
        ko: '가져오기 전에 설정을 검토하세요',
      }),
      dialogDescriptionImporting: t({
        en: 'Importing configurations...',
        ko: '설정을 가져오는 중...',
      }),
      dialogDescriptionComplete: t({
        en: 'Import operation completed',
        ko: '가져오기 작업이 완료되었습니다',
      }),
      selectFile: t({ en: 'Select Configuration File', ko: '설정 파일 선택' }),
      supportedFormats: t({ en: 'JSON files only', ko: 'JSON 파일만 지원' }),
      browseFiles: t({ en: 'Browse Files', ko: '파일 찾아보기' }),
      parsing: t({ en: 'Parsing...', ko: '분석 중...' }),
      newConfigs: t({ en: 'new', ko: '새로운' }),
      conflicts: t({ en: 'conflicts', ko: '충돌' }),
      conflictsDetected: t({ en: 'Conflicts Detected', ko: '충돌 감지됨' }),
      configType: t({ en: 'Type', ko: '유형' }),
      importingName: t({ en: 'Importing', ko: '가져올 항목' }),
      existingName: t({ en: 'Existing', ko: '기존 항목' }),
      conflictResolution: t({ en: 'Conflict Resolution', ko: '충돌 해결 방법' }),
      resolutionSkip: t({ en: 'Skip existing', ko: '기존 항목 건너뛰기' }),
      resolutionOverwrite: t({ en: 'Overwrite existing', ko: '기존 항목 덮어쓰기' }),
      resolutionRename: t({ en: 'Create with new ID', ko: '새 ID로 생성' }),
      skipDescription: t({
        en: 'Skip configurations that already exist (safest option)',
        ko: '이미 존재하는 설정은 건너뜁니다 (가장 안전한 옵션)',
      }),
      overwriteDescription: t({
        en: 'Replace existing configurations with imported ones',
        ko: '기존 설정을 가져온 설정으로 대체합니다',
      }),
      renameDescription: t({
        en: 'Create new configurations with modified IDs and names',
        ko: '변경된 ID와 이름으로 새 설정을 생성합니다',
      }),
      backToSelect: t({ en: 'Back', ko: '뒤로' }),
      startImport: t({ en: 'Import', ko: '가져오기' }),
      importing: t({ en: 'Importing...', ko: '가져오는 중...' }),
      pleaseWait: t({ en: 'Please wait...', ko: '잠시 기다려주세요...' }),
      importComplete: t({ en: 'Import Complete', ko: '가져오기 완료' }),
      importFailed: t({ en: 'Import Failed', ko: '가져오기 실패' }),
      importSuccess: t({ en: 'Configuration imported successfully', ko: '설정을 성공적으로 가져왔습니다' }),
      importPartial: t({ en: 'Import completed with errors', ko: '가져오기가 오류와 함께 완료되었습니다' }),
      created: t({ en: 'Created', ko: '생성됨' }),
      skipped: t({ en: 'Skipped', ko: '건너뜀' }),
      overwritten: t({ en: 'Overwritten', ko: '덮어씀' }),
    },

    // Common
    common: {
      active: t({ en: 'Active', ko: '활성' }),
      inactive: t({ en: 'Inactive', ko: '비활성' }),
      name: t({ en: 'Name', ko: '이름' }),
      description: t({ en: 'Description', ko: '설명' }),
      enabled: t({ en: 'Enabled', ko: '활성화' }),
      created: t({ en: 'Created', ko: '생성됨' }),
      updated: t({ en: 'Updated', ko: '수정됨' }),
    },

    // Success messages
    success: {
      configCreated: t({
        en: 'Configuration created successfully',
        ko: '설정이 생성되었습니다',
      }),
      configUpdated: t({
        en: 'Configuration updated successfully',
        ko: '설정이 수정되었습니다',
      }),
      configDeleted: t({
        en: 'Configuration deleted successfully',
        ko: '설정이 삭제되었습니다',
      }),
      incidentAcknowledged: t({
        en: 'Incident acknowledged',
        ko: '인시던트가 확인되었습니다',
      }),
      incidentResolved: t({
        en: 'Incident resolved',
        ko: '인시던트가 해결되었습니다',
      }),
    },

    // Expression Editor
    expressionEditor: {
      title: t({ en: 'Expression Editor', ko: '표현식 에디터' }),
      expressionLabel: t({ en: 'Expression', ko: '표현식' }),
      placeholder: t({
        en: "Enter a Python-like expression, e.g., severity == 'critical' and pass_rate < 0.9",
        ko: "Python 스타일 표현식을 입력하세요, 예: severity == 'critical' and pass_rate < 0.9",
      }),
      helperText: t({
        en: 'Write a Python-like boolean expression. Click variables on the right to insert them.',
        ko: 'Python 스타일 불리언 표현식을 작성하세요. 오른쪽의 변수를 클릭하여 삽입할 수 있습니다.',
      }),
      contextVariables: t({ en: 'Context Variables', ko: '컨텍스트 변수' }),
      builtinFunctions: t({ en: 'Built-in Functions', ko: '내장 함수' }),
      selectExample: t({ en: 'Select example...', ko: '예제 선택...' }),
      livePreview: t({ en: 'Live Preview', ko: '실시간 미리보기' }),
      result: t({ en: 'Result', ko: '결과' }),
      error: t({ en: 'Error', ko: '오류' }),
      matches: t({ en: 'Matches', ko: '매칭됨' }),
      noMatch: t({ en: 'No Match', ko: '매칭 안됨' }),
      sampleData: t({ en: 'Sample Data', ko: '샘플 데이터' }),
      valid: t({ en: 'Valid', ko: '유효' }),
      invalid: t({ en: 'Invalid', ko: '무효' }),
      advancedSettings: t({ en: 'Advanced Settings', ko: '고급 설정' }),
      timeoutLabel: t({ en: 'Evaluation Timeout', ko: '평가 타임아웃' }),
      timeoutDescription: t({
        en: 'Maximum time allowed for expression evaluation (seconds)',
        ko: '표현식 평가에 허용되는 최대 시간 (초)',
      }),
      validating: t({ en: 'Validating...', ko: '검증 중...' }),
      syntaxError: t({ en: 'Syntax Error', ko: '구문 오류' }),
      securityError: t({ en: 'Security Error', ko: '보안 오류' }),
      timeoutError: t({ en: 'Timeout Error', ko: '타임아웃 오류' }),
      // Variable descriptions
      variables: {
        severity: t({
          en: 'Highest severity level (critical, high, medium, low, info)',
          ko: '최고 심각도 수준 (critical, high, medium, low, info)',
        }),
        issue_count: t({
          en: 'Number of validation issues found',
          ko: '발견된 검증 이슈 수',
        }),
        status: t({
          en: 'Validation status (success, warning, failure, error)',
          ko: '검증 상태 (success, warning, failure, error)',
        }),
        pass_rate: t({
          en: 'Validation pass rate (0.0 to 1.0)',
          ko: '검증 통과율 (0.0 ~ 1.0)',
        }),
        tags: t({
          en: 'List of tags associated with the notification',
          ko: '알림에 연결된 태그 목록',
        }),
        metadata: t({
          en: 'Custom metadata dictionary',
          ko: '사용자 정의 메타데이터 딕셔너리',
        }),
        timestamp: t({
          en: 'When the validation occurred',
          ko: '검증이 발생한 시간',
        }),
        checkpoint_name: t({
          en: 'Name of the validation checkpoint',
          ko: '검증 체크포인트 이름',
        }),
        action_type: t({
          en: 'Type of action (check, learn, profile, compare, scan, mask)',
          ko: '액션 유형 (check, learn, profile, compare, scan, mask)',
        }),
        issues: t({
          en: 'List of issue identifiers',
          ko: '이슈 식별자 목록',
        }),
      },
      // Example expressions
      examples: {
        criticalSeverity: t({ en: 'Critical severity', ko: '심각도 Critical' }),
        highOrCritical: t({ en: 'High or critical severity', ko: '심각도 High 또는 Critical' }),
        lowPassRate: t({ en: 'Low pass rate', ko: '낮은 통과율' }),
        manyIssues: t({ en: 'Many issues', ko: '이슈가 많음' }),
        productionTag: t({ en: 'Production tag', ko: 'Production 태그' }),
        complexCondition: t({ en: 'Complex condition', ko: '복합 조건' }),
      },
    },

    // Jinja2 Editor
    jinja2Editor: {
      title: t({ en: 'Jinja2 Template Editor', ko: 'Jinja2 템플릿 에디터' }),
      templateEditor: t({ en: 'Template', ko: '템플릿' }),
      templatePlaceholder: t({
        en: "Enter Jinja2 template (e.g., {{ severity == 'critical' }})",
        ko: "Jinja2 템플릿을 입력하세요 (예: {{ severity == 'critical' }})",
      }),
      preview: t({ en: 'Preview', ko: '미리보기' }),
      output: t({ en: 'Output', ko: '출력' }),
      noOutput: t({ en: 'No output', ko: '출력 없음' }),
      expectedResult: t({ en: 'Expected Result', ko: '예상 결과' }),
      expectedResultHint: t({
        en: 'The template output is compared against this value',
        ko: '템플릿 출력이 이 값과 비교됩니다',
      }),
      sampleData: t({ en: 'Sample Event Data', ko: '샘플 이벤트 데이터' }),
      variables: t({ en: 'Variables', ko: '변수' }),
      snippets: t({ en: 'Snippets', ko: '스니펫' }),
      filters: t({ en: 'Filters', ko: '필터' }),
      validate: t({ en: 'Validate', ko: '검증' }),
      valid: t({ en: 'Valid', ko: '유효' }),
      invalid: t({ en: 'Invalid', ko: '무효' }),
      // Context variable descriptions
      variableDescriptions: {
        eventSeverity: t({
          en: 'Issue severity level (critical, high, medium, low, info)',
          ko: '이슈 심각도 수준 (critical, high, medium, low, info)',
        }),
        eventIssueCount: t({
          en: 'Number of validation issues found',
          ko: '발견된 검증 이슈 수',
        }),
        eventStatus: t({
          en: 'Validation status (success, warning, failure, error)',
          ko: '검증 상태 (success, warning, failure, error)',
        }),
        eventPassRate: t({
          en: 'Validation pass rate (0.0 - 1.0)',
          ko: '검증 통과율 (0.0 - 1.0)',
        }),
        eventTags: t({
          en: 'Tags associated with the event',
          ko: '이벤트에 연결된 태그',
        }),
        eventMetadata: t({
          en: 'Additional metadata dictionary',
          ko: '추가 메타데이터 딕셔너리',
        }),
        eventSourceName: t({
          en: 'Name of the data source',
          ko: '데이터 소스 이름',
        }),
        eventValidationName: t({
          en: 'Name of the validation that ran',
          ko: '실행된 검증 이름',
        }),
      },
      // Snippet descriptions
      snippetCategories: {
        expressions: t({ en: 'Expressions', ko: '표현식' }),
        controlFlow: t({ en: 'Control Flow', ko: '제어 흐름' }),
        filters: t({ en: 'Filters', ko: '필터' }),
        comments: t({ en: 'Comments', ko: '주석' }),
      },
      snippetDescriptions: {
        ifElse: t({ en: 'Conditional block', ko: '조건부 블록' }),
        ifElifElse: t({ en: 'Multiple conditions', ko: '다중 조건' }),
        forLoop: t({ en: 'Iterate over items', ko: '항목 반복' }),
        variable: t({ en: 'Output a variable', ko: '변수 출력' }),
        filter: t({ en: 'Apply a filter', ko: '필터 적용' }),
        comment: t({ en: 'Add a comment', ko: '주석 추가' }),
        severityCheck: t({ en: 'Check if severity is critical', ko: '심각도가 critical인지 확인' }),
        highSeverity: t({ en: 'Check high or critical', ko: 'high 또는 critical 확인' }),
        issueThreshold: t({ en: 'Check issue count threshold', ko: '이슈 수 임계값 확인' }),
        passRateCheck: t({ en: 'Check pass rate below threshold', ko: '통과율 임계값 미만 확인' }),
        tagContains: t({ en: 'Check if tag exists', ko: '태그 존재 확인' }),
        combinedCondition: t({ en: 'Multiple conditions combined', ko: '다중 조건 결합' }),
      },
      // Filter descriptions
      filterDescriptions: {
        severityLevel: t({
          en: 'Convert severity string to numeric level (5=critical to 1=info)',
          ko: '심각도 문자열을 숫자 레벨로 변환 (5=critical ~ 1=info)',
        }),
        isCritical: t({
          en: 'Check if severity is critical',
          ko: '심각도가 critical인지 확인',
        }),
        isHighOrCritical: t({
          en: 'Check if severity is high or critical',
          ko: '심각도가 high 또는 critical인지 확인',
        }),
        formatPercentage: t({
          en: 'Format number as percentage',
          ko: '숫자를 백분율로 포맷',
        }),
        formatIssues: t({
          en: 'Format issue list for display',
          ko: '이슈 목록을 표시용으로 포맷',
        }),
        truncateText: t({
          en: 'Truncate text to max length',
          ko: '텍스트를 최대 길이로 자르기',
        }),
        pluralize: t({
          en: 'Return singular or plural form',
          ko: '단수 또는 복수 형태 반환',
        }),
        upper: t({ en: 'Convert to uppercase', ko: '대문자로 변환' }),
        lower: t({ en: 'Convert to lowercase', ko: '소문자로 변환' }),
        title: t({ en: 'Convert to title case', ko: '제목 케이스로 변환' }),
        default: t({
          en: 'Provide default value if undefined',
          ko: '미정의 시 기본값 제공',
        }),
        length: t({ en: 'Get length of string or list', ko: '문자열 또는 리스트의 길이 가져오기' }),
        join: t({ en: 'Join list items with separator', ko: '구분자로 리스트 항목 결합' }),
        first: t({ en: 'Get first item of list', ko: '리스트의 첫 번째 항목 가져오기' }),
        last: t({ en: 'Get last item of list', ko: '리스트의 마지막 항목 가져오기' }),
        round: t({ en: 'Round number to decimal places', ko: '숫자를 소수점 자리로 반올림' }),
        int: t({ en: 'Convert to integer', ko: '정수로 변환' }),
      },
      // Validation messages
      validationMessages: {
        templateEmpty: t({ en: 'Template cannot be empty', ko: '템플릿은 비워둘 수 없습니다' }),
        syntaxError: t({ en: 'Template syntax error', ko: '템플릿 구문 오류' }),
        renderError: t({ en: 'Template rendering error', ko: '템플릿 렌더링 오류' }),
        matchesExpected: t({ en: 'Output matches expected result', ko: '출력이 예상 결과와 일치합니다' }),
        doesNotMatchExpected: t({
          en: 'Output does not match expected result',
          ko: '출력이 예상 결과와 일치하지 않습니다',
        }),
      },
    },

    // Error messages
    errors: {
      loadFailed: t({
        en: 'Failed to load data',
        ko: '데이터 로드에 실패했습니다',
      }),
      createFailed: t({
        en: 'Failed to create configuration',
        ko: '설정 생성에 실패했습니다',
      }),
      updateFailed: t({
        en: 'Failed to update configuration',
        ko: '설정 수정에 실패했습니다',
      }),
      deleteFailed: t({
        en: 'Failed to delete configuration',
        ko: '설정 삭제에 실패했습니다',
      }),
      acknowledgeFailed: t({
        en: 'Failed to acknowledge incident',
        ko: '인시던트 확인에 실패했습니다',
      }),
      resolveFailed: t({
        en: 'Failed to resolve incident',
        ko: '인시던트 해결에 실패했습니다',
      }),
    },
  },
} satisfies Dictionary

export default notificationsAdvancedContent
