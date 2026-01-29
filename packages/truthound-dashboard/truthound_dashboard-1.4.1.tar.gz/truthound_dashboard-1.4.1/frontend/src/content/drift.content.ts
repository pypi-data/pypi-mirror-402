/**
 * Drift detection page translations.
 *
 * Contains translations for the drift detection and comparison page.
 */
import { t, type Dictionary } from 'intlayer'

const driftContent = {
  key: 'drift',
  content: {
    title: t({ en: 'Drift Detection', ko: '드리프트 감지',
  }),
    subtitle: t({
      en: 'Compare datasets to detect data drift',
      ko: '데이터셋을 비교하여 데이터 드리프트 감지',
  }),

    // Actions
    compare: t({ en: 'Compare', ko: '비교',
  }),
    comparing: t({ en: 'Comparing...', ko: '비교 중...',
  }),
    newComparison: t({ en: 'New Comparison', ko: '새 비교',
  }),
    compareDatasets: t({ en: 'Compare Datasets', ko: '데이터셋 비교',
  }),
    compareDescription: t({
      en: 'Select baseline and current datasets to compare for drift',
      ko: '드리프트 비교를 위한 기준 및 현재 데이터셋을 선택하세요',
  }),

    // Source selection
    baseline: t({ en: 'Baseline', ko: '기준',
  }),
    current: t({ en: 'Current', ko: '현재',
  }),
    selectSource: t({ en: 'Select source', ko: '소스 선택',
  }),
    baselineSource: t({ en: 'Baseline Source', ko: '기준 소스',
  }),
    currentSource: t({ en: 'Current Source', ko: '현재 소스',
  }),
    selectBaseline: t({ en: 'Select baseline...', ko: '기준 선택...',
  }),
    selectCurrent: t({ en: 'Select current...', ko: '현재 선택...',
  }),
    detectionMethod: t({ en: 'Detection Method', ko: '감지 방법',
  }),

    // Validation
    selectBothSources: t({
      en: 'Please select both baseline and current sources',
      ko: '기준 소스와 현재 소스를 모두 선택하세요',
  }),
    mustBeDifferent: t({
      en: 'Baseline and current sources must be different',
      ko: '기준 소스와 현재 소스가 서로 달라야 합니다',
  }),

    // Results
    comparisonComplete: t({ en: 'Comparison complete', ko: '비교 완료',
  }),
    comparisonFailed: t({ en: 'Comparison failed', ko: '비교 실패',
  }),
    noDriftDetected: t({
      en: 'No significant drift detected',
      ko: '유의미한 드리프트가 감지되지 않았습니다',
  }),

    // Empty states
    noComparisonsYet: t({ en: 'No comparisons yet', ko: '비교 기록 없음',
  }),
    noComparisonsDesc: t({
      en: 'Compare two datasets to detect data drift',
      ko: '두 데이터셋을 비교하여 데이터 드리프트를 감지하세요',
  }),

    // Drift status
    highDrift: t({ en: 'High Drift', ko: '높은 드리프트',
  }),
    driftDetected: t({ en: 'Drift Detected', ko: '드리프트 감지됨',
  }),
    noDrift: t({ en: 'No Drift', ko: '드리프트 없음',
  }),

    // Stats
    columnsCompared: t({ en: 'Columns Compared', ko: '비교된 컬럼',
  }),
    driftedColumns: t({ en: 'Drifted Columns', ko: '드리프트 컬럼',
  }),
    driftPercentage: t({ en: 'Drift Percentage', ko: '드리프트 비율',
  }),
    columnDetails: t({ en: 'Column Details', ko: '컬럼 상세',
  }),

    // Detection methods - full list
    methods: {
      auto: t({ en: 'Auto (recommended)', ko: '자동 (권장)' }),
      ks: t({ en: 'Kolmogorov-Smirnov', ko: '콜모고로프-스미르노프' }),
      psi: t({ en: 'Population Stability Index', ko: '모집단 안정성 지수' }),
      chi2: t({ en: 'Chi-Square', ko: '카이제곱' }),
      js: t({ en: 'Jensen-Shannon', ko: '젠슨-샤논' }),
      kl: t({ en: 'Kullback-Leibler', ko: '쿨백-라이블러' }),
      wasserstein: t({ en: 'Wasserstein (EMD)', ko: '바서슈타인 (EMD)' }),
      cvm: t({ en: 'Cramér-von Mises', ko: '크라메르-폰 미제스' }),
      anderson: t({ en: 'Anderson-Darling', ko: '앤더슨-달링' }),
    },

    // Method descriptions
    methodDescriptions: {
      auto: t({
        en: 'Automatically selects the best method based on data type',
        ko: '데이터 타입에 따라 최적의 방법을 자동 선택',
      }),
      ks: t({
        en: 'Best for continuous distributions, compares cumulative distributions',
        ko: '연속 분포에 최적, 누적 분포 비교',
      }),
      psi: t({
        en: 'Industry standard for model monitoring, works with any distribution',
        ko: '모델 모니터링의 업계 표준, 모든 분포에 적용 가능',
      }),
      chi2: t({
        en: 'Statistical test for categorical data independence',
        ko: '범주형 데이터의 독립성 통계 검정',
      }),
      js: t({
        en: 'Symmetric divergence measure, bounded between 0-1',
        ko: '대칭 발산 측정, 0-1 사이 값',
      }),
      kl: t({
        en: 'Measures information loss between distributions',
        ko: '분포 간 정보 손실 측정',
      }),
      wasserstein: t({
        en: "Earth Mover's Distance, sensitive to distribution shape",
        ko: '분포 형태에 민감한 이동 거리 측정',
      }),
      cvm: t({
        en: 'More sensitive to tail differences than KS test',
        ko: 'KS 검정보다 꼬리 차이에 더 민감',
      }),
      anderson: t({
        en: 'Weighted test emphasizing tail sensitivity',
        ko: '꼬리 민감성을 강조하는 가중 검정',
      }),
    },

    // Method best-for hints
    methodBestFor: {
      auto: t({ en: 'General use', ko: '일반 용도' }),
      ks: t({ en: 'Continuous data', ko: '연속형 데이터' }),
      psi: t({ en: 'Model monitoring', ko: '모델 모니터링' }),
      chi2: t({ en: 'Categorical data', ko: '범주형 데이터' }),
      js: t({ en: 'Bounded comparison', ko: '범위 제한 비교' }),
      kl: t({ en: 'Information theory', ko: '정보 이론' }),
      wasserstein: t({ en: 'Shape comparison', ko: '형태 비교' }),
      cvm: t({ en: 'Tail analysis', ko: '꼬리 분석' }),
      anderson: t({ en: 'Tail sensitivity', ko: '꼬리 민감도' }),
    },

    // Correction methods
    correctionMethods: {
      none: t({ en: 'None', ko: '없음' }),
      bonferroni: t({ en: 'Bonferroni', ko: '본페로니' }),
      holm: t({ en: 'Holm', ko: '홀름' }),
      bh: t({ en: 'Benjamini-Hochberg', ko: '벤자미니-호흐베르그' }),
    },

    correctionDescriptions: {
      none: t({
        en: 'No correction - use with caution for multiple columns',
        ko: '보정 없음 - 다중 컬럼 시 주의 필요',
      }),
      bonferroni: t({
        en: 'Conservative correction for independent tests',
        ko: '독립 검정을 위한 보수적 보정',
      }),
      holm: t({
        en: 'Sequential adjustment, less conservative than Bonferroni',
        ko: '순차적 조정, 본페로니보다 덜 보수적',
      }),
      bh: t({
        en: 'False Discovery Rate control (recommended for multiple columns)',
        ko: '위양성 발견율 제어 (다중 컬럼에 권장)',
      }),
    },

    // Configuration labels
    config: {
      threshold: t({ en: 'Threshold', ko: '임계값' }),
      thresholdDescription: t({
        en: 'Statistical significance level for drift detection',
        ko: '드리프트 감지를 위한 통계적 유의 수준',
      }),
      correctionMethod: t({ en: 'Correction Method', ko: '보정 방법' }),
      correctionDescription: t({
        en: 'Multiple testing correction for comparing multiple columns',
        ko: '다중 컬럼 비교 시 다중 검정 보정',
      }),
      defaultThreshold: t({ en: 'Default for this method', ko: '이 방법의 기본값' }),
      columns: t({ en: 'Columns', ko: '컬럼' }),
      selectColumns: t({ en: 'Select columns to compare', ko: '비교할 컬럼 선택' }),
      allColumns: t({ en: 'All columns', ko: '모든 컬럼' }),
      selectedColumns: t({ en: 'Selected columns', ko: '선택된 컬럼' }),
      advancedOptions: t({ en: 'Advanced Options', ko: '고급 옵션' }),
    },

    // Method selector UI
    methodSelector: {
      title: t({ en: 'Detection Method', ko: '감지 방법' }),
      subtitle: t({
        en: 'Choose the statistical method for drift detection',
        ko: '드리프트 감지를 위한 통계 방법 선택',
      }),
      recommended: t({ en: 'Recommended', ko: '권장' }),
      bestFor: t({ en: 'Best for', ko: '적합 대상' }),
      defaultThreshold: t({ en: 'Default threshold', ko: '기본 임계값' }),
    },

    // Changes
    noChanges: t({ en: 'No changes detected', ko: '변경 사항이 없습니다',
  }),
    columnAdded: t({ en: 'Column Added', ko: '컬럼 추가됨',
  }),
    columnRemoved: t({ en: 'Column Removed', ko: '컬럼 제거됨',
  }),
    typeChanged: t({ en: 'Type Changed', ko: '타입 변경됨',
  }),
    statsChanged: t({ en: 'Statistics Changed', ko: '통계 변경됨',
  }),
  },
} satisfies Dictionary

export default driftContent
