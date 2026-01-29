/**
 * Anomaly detection translations.
 *
 * Contains translations for ML-based anomaly detection features.
 */
import { t, type Dictionary } from 'intlayer'

const anomalyContent = {
  key: 'anomaly',
  content: {
    title: t({ en: 'Anomaly Detection', ko: '이상 탐지' }),
    subtitle: t({
      en: 'Detect anomalies using ML algorithms',
      ko: 'ML 알고리즘을 사용하여 이상 탐지',
    }),

    // Actions
    runDetection: t({ en: 'Run Detection', ko: '탐지 실행' }),
    running: t({ en: 'Running...', ko: '실행 중...' }),
    viewDetails: t({ en: 'View Details', ko: '상세 보기' }),
    viewHistory: t({ en: 'View History', ko: '이력 보기' }),
    configure: t({ en: 'Configure', ko: '설정' }),

    // Algorithm selection
    selectAlgorithm: t({ en: 'Select Algorithm', ko: '알고리즘 선택' }),
    algorithmConfig: t({ en: 'Algorithm Configuration', ko: '알고리즘 설정' }),
    defaultConfig: t({ en: 'Using default configuration', ko: '기본 설정 사용' }),

    // Algorithms
    algorithms: {
      isolation_forest: t({ en: 'Isolation Forest', ko: '고립 숲' }),
      lof: t({ en: 'Local Outlier Factor', ko: '지역 이상치 요인' }),
      one_class_svm: t({ en: 'One-Class SVM', ko: '단일 클래스 SVM' }),
      dbscan: t({ en: 'DBSCAN', ko: 'DBSCAN' }),
      statistical: t({ en: 'Statistical', ko: '통계적' }),
      autoencoder: t({ en: 'Autoencoder', ko: '오토인코더' }),
    },

    // Algorithm categories
    categories: {
      tree: t({ en: 'Tree-based', ko: '트리 기반' }),
      density: t({ en: 'Density-based', ko: '밀도 기반' }),
      svm: t({ en: 'SVM', ko: 'SVM' }),
      clustering: t({ en: 'Clustering', ko: '클러스터링' }),
      statistical: t({ en: 'Statistical', ko: '통계적' }),
      neural: t({ en: 'Neural Network', ko: '신경망' }),
    },

    // Algorithm descriptions
    algorithmDescriptions: {
      isolation_forest: t({
        en: 'Tree-based algorithm that isolates anomalies by random partitioning',
        ko: '무작위 분할로 이상치를 격리하는 트리 기반 알고리즘',
      }),
      lof: t({
        en: 'Density-based algorithm comparing local density with neighbors',
        ko: '이웃과 지역 밀도를 비교하는 밀도 기반 알고리즘',
      }),
      one_class_svm: t({
        en: 'SVM trained on normal data to create a decision boundary',
        ko: '정상 데이터로 학습하여 결정 경계를 생성하는 SVM',
      }),
      dbscan: t({
        en: 'Density-based clustering that identifies outliers',
        ko: '이상치를 식별하는 밀도 기반 클러스터링',
      }),
      statistical: t({
        en: 'Z-score, IQR, or MAD based detection',
        ko: 'Z-score, IQR 또는 MAD 기반 탐지',
      }),
      autoencoder: t({
        en: 'Neural network with high reconstruction error for anomalies',
        ko: '이상치에 대해 높은 재구성 오류를 갖는 신경망',
      }),
    },

    // Parameters
    parameters: {
      n_estimators: t({ en: 'Number of Trees', ko: '트리 수' }),
      contamination: t({ en: 'Contamination', ko: '오염도' }),
      n_neighbors: t({ en: 'Number of Neighbors', ko: '이웃 수' }),
      kernel: t({ en: 'Kernel', ko: '커널' }),
      nu: t({ en: 'Nu', ko: 'Nu' }),
      eps: t({ en: 'Epsilon', ko: '엡실론' }),
      min_samples: t({ en: 'Minimum Samples', ko: '최소 샘플' }),
      method: t({ en: 'Method', ko: '방법' }),
      threshold: t({ en: 'Threshold', ko: '임계값' }),
      encoding_dim: t({ en: 'Encoding Dimension', ko: '인코딩 차원' }),
      epochs: t({ en: 'Epochs', ko: '에포크' }),
      threshold_percentile: t({ en: 'Threshold Percentile', ko: '임계값 백분위수' }),
    },

    // Results
    anomaliesFound: t({ en: 'Anomalies Found', ko: '발견된 이상' }),
    anomalyRate: t({ en: 'Anomaly Rate', ko: '이상 비율' }),
    totalRows: t({ en: 'Total Rows', ko: '전체 행' }),
    columnsAnalyzed: t({ en: 'Columns Analyzed', ko: '분석된 컬럼' }),
    duration: t({ en: 'Duration', ko: '소요 시간' }),
    anomalyScore: t({ en: 'Anomaly Score', ko: '이상 점수' }),
    rowIndex: t({ en: 'Row Index', ko: '행 인덱스' }),

    // Column summary
    columnSummary: t({ en: 'Column Summary', ko: '컬럼 요약' }),
    columnName: t({ en: 'Column', ko: '컬럼' }),
    columnAnomalies: t({ en: 'Anomalies', ko: '이상' }),
    meanScore: t({ en: 'Mean Score', ko: '평균 점수' }),
    topAnomalies: t({ en: 'Top Anomalies', ko: '상위 이상치' }),

    // Status
    status: {
      pending: t({ en: 'Pending', ko: '대기 중' }),
      running: t({ en: 'Running', ko: '실행 중' }),
      success: t({ en: 'Success', ko: '성공' }),
      error: t({ en: 'Error', ko: '오류' }),
    },

    // Empty states
    noDetectionsYet: t({ en: 'No detections yet', ko: '탐지 기록 없음' }),
    noDetectionsDesc: t({
      en: 'Run anomaly detection to find outliers in your data',
      ko: '이상 탐지를 실행하여 데이터에서 이상치를 찾으세요',
    }),
    noAnomaliesFound: t({
      en: 'No anomalies detected',
      ko: '이상이 감지되지 않았습니다',
    }),

    // Success messages
    detectionStarted: t({ en: 'Detection started', ko: '탐지가 시작되었습니다' }),
    detectionComplete: t({ en: 'Detection complete', ko: '탐지 완료' }),

    // Error messages
    detectionFailed: t({ en: 'Detection failed', ko: '탐지 실패' }),
    errorLoadingHistory: t({ en: 'Failed to load detection history', ko: '탐지 이력 로드 실패' }),
    errorLoadingAlgorithms: t({ en: 'Failed to load algorithms', ko: '알고리즘 로드 실패' }),

    // History
    detectionHistory: t({ en: 'Detection History', ko: '탐지 이력' }),
    latestDetection: t({ en: 'Latest Detection', ko: '최근 탐지' }),
    previousDetections: t({ en: 'Previous Detections', ko: '이전 탐지' }),
    ranAt: t({ en: 'Ran at', ko: '실행 시간' }),

    // Algorithm info
    pros: t({ en: 'Advantages', ko: '장점' }),
    cons: t({ en: 'Limitations', ko: '제한사항' }),
    bestFor: t({ en: 'Best for', ko: '최적 사용' }),
    requiresScaling: t({ en: 'Requires data scaling', ko: '데이터 스케일링 필요' }),

    // Config
    selectColumns: t({ en: 'Select Columns', ko: '컬럼 선택' }),
    allNumericColumns: t({ en: 'All numeric columns', ko: '모든 숫자 컬럼' }),
    sampleSize: t({ en: 'Sample Size', ko: '샘플 크기' }),
    sampleSizeHint: t({
      en: 'Leave empty to analyze all rows',
      ko: '비워두면 모든 행을 분석합니다',
    }),

    // Tabs
    configTab: t({ en: 'Configuration', ko: '설정' }),
    resultsTab: t({ en: 'Results', ko: '결과' }),
    historyTab: t({ en: 'History', ko: '이력' }),
    results: t({ en: 'Results', ko: '결과' }),
    history: t({ en: 'History', ko: '이력' }),

    // Chart labels
    scoreDistribution: t({ en: 'Score Distribution', ko: '점수 분포' }),
    anomalyByColumn: t({ en: 'Anomalies by Column', ko: '컬럼별 이상' }),

    // Table headers
    statusLabel: t({ en: 'Status', ko: '상태' }),
    algorithm: t({ en: 'Algorithm', ko: '알고리즘' }),
    anomalyCount: t({ en: 'Anomalies', ko: '이상 수' }),
    runAt: t({ en: 'Run at', ko: '실행 시간' }),

    // Empty states for panel
    noHistory: t({ en: 'No detection history', ko: '탐지 이력 없음' }),
    noResults: t({ en: 'No results yet', ko: '결과 없음' }),
    runDetectionFirst: t({
      en: 'Run detection to see results here',
      ko: '결과를 보려면 탐지를 실행하세요',
    }),

    // Config form
    configureParams: t({ en: 'Configure Parameters', ko: '파라미터 설정' }),

    // Anomaly records
    anomalyRecords: t({ en: 'Anomaly Records', ko: '이상 기록' }),
    actions: t({ en: 'Actions', ko: '작업' }),

    // Explainability (SHAP/LIME)
    explainTitle: t({ en: 'Anomaly Explanation', ko: '이상 설명' }),
    explainDescription: t({
      en: 'SHAP-based feature importance analysis explains why this row is anomalous',
      ko: 'SHAP 기반 특징 중요도 분석으로 이 행이 이상인 이유를 설명합니다',
    }),
    explainAnomaly: t({ en: 'Explain Anomaly', ko: '이상 설명' }),
    explainError: t({ en: 'Failed to generate explanation', ko: '설명 생성 실패' }),
    generatingExplanations: t({
      en: 'Generating SHAP explanations...',
      ko: 'SHAP 설명 생성 중...',
    }),
    noExplanationsYet: t({
      en: 'No explanations generated yet',
      ko: '아직 설명이 생성되지 않았습니다',
    }),
    generateExplanations: t({ en: 'Generate Explanations', ko: '설명 생성' }),
    retry: t({ en: 'Retry', ko: '다시 시도' }),
    selectRow: t({ en: 'Select Row', ko: '행 선택' }),

    // Explanation tabs
    summaryTab: t({ en: 'Summary', ko: '요약' }),
    chartTab: t({ en: 'Chart', ko: '차트' }),
    tableTab: t({ en: 'Table', ko: '테이블' }),

    // Feature contributions
    featureContributions: t({ en: 'Feature Contributions', ko: '특징 기여도' }),
    featureName: t({ en: 'Feature', ko: '특징' }),
    featureValue: t({ en: 'Value', ko: '값' }),
    shapValue: t({ en: 'SHAP Value', ko: 'SHAP 값' }),
    contribution: t({ en: 'Contribution', ko: '기여도' }),

    // Algorithm comparison
    comparison: {
      title: t({ en: 'Compare Algorithms', ko: '알고리즘 비교' }),
      description: t({
        en: 'Select multiple algorithms to compare their anomaly detection results side-by-side.',
        ko: '여러 알고리즘을 선택하여 이상 탐지 결과를 나란히 비교하세요.',
      }),
      compareAlgorithms: t({ en: 'Compare Algorithms', ko: '알고리즘 비교' }),

      // Tabs
      selectTab: t({ en: 'Select', ko: '선택' }),
      resultsTab: t({ en: 'Results', ko: '결과' }),
      chartTab: t({ en: 'Chart', ko: '차트' }),
      agreementTab: t({ en: 'Agreement', ko: '합의' }),

      // Selection
      selectInstructions: t({ en: 'Select 2-6 algorithms to compare', ko: '비교할 알고리즘 2-6개를 선택하세요' }),
      selected: t({ en: 'selected', ko: '선택됨' }),
      minAlgorithmsRequired: t({ en: 'Select at least 2 algorithms', ko: '최소 2개 알고리즘을 선택하세요' }),

      // Actions
      runComparison: t({ en: 'Run Comparison', ko: '비교 실행' }),
      running: t({ en: 'Running...', ko: '실행 중...' }),
      close: t({ en: 'Close', ko: '닫기' }),

      // Results table
      algorithm: t({ en: 'Algorithm', ko: '알고리즘' }),
      status: t({ en: 'Status', ko: '상태' }),
      anomalyCount: t({ en: 'Anomaly Count', ko: '이상 수' }),
      anomalyRate: t({ en: 'Anomaly Rate', ko: '이상 비율' }),
      duration: t({ en: 'Duration', ko: '소요 시간' }),
      success: t({ en: 'Success', ko: '성공' }),
      failed: t({ en: 'Failed', ko: '실패' }),

      // Stats
      totalRows: t({ en: 'Total Rows', ko: '전체 행' }),
      algorithmsCompared: t({ en: 'Algorithms', ko: '알고리즘' }),
      columnsAnalyzed: t({ en: 'Columns', ko: '컬럼' }),
      totalDuration: t({ en: 'Total Duration', ko: '총 소요 시간' }),

      // Charts
      rateComparison: t({ en: 'Anomaly Rate Comparison', ko: '이상 비율 비교' }),
      durationComparison: t({ en: 'Execution Time Comparison', ko: '실행 시간 비교' }),
      agreementMatrix: t({ en: 'Agreement Matrix (Overlap)', ko: '합의 매트릭스 (겹침)' }),
      matrixDescription: t({
        en: 'Diagonal shows total anomalies per algorithm. Other cells show overlap (anomalies detected by both algorithms).',
        ko: '대각선은 알고리즘당 총 이상치를 표시합니다. 다른 셀은 겹침(두 알고리즘 모두 감지한 이상치)을 표시합니다.',
      }),

      // Agreement
      agreementOverview: t({ en: 'Agreement Overview', ko: '합의 개요' }),
      totalUniqueAnomalies: t({ en: 'Total Unique Anomalies', ko: '총 고유 이상치' }),
      agreementDistribution: t({ en: 'Agreement Distribution', ko: '합의 분포' }),
      agreementLevels: {
        all: t({ en: 'All Agree', ko: '모두 동의' }),
        majority: t({ en: 'Majority', ko: '다수' }),
        some: t({ en: 'Some', ko: '일부' }),
        one: t({ en: 'One Only', ko: '단독' }),
      },
      noAgreementData: t({ en: 'No agreement data available', ko: '합의 데이터 없음' }),

      // Records
      anomalyRecords: t({ en: 'Anomaly Records', ko: '이상 기록' }),
      records: t({ en: 'records', ko: '기록' }),
      rowIndex: t({ en: 'Row', ko: '행' }),
      detectedBy: t({ en: 'Detected By', ko: '감지 알고리즘' }),
      agreementLevel: t({ en: 'Agreement', ko: '합의' }),
      confidence: t({ en: 'Confidence', ko: '신뢰도' }),
      noRecordsFound: t({ en: 'No records found', ko: '기록 없음' }),
      showingFirst50: t({ en: 'Showing first 50 records', ko: '처음 50개 기록 표시' }),

      // Messages
      comparisonComplete: t({ en: 'Comparison complete', ko: '비교 완료' }),
      comparisonFailed: t({ en: 'Comparison failed', ko: '비교 실패' }),
      errorLoadingAlgorithms: t({ en: 'Failed to load algorithms', ko: '알고리즘 로드 실패' }),
    },

    // Batch detection
    batch: {
      title: t({ en: 'Batch Anomaly Detection', ko: '일괄 이상 탐지' }),
      description: t({
        en: 'Run anomaly detection across multiple data sources at once',
        ko: '여러 데이터 소스에 대해 한 번에 이상 탐지 실행',
      }),
      runBatch: t({ en: 'Run Batch Detection', ko: '일괄 탐지 실행' }),
      jobName: t({ en: 'Job Name', ko: '작업 이름' }),
      jobNamePlaceholder: t({ en: 'Enter a name for this batch job', ko: '일괄 작업 이름 입력' }),
      selectSources: t({ en: 'Select Data Sources', ko: '데이터 소스 선택' }),
      selectAll: t({ en: 'Select All', ko: '모두 선택' }),
      clearAll: t({ en: 'Clear All', ko: '모두 해제' }),
      sourcesSelected: t({ en: 'sources selected', ko: '개 소스 선택됨' }),
      noSourcesSelected: t({ en: 'No sources selected', ko: '선택된 소스 없음' }),
      jobCreated: t({ en: 'Batch job created', ko: '일괄 작업 생성됨' }),
      processingSources: t({ en: 'Processing', ko: '처리 중' }),

      // Tabs
      singleSource: t({ en: 'Single Source', ko: '단일 소스' }),
      batchDetection: t({ en: 'Batch Detection', ko: '일괄 탐지' }),
      batchHistory: t({ en: 'Batch History', ko: '일괄 이력' }),
      batchHistoryDesc: t({
        en: 'View previous batch detection jobs',
        ko: '이전 일괄 탐지 작업 보기',
      }),

      // Progress
      progress: t({ en: 'Progress', ko: '진행률' }),
      processing: t({ en: 'Currently processing', ko: '현재 처리 중' }),
      completed: t({ en: 'Completed', ko: '완료' }),
      failed: t({ en: 'Failed', ko: '실패' }),
      sourceResults: t({ en: 'Source Results', ko: '소스 결과' }),

      // Status
      status: {
        pending: t({ en: 'Pending', ko: '대기 중' }),
        running: t({ en: 'Running', ko: '실행 중' }),
        completed: t({ en: 'Completed', ko: '완료' }),
        partial: t({ en: 'Partial', ko: '부분 완료' }),
        error: t({ en: 'Error', ko: '오류' }),
        cancelled: t({ en: 'Cancelled', ko: '취소됨' }),
      },

      // Actions
      cancel: t({ en: 'Cancel Job', ko: '작업 취소' }),
      cancelling: t({ en: 'Cancelling...', ko: '취소 중...' }),
      jobCancelled: t({ en: 'Batch job cancelled', ko: '일괄 작업 취소됨' }),

      // Results
      untitledJob: t({ en: 'Untitled Batch Job', ko: '제목 없는 일괄 작업' }),
      sourcesTotal: t({ en: 'sources', ko: '개 소스' }),
      sourceName: t({ en: 'Source', ko: '소스' }),
      avgAnomalyRate: t({ en: 'Avg Anomaly Rate', ko: '평균 이상 비율' }),

      // Empty states
      noBatchJobs: t({ en: 'No batch jobs', ko: '일괄 작업 없음' }),
      noBatchJobsDesc: t({
        en: 'Run batch detection to analyze multiple sources at once',
        ko: '일괄 탐지를 실행하여 여러 소스를 한 번에 분석하세요',
      }),
      noHistory: t({ en: 'No batch history', ko: '일괄 이력 없음' }),

      // Warnings
      highAnomalyRateWarning: t({
        en: 'High anomaly rates detected',
        ko: '높은 이상 비율 감지됨',
      }),
      highAnomalyRateDescription: t({
        en: 'Some sources have anomaly rates above 15%. This may indicate data quality issues.',
        ko: '일부 소스의 이상 비율이 15%를 초과합니다. 데이터 품질 문제가 있을 수 있습니다.',
      }),
    },

    // Streaming anomaly detection
    streaming: {
      tab: t({ en: 'Streaming', ko: '스트리밍' }),
      title: t({ en: 'Real-time Streaming Detection', ko: '실시간 스트리밍 탐지' }),
      subtitle: t({
        en: 'Monitor data streams in real-time and detect anomalies as they occur',
        ko: '데이터 스트림을 실시간으로 모니터링하고 발생하는 이상을 탐지합니다',
      }),

      // Controls
      controls: t({ en: 'Streaming Controls', ko: '스트리밍 제어' }),
      controlsDescription: t({
        en: 'Configure and manage real-time anomaly detection',
        ko: '실시간 이상 탐지를 설정하고 관리합니다',
      }),
      algorithm: t({ en: 'Algorithm', ko: '알고리즘' }),
      windowSize: t({ en: 'Window Size', ko: '윈도우 크기' }),
      windowSizeHint: t({
        en: 'Number of recent data points to analyze',
        ko: '분석할 최근 데이터 포인트 수',
      }),
      threshold: t({ en: 'Threshold', ko: '임계값' }),
      thresholdHint: t({
        en: 'Standard deviations for anomaly detection',
        ko: '이상 탐지를 위한 표준 편차',
      }),
      columns: t({ en: 'Columns to Monitor', ko: '모니터링할 컬럼' }),
      allColumnsHint: t({
        en: 'All numeric columns will be monitored',
        ko: '모든 숫자 컬럼이 모니터링됩니다',
      }),
      onlineLearning: t({ en: 'Online', ko: '온라인' }),

      // Session
      startSession: t({ en: 'Start Streaming', ko: '스트리밍 시작' }),
      stopSession: t({ en: 'Stop Streaming', ko: '스트리밍 중지' }),
      sessionId: t({ en: 'Session ID', ko: '세션 ID' }),
      totalPoints: t({ en: 'Points', ko: '포인트' }),
      totalAlerts: t({ en: 'Alerts', ko: '알림' }),
      startedAt: t({ en: 'Started', ko: '시작 시간' }),
      sessionStarted: t({ en: 'Session Started', ko: '세션 시작됨' }),
      sessionStopped: t({ en: 'Session Stopped', ko: '세션 중지됨' }),

      // Status
      connected: t({ en: 'Connected', ko: '연결됨' }),
      disconnected: t({ en: 'Disconnected', ko: '연결 끊김' }),
      error: t({ en: 'Error', ko: '오류' }),

      // Statistics
      statistics: t({ en: 'Statistics', ko: '통계' }),
      dataPoints: t({ en: 'Data Points', ko: '데이터 포인트' }),
      anomalies: t({ en: 'Anomalies', ko: '이상' }),
      bufferUtilization: t({ en: 'Buffer', ko: '버퍼' }),
      anomalyRate: t({ en: 'Anomaly Rate', ko: '이상 비율' }),

      // Demo
      startDemo: t({ en: 'Start Demo Data', ko: '데모 데이터 시작' }),
      simulatingData: t({ en: 'Simulating data...', ko: '데이터 시뮬레이션 중...' }),

      // Chart
      liveChart: t({ en: 'Live Data Stream', ko: '실시간 데이터 스트림' }),
      noColumns: t({ en: 'No columns to display', ko: '표시할 컬럼 없음' }),
      paused: t({ en: 'Paused', ko: '일시정지' }),

      // Alerts
      recentAlerts: t({ en: 'Recent Alerts', ko: '최근 알림' }),
      alertsDescription: t({
        en: 'Real-time anomaly alerts from the streaming session',
        ko: '스트리밍 세션의 실시간 이상 알림',
      }),
      noAlerts: t({ en: 'No anomalies detected yet', ko: '아직 이상이 감지되지 않았습니다' }),
      noAlertsHint: t({
        en: 'Alerts will appear here when anomalies are detected',
        ko: '이상이 감지되면 여기에 알림이 표시됩니다',
      }),
      clearAlerts: t({ en: 'Clear', ko: '지우기' }),

      // Algorithms
      algorithms: {
        zscore_rolling: t({ en: 'Rolling Z-Score', ko: '롤링 Z-점수' }),
        ema: t({ en: 'Exponential Moving Average', ko: '지수 이동 평균' }),
        isolation_forest_incremental: t({ en: 'Incremental Isolation Forest', ko: '증분 고립 숲' }),
        half_space_trees: t({ en: 'Half-Space Trees', ko: '반공간 트리' }),
        rrcf: t({ en: 'Robust Random Cut Forest', ko: '강건 랜덤 컷 포레스트' }),
      },
    },
  },
} satisfies Dictionary

export default anomalyContent
