/**
 * Rule Suggestions translations
 *
 * This file contains translations for profile-based
 * validation rule suggestions feature including:
 * - Strictness levels
 * - Presets
 * - Export formats
 * - Category filtering
 */
import { t, type Dictionary } from 'intlayer'

const ruleSuggestionsContent = {
  key: 'ruleSuggestions',
  content: {
    // Dialog title and description
    title: t({ en: 'Suggested Validation Rules', ko: '제안된 검증 규칙' }),
    description: t({
      en: 'Based on profile analysis, we suggest the following validation rules.',
      ko: '프로파일 분석을 기반으로 다음 검증 규칙을 제안합니다.',
    }),
    selectRulesDesc: t({
      en: 'Select the rules you want to apply.',
      ko: '적용할 규칙을 선택하세요.',
    }),

    // Stats
    suggestions: t({ en: 'suggestions', ko: '제안' }),
    highConfidence: t({ en: 'high confidence', ko: '높은 신뢰도' }),

    // Selection
    selectAll: t({ en: 'Select All', ko: '전체 선택' }),
    deselectAll: t({ en: 'Deselect All', ko: '전체 해제' }),
    selected: t({ en: 'selected', ko: '선택됨' }),

    // Actions
    generateRules: t({ en: 'Generate Rules', ko: '규칙 생성' }),
    applyRules: t({ en: 'Apply Rules', ko: '규칙 적용' }),
    applying: t({ en: 'Applying...', ko: '적용 중...' }),
    analyzingProfile: t({
      en: 'Analyzing profile data...',
      ko: '프로파일 데이터 분석 중...',
    }),

    // Filter and search
    searchSuggestions: t({ en: 'Search suggestions...', ko: '제안 검색...' }),
    allCategories: t({ en: 'All Categories', ko: '모든 카테고리' }),
    noSuggestionsMatch: t({
      en: 'No suggestions match your filters.',
      ko: '필터에 맞는 제안이 없습니다.',
    }),

    // Empty state
    noSuggestionsAvailable: t({
      en: 'No suggestions available. Run profiling first.',
      ko: '제안이 없습니다. 먼저 프로파일링을 실행하세요.',
    }),

    // Confidence levels
    confidence: t({ en: 'Confidence', ko: '신뢰도' }),
    highConfidenceLabel: t({ en: 'High confidence', ko: '높은 신뢰도' }),
    mediumConfidenceLabel: t({ en: 'Medium confidence', ko: '중간 신뢰도' }),
    lowConfidenceLabel: t({ en: 'Low confidence', ko: '낮은 신뢰도' }),

    // Categories
    completeness: t({ en: 'Completeness', ko: '완전성' }),
    uniqueness: t({ en: 'Uniqueness', ko: '고유성' }),
    distribution: t({ en: 'Distribution', ko: '분포' }),
    string: t({ en: 'String', ko: '문자열' }),
    datetime: t({ en: 'Datetime', ko: '날짜/시간' }),
    schema: t({ en: 'Schema', ko: '스키마' }),
    stats: t({ en: 'Statistics', ko: '통계' }),
    pattern: t({ en: 'Pattern', ko: '패턴' }),

    // Status messages
    rulesApplied: t({
      en: 'Rules applied successfully',
      ko: '규칙이 성공적으로 적용되었습니다',
    }),
    appliedCount: t({ en: 'rules applied', ko: '개의 규칙 적용됨' }),

    // Validation reasons
    lowNulls: t({
      en: 'Column has less than 1% null values',
      ko: '컬럼의 null 값이 1% 미만입니다',
    }),
    noNulls: t({
      en: 'Column has 0% null values',
      ko: '컬럼에 null 값이 없습니다',
    }),
    highUniqueness: t({
      en: 'Column has 100% unique values',
      ko: '컬럼의 모든 값이 고유합니다',
    }),
    lowCardinality: t({
      en: 'Column has low cardinality with limited distinct values',
      ko: '컬럼의 카디널리티가 낮습니다',
    }),
    numericRange: t({
      en: 'Column values fall within a defined numeric range',
      ko: '컬럼 값이 정의된 숫자 범위 내에 있습니다',
    }),
    emailPattern: t({
      en: 'Column name suggests email format',
      ko: '컬럼 이름이 이메일 형식을 암시합니다',
    }),
    phonePattern: t({
      en: 'Column name suggests phone number format',
      ko: '컬럼 이름이 전화번호 형식을 암시합니다',
    }),

    // =========================================================================
    // Advanced Options
    // =========================================================================

    // Section headers
    advancedOptions: t({ en: 'Advanced Options', ko: '고급 옵션' }),
    generationSettings: t({ en: 'Generation Settings', ko: '생성 설정' }),
    exportOptions: t({ en: 'Export Options', ko: '내보내기 옵션' }),

    // Strictness levels
    strictness: t({ en: 'Strictness', ko: '엄격도' }),
    strictnessLoose: t({ en: 'Loose', ko: '느슨함' }),
    strictnessMedium: t({ en: 'Medium', ko: '보통' }),
    strictnessStrict: t({ en: 'Strict', ko: '엄격' }),
    strictnessLooseDesc: t({
      en: 'Permissive thresholds for development/testing',
      ko: '개발/테스트용 허용적인 임계값',
    }),
    strictnessMediumDesc: t({
      en: 'Balanced defaults (recommended)',
      ko: '균형잡힌 기본값 (권장)',
    }),
    strictnessStrictDesc: t({
      en: 'Tight thresholds for production data',
      ko: '프로덕션 데이터용 엄격한 임계값',
    }),

    // Presets
    preset: t({ en: 'Preset', ko: '프리셋' }),
    presetNone: t({ en: 'No preset', ko: '프리셋 없음' }),
    presetDefault: t({ en: 'Default', ko: '기본' }),
    presetStrict: t({ en: 'Strict', ko: '엄격' }),
    presetLoose: t({ en: 'Loose', ko: '느슨함' }),
    presetMinimal: t({ en: 'Minimal', ko: '최소' }),
    presetComprehensive: t({ en: 'Comprehensive', ko: '종합' }),
    presetCiCd: t({ en: 'CI/CD', ko: 'CI/CD' }),
    presetSchemaOnly: t({ en: 'Schema Only', ko: '스키마만' }),
    presetFormatOnly: t({ en: 'Format Only', ko: '포맷만' }),

    // Preset descriptions
    presetDefaultDesc: t({
      en: 'General purpose validation rules',
      ko: '범용 검증 규칙',
    }),
    presetStrictDesc: t({
      en: 'Production data pipelines, data quality gates',
      ko: '프로덕션 데이터 파이프라인, 품질 게이트',
    }),
    presetLooseDesc: t({
      en: 'Development, testing, exploratory analysis',
      ko: '개발, 테스트, 탐색적 분석',
    }),
    presetMinimalDesc: t({
      en: 'Essential rules only, minimal overhead',
      ko: '필수 규칙만, 최소 오버헤드',
    }),
    presetComprehensiveDesc: t({
      en: 'Full data audit, compliance checks',
      ko: '전체 데이터 감사, 규정 준수 검사',
    }),
    presetCiCdDesc: t({
      en: 'Fast execution, clear failures',
      ko: '빠른 실행, 명확한 실패',
    }),
    presetSchemaOnlyDesc: t({
      en: 'Schema drift detection, structure validation',
      ko: '스키마 드리프트 감지, 구조 검증',
    }),
    presetFormatOnlyDesc: t({
      en: 'Data format validation, PII detection',
      ko: '데이터 형식 검증, PII 탐지',
    }),

    // Export formats
    exportFormat: t({ en: 'Export Format', ko: '내보내기 형식' }),
    exportYaml: t({ en: 'YAML', ko: 'YAML' }),
    exportJson: t({ en: 'JSON', ko: 'JSON' }),
    exportPython: t({ en: 'Python', ko: 'Python' }),
    exportToml: t({ en: 'TOML', ko: 'TOML' }),
    exportYamlDesc: t({
      en: 'Human-readable configuration format',
      ko: '사람이 읽기 쉬운 설정 형식',
    }),
    exportJsonDesc: t({
      en: 'Machine-readable format',
      ko: '기계가 읽기 쉬운 형식',
    }),
    exportPythonDesc: t({
      en: 'Executable Python code',
      ko: '실행 가능한 Python 코드',
    }),
    exportTomlDesc: t({
      en: 'Configuration-friendly format',
      ko: '설정에 적합한 형식',
    }),

    // Export actions
    exportRules: t({ en: 'Export Rules', ko: '규칙 내보내기' }),
    downloadRules: t({ en: 'Download', ko: '다운로드' }),
    copyToClipboard: t({ en: 'Copy to Clipboard', ko: '클립보드에 복사' }),
    copied: t({ en: 'Copied!', ko: '복사됨!' }),
    exporting: t({ en: 'Exporting...', ko: '내보내는 중...' }),
    exportSuccess: t({
      en: 'Rules exported successfully',
      ko: '규칙을 성공적으로 내보냈습니다',
    }),

    // Category filtering
    categoryFilter: t({ en: 'Categories', ko: '카테고리' }),
    includedCategories: t({ en: 'Included Categories', ko: '포함된 카테고리' }),
    excludedCategories: t({ en: 'Excluded Categories', ko: '제외된 카테고리' }),

    // Summary stats
    byCategory: t({ en: 'By Category', ko: '카테고리별' }),
    ruleCount: t({ en: 'rules', ko: '규칙' }),

    // Min confidence
    minConfidence: t({ en: 'Min Confidence', ko: '최소 신뢰도' }),
    minConfidenceDesc: t({
      en: 'Only suggest rules with confidence above this threshold',
      ko: '이 임계값 이상의 신뢰도를 가진 규칙만 제안',
    }),

    // =========================================================================
    // Cross-Column Rules
    // =========================================================================

    // Tab and section headers
    crossColumnRules: t({ en: 'Cross-Column Rules', ko: '크로스 컬럼 규칙' }),
    singleColumnRules: t({ en: 'Single-Column Rules', ko: '단일 컬럼 규칙' }),
    crossColumnDescription: t({
      en: 'Rules that validate relationships between multiple columns',
      ko: '여러 컬럼 간의 관계를 검증하는 규칙',
    }),

    // Cross-column stats
    crossColumnCount: t({ en: 'cross-column', ko: '크로스 컬럼' }),
    relationships: t({ en: 'relationships', ko: '관계' }),

    // Categories for cross-column
    relationship: t({ en: 'Relationship', ko: '관계' }),
    multiColumn: t({ en: 'Multi-Column', ko: '다중 컬럼' }),

    // Cross-column rule types
    compositeKey: t({ en: 'Composite Key', ko: '복합 키' }),
    compositeKeyDesc: t({
      en: 'Multi-column uniqueness constraint',
      ko: '다중 컬럼 고유성 제약',
    }),
    columnComparison: t({ en: 'Column Comparison', ko: '컬럼 비교' }),
    columnComparisonDesc: t({
      en: 'Validates comparison relationships (>, <, >=, <=)',
      ko: '비교 관계 검증 (>, <, >=, <=)',
    }),
    columnSum: t({ en: 'Column Sum', ko: '컬럼 합계' }),
    columnSumDesc: t({
      en: 'Validates that columns sum to a target',
      ko: '컬럼 합이 목표 값과 일치하는지 검증',
    }),
    columnDependency: t({ en: 'Column Dependency', ko: '컬럼 종속성' }),
    columnDependencyDesc: t({
      en: 'Validates functional dependencies between columns',
      ko: '컬럼 간 함수적 종속성 검증',
    }),
    columnImplication: t({ en: 'Column Implication', ko: '컬럼 함축' }),
    columnImplicationDesc: t({
      en: 'If condition A, then B must be true',
      ko: '조건 A이면 B가 참이어야 함',
    }),
    columnCoexistence: t({ en: 'Column Coexistence', ko: '컬럼 공존' }),
    columnCoexistenceDesc: t({
      en: 'All columns must be null or all non-null',
      ko: '모든 컬럼이 null이거나 모두 non-null',
    }),
    columnMutualExclusivity: t({ en: 'Mutual Exclusivity', ko: '상호 배제' }),
    columnMutualExclusivityDesc: t({
      en: 'At most one column can be non-null',
      ko: '최대 하나의 컬럼만 non-null일 수 있음',
    }),
    columnRatio: t({ en: 'Column Ratio', ko: '컬럼 비율' }),
    columnRatioDesc: t({
      en: 'Validates ratio between columns',
      ko: '컬럼 간 비율 검증',
    }),
    columnCorrelation: t({ en: 'Column Correlation', ko: '컬럼 상관관계' }),
    columnCorrelationDesc: t({
      en: 'Validates correlation between numeric columns',
      ko: '숫자 컬럼 간 상관관계 검증',
    }),

    // New cross-column rule types (added)
    columnProduct: t({ en: 'Column Product', ko: '컬럼 곱셈' }),
    columnProductDesc: t({
      en: 'Validates multiplication relationship (A × B = C)',
      ko: '곱셈 관계 검증 (A × B = C)',
    }),
    columnDifference: t({ en: 'Column Difference', ko: '컬럼 차이' }),
    columnDifferenceDesc: t({
      en: 'Validates difference relationship (A - B = C)',
      ko: '차이 관계 검증 (A - B = C)',
    }),
    columnPercentage: t({ en: 'Column Percentage', ko: '컬럼 백분율' }),
    columnPercentageDesc: t({
      en: 'Validates percentage calculation (Base × Pct% = Result)',
      ko: '백분율 계산 검증 (기준 × 백분율% = 결과)',
    }),
    columnChainComparison: t({ en: 'Chain Comparison', ko: '체인 비교' }),
    columnChainComparisonDesc: t({
      en: 'Validates ordered chain (A ≤ B ≤ C)',
      ko: '순서 체인 검증 (A ≤ B ≤ C)',
    }),
    referentialIntegrity: t({ en: 'Referential Integrity', ko: '참조 무결성' }),
    referentialIntegrityDesc: t({
      en: 'Validates foreign key relationships between tables',
      ko: '테이블 간 외래 키 관계 검증',
    }),

    // Cross-column rule UI
    involvedColumns: t({ en: 'Involved Columns', ko: '관련 컬럼' }),
    ruleType: t({ en: 'Rule Type', ko: '규칙 유형' }),
    evidence: t({ en: 'Evidence', ko: '근거' }),
    sampleViolations: t({ en: 'Sample Violations', ko: '위반 샘플' }),
    noViolationsFound: t({
      en: 'No violations found in sample data',
      ko: '샘플 데이터에서 위반 사항 없음',
    }),

    // Cross-column presets
    presetCrossColumn: t({ en: 'Cross-Column', ko: '크로스 컬럼' }),
    presetCrossColumnDesc: t({
      en: 'Focus on cross-column relationships and constraints',
      ko: '크로스 컬럼 관계 및 제약에 집중',
    }),
    presetDataIntegrity: t({ en: 'Data Integrity', ko: '데이터 무결성' }),
    presetDataIntegrityDesc: t({
      en: 'Comprehensive data integrity including cross-column rules',
      ko: '크로스 컬럼 규칙을 포함한 종합 데이터 무결성',
    }),

    // Cross-column toggle
    enableCrossColumn: t({ en: 'Enable Cross-Column Rules', ko: '크로스 컬럼 규칙 활성화' }),
    enableCrossColumnDesc: t({
      en: 'Analyze relationships between columns to suggest cross-column validation rules',
      ko: '컬럼 간 관계를 분석하여 크로스 컬럼 검증 규칙 제안',
    }),

    // Cross-column type filter
    crossColumnTypes: t({ en: 'Cross-Column Types', ko: '크로스 컬럼 유형' }),
    byCrossColumnType: t({ en: 'By Type', ko: '유형별' }),
  },
} satisfies Dictionary

export default ruleSuggestionsContent
