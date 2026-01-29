/* eslint-disable */
export default {
  "key": "drift",
  "content": {
    "nodeType": "translation",
    "translation": {
      "en": {
        "title": "Drift Detection",
        "subtitle": "Compare datasets to detect data drift",
        "compare": "Compare",
        "comparing": "Comparing...",
        "newComparison": "New Comparison",
        "compareDatasets": "Compare Datasets",
        "compareDescription": "Select baseline and current datasets to compare for drift",
        "baseline": "Baseline",
        "current": "Current",
        "selectSource": "Select source",
        "baselineSource": "Baseline Source",
        "currentSource": "Current Source",
        "selectBaseline": "Select baseline...",
        "selectCurrent": "Select current...",
        "detectionMethod": "Detection Method",
        "selectBothSources": "Please select both baseline and current sources",
        "mustBeDifferent": "Baseline and current sources must be different",
        "comparisonComplete": "Comparison complete",
        "comparisonFailed": "Comparison failed",
        "noDriftDetected": "No significant drift detected",
        "noComparisonsYet": "No comparisons yet",
        "noComparisonsDesc": "Compare two datasets to detect data drift",
        "highDrift": "High Drift",
        "driftDetected": "Drift Detected",
        "noDrift": "No Drift",
        "columnsCompared": "Columns Compared",
        "driftedColumns": "Drifted Columns",
        "driftPercentage": "Drift Percentage",
        "columnDetails": "Column Details",
        "methods": {
          "auto": "Auto (recommended)",
          "ks": "Kolmogorov-Smirnov",
          "psi": "Population Stability Index",
          "chi2": "Chi-Square",
          "js": "Jensen-Shannon",
          "kl": "Kullback-Leibler",
          "wasserstein": "Wasserstein (EMD)",
          "cvm": "Cramér-von Mises",
          "anderson": "Anderson-Darling"
        },
        "methodDescriptions": {
          "auto": "Automatically selects the best method based on data type",
          "ks": "Best for continuous distributions, compares cumulative distributions",
          "psi": "Industry standard for model monitoring, works with any distribution",
          "chi2": "Statistical test for categorical data independence",
          "js": "Symmetric divergence measure, bounded between 0-1",
          "kl": "Measures information loss between distributions",
          "wasserstein": "Earth Mover's Distance, sensitive to distribution shape",
          "cvm": "More sensitive to tail differences than KS test",
          "anderson": "Weighted test emphasizing tail sensitivity"
        },
        "methodBestFor": {
          "auto": "General use",
          "ks": "Continuous data",
          "psi": "Model monitoring",
          "chi2": "Categorical data",
          "js": "Bounded comparison",
          "kl": "Information theory",
          "wasserstein": "Shape comparison",
          "cvm": "Tail analysis",
          "anderson": "Tail sensitivity"
        },
        "correctionMethods": {
          "none": "None",
          "bonferroni": "Bonferroni",
          "holm": "Holm",
          "bh": "Benjamini-Hochberg"
        },
        "correctionDescriptions": {
          "none": "No correction - use with caution for multiple columns",
          "bonferroni": "Conservative correction for independent tests",
          "holm": "Sequential adjustment, less conservative than Bonferroni",
          "bh": "False Discovery Rate control (recommended for multiple columns)"
        },
        "config": {
          "threshold": "Threshold",
          "thresholdDescription": "Statistical significance level for drift detection",
          "correctionMethod": "Correction Method",
          "correctionDescription": "Multiple testing correction for comparing multiple columns",
          "defaultThreshold": "Default for this method",
          "columns": "Columns",
          "selectColumns": "Select columns to compare",
          "allColumns": "All columns",
          "selectedColumns": "Selected columns",
          "advancedOptions": "Advanced Options"
        },
        "methodSelector": {
          "title": "Detection Method",
          "subtitle": "Choose the statistical method for drift detection",
          "recommended": "Recommended",
          "bestFor": "Best for",
          "defaultThreshold": "Default threshold"
        },
        "noChanges": "No changes detected",
        "columnAdded": "Column Added",
        "columnRemoved": "Column Removed",
        "typeChanged": "Type Changed",
        "statsChanged": "Statistics Changed"
      },
      "ko": {
        "title": "드리프트 감지",
        "subtitle": "데이터셋을 비교하여 데이터 드리프트 감지",
        "compare": "비교",
        "comparing": "비교 중...",
        "newComparison": "새 비교",
        "compareDatasets": "데이터셋 비교",
        "compareDescription": "드리프트 비교를 위한 기준 및 현재 데이터셋을 선택하세요",
        "baseline": "기준",
        "current": "현재",
        "selectSource": "소스 선택",
        "baselineSource": "기준 소스",
        "currentSource": "현재 소스",
        "selectBaseline": "기준 선택...",
        "selectCurrent": "현재 선택...",
        "detectionMethod": "감지 방법",
        "selectBothSources": "기준 소스와 현재 소스를 모두 선택하세요",
        "mustBeDifferent": "기준 소스와 현재 소스가 서로 달라야 합니다",
        "comparisonComplete": "비교 완료",
        "comparisonFailed": "비교 실패",
        "noDriftDetected": "유의미한 드리프트가 감지되지 않았습니다",
        "noComparisonsYet": "비교 기록 없음",
        "noComparisonsDesc": "두 데이터셋을 비교하여 데이터 드리프트를 감지하세요",
        "highDrift": "높은 드리프트",
        "driftDetected": "드리프트 감지됨",
        "noDrift": "드리프트 없음",
        "columnsCompared": "비교된 컬럼",
        "driftedColumns": "드리프트 컬럼",
        "driftPercentage": "드리프트 비율",
        "columnDetails": "컬럼 상세",
        "methods": {
          "auto": "자동 (권장)",
          "ks": "콜모고로프-스미르노프",
          "psi": "모집단 안정성 지수",
          "chi2": "카이제곱",
          "js": "젠슨-샤논",
          "kl": "쿨백-라이블러",
          "wasserstein": "바서슈타인 (EMD)",
          "cvm": "크라메르-폰 미제스",
          "anderson": "앤더슨-달링"
        },
        "methodDescriptions": {
          "auto": "데이터 타입에 따라 최적의 방법을 자동 선택",
          "ks": "연속 분포에 최적, 누적 분포 비교",
          "psi": "모델 모니터링의 업계 표준, 모든 분포에 적용 가능",
          "chi2": "범주형 데이터의 독립성 통계 검정",
          "js": "대칭 발산 측정, 0-1 사이 값",
          "kl": "분포 간 정보 손실 측정",
          "wasserstein": "분포 형태에 민감한 이동 거리 측정",
          "cvm": "KS 검정보다 꼬리 차이에 더 민감",
          "anderson": "꼬리 민감성을 강조하는 가중 검정"
        },
        "methodBestFor": {
          "auto": "일반 용도",
          "ks": "연속형 데이터",
          "psi": "모델 모니터링",
          "chi2": "범주형 데이터",
          "js": "범위 제한 비교",
          "kl": "정보 이론",
          "wasserstein": "형태 비교",
          "cvm": "꼬리 분석",
          "anderson": "꼬리 민감도"
        },
        "correctionMethods": {
          "none": "없음",
          "bonferroni": "본페로니",
          "holm": "홀름",
          "bh": "벤자미니-호흐베르그"
        },
        "correctionDescriptions": {
          "none": "보정 없음 - 다중 컬럼 시 주의 필요",
          "bonferroni": "독립 검정을 위한 보수적 보정",
          "holm": "순차적 조정, 본페로니보다 덜 보수적",
          "bh": "위양성 발견율 제어 (다중 컬럼에 권장)"
        },
        "config": {
          "threshold": "임계값",
          "thresholdDescription": "드리프트 감지를 위한 통계적 유의 수준",
          "correctionMethod": "보정 방법",
          "correctionDescription": "다중 컬럼 비교 시 다중 검정 보정",
          "defaultThreshold": "이 방법의 기본값",
          "columns": "컬럼",
          "selectColumns": "비교할 컬럼 선택",
          "allColumns": "모든 컬럼",
          "selectedColumns": "선택된 컬럼",
          "advancedOptions": "고급 옵션"
        },
        "methodSelector": {
          "title": "감지 방법",
          "subtitle": "드리프트 감지를 위한 통계 방법 선택",
          "recommended": "권장",
          "bestFor": "적합 대상",
          "defaultThreshold": "기본 임계값"
        },
        "noChanges": "변경 사항이 없습니다",
        "columnAdded": "컬럼 추가됨",
        "columnRemoved": "컬럼 제거됨",
        "typeChanged": "타입 변경됨",
        "statsChanged": "통계 변경됨"
      }
    }
  },
  "localIds": [
    "drift::local::src/content/drift.content.ts"
  ]
} as const;
