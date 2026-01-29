/**
 * Profiler Configuration translations
 *
 * This file contains translations for profiler configuration UI,
 * including sampling strategies and pattern detection settings.
 */
import { t, type Dictionary } from 'intlayer'

const profilerContent = {
  key: 'profiler',
  content: {
    // Main sections
    samplingConfig: t({ en: 'Sampling Configuration', ko: '샘플링 설정' }),
    patternDetection: t({ en: 'Pattern Detection', ko: '패턴 감지' }),
    advancedOptions: t({ en: 'Advanced Options', ko: '고급 옵션' }),
    profilingResults: t({ en: 'Profiling Results', ko: '프로파일링 결과' }),

    // Sampling strategy labels
    samplingStrategy: t({ en: 'Sampling Strategy', ko: '샘플링 전략' }),
    sampleSize: t({ en: 'Sample Size', ko: '샘플 크기' }),
    confidenceLevel: t({ en: 'Confidence Level', ko: '신뢰 수준' }),
    marginOfError: t({ en: 'Margin of Error', ko: '오차 범위' }),
    strataColumn: t({ en: 'Stratification Column', ko: '계층화 컬럼' }),
    randomSeed: t({ en: 'Random Seed', ko: '랜덤 시드' }),

    // Sampling strategies
    strategies: {
      none: t({
        en: 'None (Profile All Data)',
        ko: '없음 (전체 데이터 프로파일링)',
      }),
      head: t({
        en: 'Head (First N Rows)',
        ko: '헤드 (첫 N개 행)',
      }),
      random: t({
        en: 'Random Sampling',
        ko: '랜덤 샘플링',
      }),
      systematic: t({
        en: 'Systematic (Every Nth Row)',
        ko: '체계적 샘플링 (N번째 행마다)',
      }),
      stratified: t({
        en: 'Stratified (Maintain Distribution)',
        ko: '계층적 샘플링 (분포 유지)',
      }),
      reservoir: t({
        en: 'Reservoir (Streaming)',
        ko: '저수지 샘플링 (스트리밍)',
      }),
      adaptive: t({
        en: 'Adaptive (Auto-Select)',
        ko: '적응형 (자동 선택)',
      }),
      hash: t({
        en: 'Hash (Deterministic)',
        ko: '해시 (결정적)',
      }),
    },

    // Strategy descriptions
    strategyDescriptions: {
      none: t({
        en: 'Profile all rows. Best for small datasets (<100K rows).',
        ko: '모든 행을 프로파일링합니다. 소규모 데이터셋(<100K 행)에 적합합니다.',
      }),
      head: t({
        en: 'Use first N rows. Fast but may not represent full distribution.',
        ko: '첫 N개 행을 사용합니다. 빠르지만 전체 분포를 대표하지 않을 수 있습니다.',
      }),
      random: t({
        en: 'Random selection of rows. Good general-purpose strategy.',
        ko: '무작위로 행을 선택합니다. 범용적으로 좋은 전략입니다.',
      }),
      systematic: t({
        en: 'Select every Nth row. Good for ordered datasets.',
        ko: 'N번째마다 행을 선택합니다. 정렬된 데이터셋에 적합합니다.',
      }),
      stratified: t({
        en: 'Maintain category distribution. Best for categorical data.',
        ko: '카테고리 분포를 유지합니다. 범주형 데이터에 적합합니다.',
      }),
      reservoir: t({
        en: 'Single-pass streaming algorithm. Good for very large datasets.',
        ko: '단일 패스 스트리밍 알고리즘. 매우 큰 데이터셋에 적합합니다.',
      }),
      adaptive: t({
        en: 'Automatically selects best strategy based on data characteristics.',
        ko: '데이터 특성에 따라 자동으로 최적 전략을 선택합니다.',
      }),
      hash: t({
        en: 'Deterministic selection using hash. Reproducible results.',
        ko: '해시를 사용한 결정적 선택. 재현 가능한 결과.',
      }),
    },

    // Pattern detection
    enablePatternDetection: t({
      en: 'Enable Pattern Detection',
      ko: '패턴 감지 활성화',
    }),
    patternSampleSize: t({
      en: 'Pattern Sample Size',
      ko: '패턴 샘플 크기',
    }),
    minPatternConfidence: t({
      en: 'Minimum Confidence',
      ko: '최소 신뢰도',
    }),
    patternsToDetect: t({
      en: 'Patterns to Detect',
      ko: '감지할 패턴',
    }),
    allPatterns: t({ en: 'All Patterns', ko: '모든 패턴' }),

    // Pattern types
    patterns: {
      email: t({ en: 'Email', ko: '이메일' }),
      phone: t({ en: 'Phone', ko: '전화번호' }),
      uuid: t({ en: 'UUID', ko: 'UUID' }),
      url: t({ en: 'URL', ko: 'URL' }),
      ip_address: t({ en: 'IP Address', ko: 'IP 주소' }),
      credit_card: t({ en: 'Credit Card', ko: '신용카드' }),
      date: t({ en: 'Date', ko: '날짜' }),
      datetime: t({ en: 'DateTime', ko: '날짜시간' }),
      korean_rrn: t({ en: 'Korean RRN', ko: '주민등록번호' }),
      korean_phone: t({ en: 'Korean Phone', ko: '한국 전화번호' }),
      ssn: t({ en: 'SSN', ko: '사회보장번호' }),
      postal_code: t({ en: 'Postal Code', ko: '우편번호' }),
      currency: t({ en: 'Currency', ko: '통화' }),
      percentage: t({ en: 'Percentage', ko: '백분율' }),
    },

    // Advanced options
    includeHistograms: t({
      en: 'Include Histograms',
      ko: '히스토그램 포함',
    }),
    includeCorrelations: t({
      en: 'Include Correlations',
      ko: '상관관계 포함',
    }),
    includeCardinality: t({
      en: 'Include Cardinality Estimates',
      ko: '카디널리티 추정 포함',
    }),

    // Sampling metadata display
    samplingUsed: t({ en: 'Sampling Used', ko: '사용된 샘플링' }),
    totalRows: t({ en: 'Total Rows', ko: '전체 행 수' }),
    sampledRows: t({ en: 'Sampled Rows', ko: '샘플링된 행' }),
    samplingRatio: t({ en: 'Sampling Ratio', ko: '샘플링 비율' }),
    seedUsed: t({ en: 'Seed Used', ko: '사용된 시드' }),

    // Pattern results
    detectedPatterns: t({ en: 'Detected Patterns', ko: '감지된 패턴' }),
    primaryPattern: t({ en: 'Primary Pattern', ko: '주요 패턴' }),
    patternConfidence: t({ en: 'Confidence', ko: '신뢰도' }),
    matchCount: t({ en: 'Matches', ko: '일치 수' }),
    matchPercentage: t({ en: 'Match %', ko: '일치율' }),
    sampleMatches: t({ en: 'Sample Matches', ko: '샘플 일치' }),
    inferredType: t({ en: 'Inferred Type', ko: '추론된 타입' }),

    // Column statistics
    columnStatistics: t({ en: 'Column Statistics', ko: '컬럼 통계' }),
    basicStats: t({ en: 'Basic Statistics', ko: '기본 통계' }),
    distributionStats: t({ en: 'Distribution', ko: '분포' }),
    stringStats: t({ en: 'String Statistics', ko: '문자열 통계' }),

    // Stats labels
    nullCount: t({ en: 'Null Count', ko: 'Null 개수' }),
    distinctCount: t({ en: 'Distinct Count', ko: '고유값 개수' }),
    isUnique: t({ en: 'Is Unique', ko: '고유 여부' }),
    median: t({ en: 'Median', ko: '중앙값' }),
    q1: t({ en: 'Q1 (25%)', ko: 'Q1 (25%)' }),
    q3: t({ en: 'Q3 (75%)', ko: 'Q3 (75%)' }),
    skewness: t({ en: 'Skewness', ko: '왜도' }),
    kurtosis: t({ en: 'Kurtosis', ko: '첨도' }),
    minLength: t({ en: 'Min Length', ko: '최소 길이' }),
    maxLength: t({ en: 'Max Length', ko: '최대 길이' }),
    avgLength: t({ en: 'Avg Length', ko: '평균 길이' }),
    cardinalityEstimate: t({
      en: 'Cardinality Estimate',
      ko: '카디널리티 추정',
    }),

    // Histogram
    histogram: t({ en: 'Value Distribution', ko: '값 분포' }),
    bucket: t({ en: 'Range', ko: '범위' }),
    count: t({ en: 'Count', ko: '개수' }),
    percentage: t({ en: 'Percentage', ko: '비율' }),

    // Actions
    runProfileWithConfig: t({
      en: 'Run Profile with Configuration',
      ko: '설정으로 프로파일 실행',
    }),
    useDefaultSettings: t({
      en: 'Use Default Settings',
      ko: '기본 설정 사용',
    }),
    resetToDefaults: t({
      en: 'Reset to Defaults',
      ko: '기본값으로 재설정',
    }),

    // Tooltips
    tooltips: {
      confidenceLevel: t({
        en: 'Higher confidence requires larger samples but gives more reliable results.',
        ko: '높은 신뢰 수준은 더 큰 샘플을 필요로 하지만 더 신뢰할 수 있는 결과를 제공합니다.',
      }),
      marginOfError: t({
        en: 'Smaller margin of error requires larger samples for statistical accuracy.',
        ko: '작은 오차 범위는 통계적 정확성을 위해 더 큰 샘플을 필요로 합니다.',
      }),
      strataColumn: t({
        en: 'Select a categorical column to ensure proportional sampling from each category.',
        ko: '각 카테고리에서 비례 샘플링을 보장하려면 범주형 컬럼을 선택하세요.',
      }),
      randomSeed: t({
        en: 'Set a seed for reproducible sampling results across runs.',
        ko: '실행 간에 재현 가능한 샘플링 결과를 위해 시드를 설정하세요.',
      }),
    },

    // Presets
    presets: {
      label: t({ en: 'Presets', ko: '프리셋' }),
      quick: t({ en: 'Quick Scan', ko: '빠른 스캔' }),
      quickDesc: t({
        en: 'Fast profiling with head sampling',
        ko: '헤드 샘플링으로 빠른 프로파일링',
      }),
      balanced: t({ en: 'Balanced', ko: '균형' }),
      balancedDesc: t({
        en: 'Good balance of speed and accuracy',
        ko: '속도와 정확성의 적절한 균형',
      }),
      thorough: t({ en: 'Thorough', ko: '철저함' }),
      thoroughDesc: t({
        en: 'Complete profiling with all features',
        ko: '모든 기능을 포함한 완전한 프로파일링',
      }),
      custom: t({ en: 'Custom', ko: '사용자 정의' }),
    },

    // Profiling duration
    profilingDuration: t({ en: 'Profiling Duration', ko: '프로파일링 소요 시간' }),
    profiledAt: t({ en: 'Profiled At', ko: '프로파일링 시간' }),

    // Summary
    patternsSummary: t({
      en: 'Patterns Detected Summary',
      ko: '감지된 패턴 요약',
    }),
    columnsWithPatterns: t({
      en: 'Columns with Patterns',
      ko: '패턴이 있는 컬럼',
    }),
  },
} satisfies Dictionary

export default profilerContent
