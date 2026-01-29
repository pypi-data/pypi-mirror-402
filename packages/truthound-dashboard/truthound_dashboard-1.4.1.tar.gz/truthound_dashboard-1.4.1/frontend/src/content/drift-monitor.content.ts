/**
 * Drift monitoring translations.
 *
 * Contains translations for automatic drift monitoring features.
 */
import { t, type Dictionary } from 'intlayer'

const driftMonitorContent = {
  key: 'driftMonitor',
  content: {
    title: t({ en: 'Drift Monitoring', ko: '드리프트 모니터링' }),
    subtitle: t({
      en: 'Automatic drift detection with alerts',
      ko: '알림과 함께하는 자동 드리프트 감지',
    }),

    // Tabs
    tabs: {
      monitors: t({ en: 'Monitors', ko: '모니터' }),
      alerts: t({ en: 'Alerts', ko: '알림' }),
      trends: t({ en: 'Trends', ko: '트렌드' }),
      basic: t({ en: 'Basic', ko: '기본' }),
      performance: t({ en: 'Performance', ko: '성능' }),
    },

    // Monitor Management
    monitor: {
      createMonitor: t({ en: 'Create Monitor', ko: '모니터 생성' }),
      editMonitor: t({ en: 'Edit Monitor', ko: '모니터 편집' }),
      deleteMonitor: t({ en: 'Delete Monitor', ko: '모니터 삭제' }),
      runNow: t({ en: 'Run Now', ko: '지금 실행' }),
      pause: t({ en: 'Pause', ko: '일시정지' }),
      resume: t({ en: 'Resume', ko: '재개' }),

      // Form fields
      name: t({ en: 'Monitor Name', ko: '모니터 이름' }),
      baselineSource: t({ en: 'Baseline Source', ko: '기준 소스' }),
      currentSource: t({ en: 'Current Source', ko: '현재 소스' }),
      schedule: t({ en: 'Schedule', ko: '스케줄' }),
      method: t({ en: 'Detection Method', ko: '탐지 방법' }),
      threshold: t({ en: 'Drift Threshold', ko: '드리프트 임계값' }),
      columns: t({ en: 'Columns to Monitor', ko: '모니터링할 컬럼' }),
      alertOnDrift: t({ en: 'Alert on Drift', ko: '드리프트 시 알림' }),
      criticalThreshold: t({ en: 'Critical Alert Threshold', ko: '심각 알림 임계값' }),
      highThreshold: t({ en: 'High Alert Threshold', ko: '높음 알림 임계값' }),
      notificationChannels: t({ en: 'Notification Channels', ko: '알림 채널' }),
    },

    // Status
    status: {
      active: t({ en: 'Active', ko: '활성' }),
      paused: t({ en: 'Paused', ko: '일시정지' }),
      error: t({ en: 'Error', ko: '오류' }),
    },

    // Alert Severity
    severity: {
      critical: t({ en: 'Critical', ko: '심각' }),
      high: t({ en: 'High', ko: '높음' }),
      medium: t({ en: 'Medium', ko: '중간' }),
      low: t({ en: 'Low', ko: '낮음' }),
    },

    // Alert Status
    alertStatus: {
      open: t({ en: 'Open', ko: '열림' }),
      acknowledged: t({ en: 'Acknowledged', ko: '확인됨' }),
      resolved: t({ en: 'Resolved', ko: '해결됨' }),
      ignored: t({ en: 'Ignored', ko: '무시됨' }),
    },

    // Alert Actions
    alertActions: {
      acknowledge: t({ en: 'Acknowledge', ko: '확인' }),
      resolve: t({ en: 'Resolve', ko: '해결' }),
      ignore: t({ en: 'Ignore', ko: '무시' }),
      addNote: t({ en: 'Add Note', ko: '메모 추가' }),
      viewDetails: t({ en: 'View Details', ko: '상세 보기' }),
    },

    // Stats
    stats: {
      totalMonitors: t({ en: 'Total Monitors', ko: '전체 모니터' }),
      activeMonitors: t({ en: 'Active Monitors', ko: '활성 모니터' }),
      monitorsWithDrift: t({ en: 'With Drift', ko: '드리프트 발생' }),
      openAlerts: t({ en: 'Open Alerts', ko: '미해결 알림' }),
      criticalAlerts: t({ en: 'Critical', ko: '심각' }),
      driftRate: t({ en: 'Drift Rate', ko: '드리프트 비율' }),
      lastRun: t({ en: 'Last Run', ko: '마지막 실행' }),
      totalRuns: t({ en: 'Total Runs', ko: '전체 실행' }),
      consecutiveDrift: t({ en: 'Consecutive Drift', ko: '연속 드리프트' }),
    },

    // Schedule Presets
    schedulePresets: {
      hourly: t({ en: 'Every Hour', ko: '매시간' }),
      daily: t({ en: 'Daily', ko: '매일' }),
      weekly: t({ en: 'Weekly', ko: '매주' }),
      custom: t({ en: 'Custom', ko: '사용자 정의' }),
    },

    // Trend
    trend: {
      title: t({ en: 'Drift Trend', ko: '드리프트 트렌드' }),
      period: t({ en: 'Period', ko: '기간' }),
      last7Days: t({ en: 'Last 7 Days', ko: '최근 7일' }),
      last30Days: t({ en: 'Last 30 Days', ko: '최근 30일' }),
      last90Days: t({ en: 'Last 90 Days', ko: '최근 90일' }),
      avgDrift: t({ en: 'Avg. Drift', ko: '평균 드리프트' }),
      maxDrift: t({ en: 'Max Drift', ko: '최대 드리프트' }),
      driftOccurrence: t({ en: 'Drift Occurrence', ko: '드리프트 발생률' }),
    },

    // Empty States
    empty: {
      noMonitors: t({ en: 'No drift monitors', ko: '드리프트 모니터 없음' }),
      noMonitorsDesc: t({
        en: 'Create a monitor to automatically detect drift between data sources',
        ko: '데이터 소스 간 드리프트를 자동으로 감지하는 모니터를 생성하세요',
      }),
      noAlerts: t({ en: 'No alerts', ko: '알림 없음' }),
      noAlertsDesc: t({
        en: 'No drift alerts have been triggered',
        ko: '발생한 드리프트 알림이 없습니다',
      }),
      noRunData: t({ en: 'No run data available', ko: '실행 데이터 없음' }),
      runMonitorFirst: t({
        en: 'Run the monitor to see column details',
        ko: '컬럼 상세 정보를 보려면 모니터를 실행하세요',
      }),
    },

    // Messages
    messages: {
      monitorCreated: t({ en: 'Monitor created', ko: '모니터가 생성되었습니다' }),
      monitorUpdated: t({ en: 'Monitor updated', ko: '모니터가 업데이트되었습니다' }),
      monitorDeleted: t({ en: 'Monitor deleted', ko: '모니터가 삭제되었습니다' }),
      monitorRunStarted: t({ en: 'Monitor run started', ko: '모니터 실행이 시작되었습니다' }),
      alertAcknowledged: t({ en: 'Alert acknowledged', ko: '알림이 확인되었습니다' }),
      alertResolved: t({ en: 'Alert resolved', ko: '알림이 해결되었습니다' }),
      driftDetected: t({ en: 'Drift detected!', ko: '드리프트가 감지되었습니다!' }),
      noDriftDetected: t({ en: 'No drift detected', ko: '드리프트가 감지되지 않았습니다' }),
    },

    // Confirmation
    confirm: {
      deleteMonitor: t({
        en: 'Are you sure you want to delete this monitor?',
        ko: '이 모니터를 삭제하시겠습니까?',
      }),
      pauseMonitor: t({
        en: 'Are you sure you want to pause this monitor?',
        ko: '이 모니터를 일시정지하시겠습니까?',
      }),
    },

    // Table Headers
    table: {
      name: t({ en: 'Name', ko: '이름' }),
      sources: t({ en: 'Sources', ko: '소스' }),
      schedule: t({ en: 'Schedule', ko: '스케줄' }),
      status: t({ en: 'Status', ko: '상태' }),
      lastRun: t({ en: 'Last Run', ko: '마지막 실행' }),
      driftStatus: t({ en: 'Drift Status', ko: '드리프트 상태' }),
      actions: t({ en: 'Actions', ko: '작업' }),
      severity: t({ en: 'Severity', ko: '심각도' }),
      message: t({ en: 'Message', ko: '메시지' }),
      alertTime: t({ en: 'Alert Time', ko: '알림 시간' }),
    },

    // Column Drilldown
    columnDrilldown: {
      title: t({ en: 'Column Drift Analysis', ko: '컬럼 드리프트 분석' }),
      totalColumns: t({ en: 'columns', ko: '개 컬럼' }),
      drifted: t({ en: 'drifted', ko: '드리프트' }),
      selectColumn: t({
        en: 'Select a column to view details',
        ko: '상세 정보를 보려면 컬럼을 선택하세요',
      }),
      noResults: t({
        en: 'No columns match the filter criteria',
        ko: '필터 조건에 맞는 컬럼이 없습니다',
      }),
      searchPlaceholder: t({ en: 'Search columns...', ko: '컬럼 검색...' }),
      viewDetails: t({ en: 'View Column Details', ko: '컬럼 상세 보기' }),
      distribution: t({ en: 'Distribution Comparison', ko: '분포 비교' }),
      baseline: t({ en: 'Baseline', ko: '기준' }),
      current: t({ en: 'Current', ko: '현재' }),
      overlay: t({ en: 'Overlay', ko: '오버레이' }),
      smooth: t({ en: 'Smooth', ko: '스무딩' }),

      // Tabs
      tabs: {
        distribution: t({ en: 'Distribution', ko: '분포' }),
        statistics: t({ en: 'Statistics', ko: '통계' }),
      },

      // Filter options
      filter: {
        all: t({ en: 'All Columns', ko: '전체 컬럼' }),
        drifted: t({ en: 'Drifted Only', ko: '드리프트만' }),
        notDrifted: t({ en: 'Not Drifted', ko: '드리프트 없음' }),
        high: t({ en: 'High Level', ko: '높음 수준' }),
        medium: t({ en: 'Medium Level', ko: '중간 수준' }),
        low: t({ en: 'Low Level', ko: '낮음 수준' }),
      },

      // Sort options
      sort: {
        drift: t({ en: 'By Drift', ko: '드리프트순' }),
        level: t({ en: 'By Level', ko: '수준순' }),
        pvalue: t({ en: 'By P-Value', ko: 'P값순' }),
        name: t({ en: 'By Name', ko: '이름순' }),
      },

      // Drift levels
      levels: {
        high: t({ en: 'High', ko: '높음' }),
        medium: t({ en: 'Medium', ko: '중간' }),
        low: t({ en: 'Low', ko: '낮음' }),
        none: t({ en: 'None', ko: '없음' }),
      },

      // Test results
      testResults: t({ en: 'Statistical Test Results', ko: '통계 검정 결과' }),
      testMethod: t({ en: 'Test Method', ko: '검정 방법' }),
      driftLevel: t({ en: 'Drift Level', ko: '드리프트 수준' }),
      statistic: t({ en: 'Test Statistic', ko: '검정 통계량' }),
      pValue: t({ en: 'P-Value', ko: 'P값' }),
    },

    // Column Statistics
    columnStats: {
      statistic: t({ en: 'Statistic', ko: '통계' }),
      baseline: t({ en: 'Baseline', ko: '기준' }),
      current: t({ en: 'Current', ko: '현재' }),
      change: t({ en: 'Change', ko: '변화' }),
      mean: t({ en: 'Mean', ko: '평균' }),
      std: t({ en: 'Std Dev', ko: '표준편차' }),
      median: t({ en: 'Median', ko: '중앙값' }),
      min: t({ en: 'Min', ko: '최소값' }),
      max: t({ en: 'Max', ko: '최대값' }),
      q25: t({ en: '25th %ile', ko: '25 백분위' }),
      q75: t({ en: '75th %ile', ko: '75 백분위' }),
      count: t({ en: 'Count', ko: '건수' }),
      nullCount: t({ en: 'Null Count', ko: 'Null 수' }),
      uniqueCount: t({ en: 'Unique Count', ko: '고유값 수' }),
    },

    // Preview Feature
    preview: {
      title: t({ en: 'Preview Drift', ko: '드리프트 미리보기' }),
      previewDrift: t({ en: 'Preview Drift', ko: '드리프트 미리보기' }),
      description: t({
        en: 'Compare two data sources to preview drift results before creating a monitor',
        ko: '모니터 생성 전 두 데이터 소스를 비교하여 드리프트 결과를 미리 확인하세요',
      }),
      runPreview: t({ en: 'Run Preview', ko: '미리보기 실행' }),
      previewResults: t({ en: 'Preview Results', ko: '미리보기 결과' }),
      reviewBeforeCreate: t({
        en: 'Review drift results before creating the monitor',
        ko: '모니터 생성 전 드리프트 결과를 검토하세요',
      }),
      backToConfig: t({ en: 'Back to Configuration', ko: '설정으로 돌아가기' }),
      sameSourceWarning: t({
        en: 'Baseline and current source must be different',
        ko: '기준 소스와 현재 소스가 달라야 합니다',
      }),

      // Results
      driftStatus: t({ en: 'Drift Status', ko: '드리프트 상태' }),
      driftDetected: t({ en: 'Drift Detected', ko: '드리프트 감지됨' }),
      noDrift: t({ en: 'No Drift', ko: '드리프트 없음' }),
      driftPercentage: t({ en: 'Drift Percentage', ko: '드리프트 비율' }),
      columnsAffected: t({ en: 'columns affected', ko: '개 컬럼 영향' }),
      rowComparison: t({ en: 'Row Count', ko: '행 수' }),
      baseline: t({ en: 'Baseline', ko: '기준' }),
      current: t({ en: 'Current', ko: '현재' }),
      configuration: t({ en: 'Configuration', ko: '설정' }),
      mostAffected: t({ en: 'Most Affected Columns', ko: '가장 영향받은 컬럼' }),
      columnResults: t({ en: 'Column Results', ko: '컬럼별 결과' }),

      // Table headers
      column: t({ en: 'Column', ko: '컬럼' }),
      type: t({ en: 'Type', ko: '타입' }),
      status: t({ en: 'Status', ko: '상태' }),
      level: t({ en: 'Level', ko: '수준' }),
      pValue: t({ en: 'P-Value', ko: 'P값' }),
      statistic: t({ en: 'Statistic', ko: '통계량' }),
      testStatistic: t({ en: 'Test Statistic', ko: '검정 통계량' }),
      distributionComparison: t({ en: 'Distribution Comparison', ko: '분포 비교' }),
    },

    // Root Cause Analysis
    rootCause: {
      title: t({ en: 'Root Cause Analysis', ko: '근본 원인 분석' }),
      subtitle: t({
        en: 'Detailed analysis of why drift is occurring',
        ko: '드리프트 발생 원인에 대한 상세 분석',
      }),
      analyzeRootCause: t({ en: 'Analyze Root Cause', ko: '근본 원인 분석' }),
      noData: t({ en: 'No root cause data available', ko: '근본 원인 데이터 없음' }),
      noAnalysis: t({ en: 'No analysis available', ko: '분석 결과 없음' }),
      noDrift: t({
        en: 'No drift detected in any columns',
        ko: '어떤 컬럼에서도 드리프트가 감지되지 않았습니다',
      }),
      totalColumns: t({ en: 'Total Columns', ko: '전체 컬럼' }),
      driftedColumns: t({ en: 'Drifted Columns', ko: '드리프트 컬럼' }),
      confidence: t({ en: 'Confidence', ko: '신뢰도' }),
      analysisTime: t({ en: 'Analysis Time', ko: '분석 시간' }),
      volumeChange: t({ en: 'Data Volume Change', ko: '데이터 볼륨 변화' }),
      causeDistribution: t({ en: 'Cause Distribution', ko: '원인 분포' }),
      columnAnalysis: t({ en: 'Column Analysis', ko: '컬럼 분석' }),
      columnAnalysisDesc: t({
        en: 'Detailed breakdown by column',
        ko: '컬럼별 상세 분석',
      }),
      detectedCauses: t({ en: 'Detected Causes', ko: '감지된 원인' }),
      statisticalShifts: t({ en: 'Statistical Shifts', ko: '통계적 변화' }),

      // Cause Types
      causes: {
        mean_shift: t({ en: 'Mean Shift', ko: '평균 변화' }),
        variance_change: t({ en: 'Variance Change', ko: '분산 변화' }),
        new_categories: t({ en: 'New Categories', ko: '신규 카테고리' }),
        missing_categories: t({ en: 'Missing Categories', ko: '누락된 카테고리' }),
        outlier_introduction: t({ en: 'Outlier Introduction', ko: '이상치 유입' }),
        data_volume_change: t({ en: 'Data Volume Change', ko: '데이터 볼륨 변화' }),
        temporal_pattern: t({ en: 'Temporal Pattern', ko: '시계열 패턴' }),
        distribution_shape_change: t({
          en: 'Distribution Shape Change',
          ko: '분포 형태 변화',
        }),
        null_rate_change: t({ en: 'Null Rate Change', ko: 'Null 비율 변화' }),
      },

      // Remediation Panel
      remediations: t({ en: 'Suggested Actions', ko: '권장 조치' }),
      remediationsDesc: t({
        en: 'Recommended steps to address drift issues',
        ko: '드리프트 문제 해결을 위한 권장 단계',
      }),
      noRemediations: t({ en: 'No actions needed', ko: '조치 필요 없음' }),
      noRemediationsDesc: t({
        en: 'No remediation suggestions at this time',
        ko: '현재 권장 조치 사항이 없습니다',
      }),
      affectedColumns: t({ en: 'Affected Columns', ko: '영향받는 컬럼' }),
      manualReview: t({ en: 'Requires manual review', ko: '수동 검토 필요' }),
      automationAvailable: t({ en: 'Automation available', ko: '자동화 가능' }),
      runAutomation: t({ en: 'Run Automation', ko: '자동화 실행' }),
      investigate: t({ en: 'Investigate', ko: '조사' }),
      dismiss: t({ en: 'Dismiss', ko: '무시' }),
      quickSummary: t({ en: 'Quick Summary', ko: '빠른 요약' }),
      totalSuggestions: t({ en: 'Total suggestions', ko: '전체 제안' }),
      highPriority: t({ en: 'High priority', ko: '높은 우선순위' }),
      automatable: t({ en: 'Automatable', ko: '자동화 가능' }),

      // Actions
      actions: {
        investigate_upstream: t({
          en: 'Investigate Upstream',
          ko: '업스트림 조사',
        }),
        update_baseline: t({ en: 'Update Baseline', ko: '기준 업데이트' }),
        adjust_threshold: t({ en: 'Adjust Threshold', ko: '임계값 조정' }),
        review_data_pipeline: t({
          en: 'Review Data Pipeline',
          ko: '데이터 파이프라인 검토',
        }),
        check_data_source: t({ en: 'Check Data Source', ko: '데이터 소스 확인' }),
        normalize_values: t({ en: 'Normalize Values', ko: '값 정규화' }),
        filter_outliers: t({ en: 'Filter Outliers', ko: '이상치 필터링' }),
        retrain_model: t({ en: 'Retrain Model', ko: '모델 재학습' }),
        acknowledge_expected_change: t({
          en: 'Acknowledge Expected Change',
          ko: '예상된 변경 확인',
        }),
      },
    },

    // Sampling Configuration (Large-Scale Optimization)
    sampling: {
      title: t({ en: 'Sampling Configuration', ko: '샘플링 설정' }),
      description: t({
        en: 'Enable sampling for faster processing of large datasets',
        ko: '대용량 데이터셋의 빠른 처리를 위해 샘플링을 활성화하세요',
      }),
      method: t({ en: 'Sampling Method', ko: '샘플링 방법' }),
      sampleSize: t({ en: 'Sample Size', ko: '샘플 크기' }),
      confidenceLevel: t({ en: 'Confidence Level', ko: '신뢰 수준' }),
      marginOfError: t({ en: 'Margin of Error', ko: '오차 범위' }),
      strataColumn: t({ en: 'Stratification Column', ko: '계층화 컬럼' }),
      estimatedTime: t({ en: 'Est. Time', ko: '예상 시간' }),
      speedup: t({ en: 'Speedup', ko: '속도 향상' }),
      autoEstimate: t({ en: 'Auto-estimated', ko: '자동 추정' }),
      advancedSettings: t({ en: 'Advanced Settings', ko: '고급 설정' }),
      earlyStopThreshold: t({ en: 'Early Stop Threshold', ko: '조기 중단 임계값' }),
      earlyStopDescription: t({
        en: 'Stop processing when this percentage of columns show drift',
        ko: '이 비율의 컬럼에서 드리프트가 감지되면 처리를 중단합니다',
      }),
      maxWorkers: t({ en: 'Max Parallel Workers', ko: '최대 병렬 워커' }),
      largeDatasetNotice: t({ en: 'Large Dataset Detected', ko: '대용량 데이터셋 감지됨' }),
      largeDatasetDescription: t({
        en: 'This dataset has {rows} rows. Sampling is recommended for optimal performance.',
        ko: '이 데이터셋은 {rows} 행을 포함합니다. 최적의 성능을 위해 샘플링을 권장합니다.',
      }),
    },

    // Large Dataset Warning
    largeDataset: {
      title: t({ en: 'Large Dataset Warning', ko: '대용량 데이터셋 경고' }),
      rows: t({ en: 'rows', ko: '행' }),
      description: t({
        en: 'Processing this dataset without sampling may take a long time. We recommend enabling sampling for better performance.',
        ko: '샘플링 없이 이 데이터셋을 처리하면 오랜 시간이 걸릴 수 있습니다. 더 나은 성능을 위해 샘플링을 활성화하는 것을 권장합니다.',
      }),
      fullScan: t({ en: 'Full Scan', ko: '전체 스캔' }),
      withSampling: t({ en: 'With Sampling', ko: '샘플링 사용' }),
      estimatedTime: t({ en: 'Estimated Time', ko: '예상 시간' }),
      faster: t({ en: 'faster', ko: '더 빠름' }),
      recommendations: t({ en: 'Recommendations', ko: '권장 사항' }),
      recommendation1: t({
        en: 'Enable sampling to process only a statistically significant subset',
        ko: '통계적으로 유의미한 부분집합만 처리하도록 샘플링을 활성화하세요',
      }),
      recommendation2: t({
        en: 'Use stratified sampling if you need to ensure category coverage',
        ko: '카테고리 커버리지를 보장해야 한다면 계층화 샘플링을 사용하세요',
      }),
      recommendation3: t({
        en: 'Consider increasing the threshold for faster processing',
        ko: '더 빠른 처리를 위해 임계값을 높이는 것을 고려하세요',
      }),
      enableSampling: t({ en: 'Enable Sampling', ko: '샘플링 활성화' }),
      enableSamplingShort: t({ en: 'Enable', ko: '활성화' }),
      inlineWarning: t({
        en: 'Dataset has {rows} rows. Sampling recommended.',
        ko: '데이터셋에 {rows} 행이 있습니다. 샘플링을 권장합니다.',
      }),
    },

    // Progress Tracking
    progress: {
      running: t({ en: 'Processing...', ko: '처리 중...' }),
      completed: t({ en: 'Completed', ko: '완료됨' }),
      cancelled: t({ en: 'Cancelled', ko: '취소됨' }),
      error: t({ en: 'Error', ko: '오류' }),
      progress: t({ en: 'Progress', ko: '진행률' }),
      chunks: t({ en: 'Chunks', ko: '청크' }),
      rowsProcessed: t({ en: 'Rows Processed', ko: '처리된 행' }),
      elapsed: t({ en: 'Elapsed', ko: '경과 시간' }),
      eta: t({ en: 'ETA', ko: '남은 시간' }),
      cancel: t({ en: 'Cancel', ko: '취소' }),
      earlyStopTriggered: t({ en: 'Early Stop Triggered', ko: '조기 중단 활성화됨' }),
      earlyStopReason: t({
        en: 'Sufficient drift detected to conclude analysis',
        ko: '분석 결론을 내리기에 충분한 드리프트가 감지되었습니다',
      }),
      driftedColumnsFound: t({ en: 'Drifted Columns Found', ko: '드리프트 컬럼 발견' }),
      showDetails: t({ en: 'Show Details', ko: '상세 보기' }),
      hideDetails: t({ en: 'Hide Details', ko: '숨기기' }),
    },
  },
} satisfies Dictionary

export default driftMonitorContent
