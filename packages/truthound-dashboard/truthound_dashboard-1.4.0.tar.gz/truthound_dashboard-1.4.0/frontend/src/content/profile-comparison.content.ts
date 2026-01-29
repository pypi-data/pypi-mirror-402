/**
 * Profile Comparison translations
 *
 * This file contains translations for profile comparison,
 * trend analysis, and version selection features.
 */
import { t, type Dictionary } from 'intlayer'

const profileComparisonContent = {
  key: 'profileComparison',
  content: {
    // Section titles
    comparisonSummary: t({ en: 'Comparison Summary', ko: '비교 요약' }),
    columnDetails: t({ en: 'Column Details', ko: '컬럼 상세' }),
    profileHistory: t({ en: 'Profile History', ko: '프로파일 이력' }),
    profileTrends: t({ en: 'Profile Trends', ko: '프로파일 추이' }),

    // Comparison description
    comparingProfiles: t({ en: 'Comparing profiles from', ko: '프로파일 비교:' }),
    to: t({ en: 'to', ko: '에서' }),

    // Summary stats
    totalColumns: t({ en: 'Total Columns', ko: '전체 컬럼' }),
    withChanges: t({ en: 'With Changes', ko: '변경됨' }),
    significantChanges: t({ en: 'Significant', ko: '중요 변경' }),
    improved: t({ en: 'Improved', ko: '개선됨' }),
    degraded: t({ en: 'Degraded', ko: '악화됨' }),

    // Row count
    rowCountChange: t({ en: 'Row Count Change', ko: '행 수 변화' }),

    // Table headers
    column: t({ en: 'Column', ko: '컬럼' }),
    metric: t({ en: 'Metric', ko: '지표' }),
    baseline: t({ en: 'Baseline', ko: '기준' }),
    current: t({ en: 'Current', ko: '현재' }),
    change: t({ en: 'Change', ko: '변화' }),
    trend: t({ en: 'Trend', ko: '추이' }),

    // Version selector
    profilesAvailable: t({
      en: 'profiles available',
      ko: '개의 프로파일 사용 가능',
    }),
    selectProfiles: t({
      en: 'Select 2 profiles to compare',
      ko: '비교할 2개의 프로파일을 선택하세요',
    }),
    selectOneMore: t({
      en: 'Select 1 more profile',
      ko: '1개의 프로파일을 더 선택하세요',
    }),
    readyToCompare: t({ en: 'Ready to compare', ko: '비교 준비 완료' }),
    compareSelected: t({ en: 'Compare Selected', ko: '선택 항목 비교' }),
    comparing: t({ en: 'Comparing...', ko: '비교 중...' }),

    // Selection labels
    baselineLabel: t({ en: 'Baseline', ko: '기준' }),
    currentLabel: t({ en: 'Current', ko: '현재' }),
    latest: t({ en: 'Latest', ko: '최신' }),

    // Table columns
    date: t({ en: 'Date', ko: '날짜' }),
    rows: t({ en: 'Rows', ko: '행' }),
    columns: t({ en: 'Columns', ko: '컬럼' }),
    size: t({ en: 'Size', ko: '크기' }),
    nullPct: t({ en: 'Null %', ko: 'Null %' }),
    uniquePct: t({ en: 'Unique %', ko: '고유 %' }),

    // Trend chart
    granularity: t({ en: 'Granularity', ko: '단위' }),
    daily: t({ en: 'Daily', ko: '일별' }),
    weekly: t({ en: 'Weekly', ko: '주별' }),
    monthly: t({ en: 'Monthly', ko: '월별' }),

    // Chart titles
    rowCountOverTime: t({ en: 'Row Count Over Time', ko: '시간별 행 수' }),
    dataQualityMetrics: t({
      en: 'Data Quality Metrics',
      ko: '데이터 품질 지표',
    }),
    avgNullAndUnique: t({
      en: 'Average null and unique percentages over time',
      ko: '시간별 평균 null 및 고유 비율',
    }),

    // Trend labels
    rowCount: t({ en: 'Row Count', ko: '행 수' }),
    avgNullPct: t({ en: 'Avg Null %', ko: '평균 Null %' }),
    avgUniquePct: t({ en: 'Avg Unique %', ko: '평균 고유 %' }),

    // Trend directions
    up: t({ en: 'up', ko: '증가' }),
    down: t({ en: 'down', ko: '감소' }),
    stable: t({ en: 'stable', ko: '안정' }),

    // Data points
    dataPoints: t({ en: 'data points', ko: '개의 데이터 포인트' }),

    // Empty states
    noProfileHistory: t({
      en: 'No profile history available.',
      ko: '프로파일 이력이 없습니다.',
    }),
    runProfilingFirst: t({
      en: 'Run profiling to create the first snapshot.',
      ko: '프로파일링을 실행하여 첫 스냅샷을 생성하세요.',
    }),
    loadingHistory: t({
      en: 'Loading profile history...',
      ko: '프로파일 이력 로딩 중...',
    }),
    notEnoughProfiles: t({
      en: 'Not enough profiles to compare. Need at least 2 profiles.',
      ko: '비교할 프로파일이 부족합니다. 최소 2개의 프로파일이 필요합니다.',
    }),

    // Period
    periodFrom: t({ en: 'from', ko: '시작' }),
    periodTo: t({ en: 'to', ko: '종료' }),
  },
} satisfies Dictionary

export default profileComparisonContent
