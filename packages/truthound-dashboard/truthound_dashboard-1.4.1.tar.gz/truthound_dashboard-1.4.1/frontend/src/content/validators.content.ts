/**
 * Validator configuration UI translations.
 *
 * This file contains translations for the validator selection and configuration UI.
 */
import { t, type Dictionary } from 'intlayer'

const validatorsContent = {
  key: 'validators',
  content: {
    // Page titles
    title: t({ en: 'Validators', ko: '검증기' }),
    selectValidators: t({ en: 'Select Validators', ko: '검증기 선택' }),
    configureValidators: t({ en: 'Configure Validators', ko: '검증기 설정' }),

    // Categories
    categories: {
      schema: t({ en: 'Schema', ko: '스키마' }),
      completeness: t({ en: 'Completeness', ko: '완전성' }),
      uniqueness: t({ en: 'Uniqueness', ko: '유일성' }),
      distribution: t({ en: 'Distribution', ko: '분포' }),
      string: t({ en: 'String', ko: '문자열' }),
      datetime: t({ en: 'Datetime', ko: '날짜/시간' }),
      aggregate: t({ en: 'Aggregate', ko: '집계' }),
      crossTable: t({ en: 'Cross-Table', ko: '테이블 간' }),
      query: t({ en: 'Query', ko: '쿼리' }),
      multiColumn: t({ en: 'Multi-Column', ko: '다중 열' }),
      table: t({ en: 'Table', ko: '테이블' }),
      geospatial: t({ en: 'Geospatial', ko: '지리공간' }),
      drift: t({ en: 'Drift', ko: '드리프트' }),
      anomaly: t({ en: 'Anomaly', ko: '이상 탐지' }),
      privacy: t({ en: 'Privacy', ko: '프라이버시' }),
      timeSeries: t({ en: 'Time Series', ko: '시계열' }),
      referential: t({ en: 'Referential', ko: '참조' }),
      streaming: t({ en: 'Streaming', ko: '스트리밍' }),
      business: t({ en: 'Business', ko: '비즈니스' }),
    },

    // Category descriptions
    categoryDescriptions: {
      schema: t({
        en: 'Validate structure, columns, and data types',
        ko: '구조, 열, 데이터 타입 검증',
      }),
      completeness: t({
        en: 'Check for null values and missing data',
        ko: 'Null 값 및 누락 데이터 확인',
      }),
      uniqueness: t({
        en: 'Detect duplicates and validate keys',
        ko: '중복 탐지 및 키 검증',
      }),
      distribution: t({
        en: 'Validate value ranges and distributions',
        ko: '값 범위 및 분포 검증',
      }),
      string: t({
        en: 'Pattern matching and format validation',
        ko: '패턴 매칭 및 형식 검증',
      }),
      datetime: t({
        en: 'Date/time format and range validation',
        ko: '날짜/시간 형식 및 범위 검증',
      }),
      aggregate: t({
        en: 'Statistical aggregate checks (mean, sum, etc.)',
        ko: '통계적 집계 검사 (평균, 합계 등)',
      }),
      crossTable: t({
        en: 'Multi-table relationships and foreign keys',
        ko: '다중 테이블 관계 및 외래 키',
      }),
      multiColumn: t({
        en: 'Column relationships and calculations',
        ko: '열 간 관계 및 계산',
      }),
      query: t({
        en: 'Expression-based custom validation',
        ko: '표현식 기반 사용자 정의 검증',
      }),
      table: t({
        en: 'Table metadata and structure validation',
        ko: '테이블 메타데이터 및 구조 검증',
      }),
      geospatial: t({
        en: 'Geographic coordinate validation',
        ko: '지리적 좌표 검증',
      }),
      drift: t({
        en: 'Distribution change detection between datasets',
        ko: '데이터셋 간 분포 변화 감지',
      }),
      anomaly: t({
        en: 'ML-based outlier and anomaly detection',
        ko: 'ML 기반 이상치 및 이상 탐지',
      }),
      privacy: t({
        en: 'PII detection and compliance (GDPR, CCPA)',
        ko: 'PII 탐지 및 규정 준수 (GDPR, CCPA)',
      }),
      timeSeries: t({
        en: 'Time series data validation',
        ko: '시계열 데이터 검증',
      }),
      referential: t({
        en: 'Referential integrity validation',
        ko: '참조 무결성 검증',
      }),
      streaming: t({
        en: 'Streaming data validation',
        ko: '스트리밍 데이터 검증',
      }),
      business: t({
        en: 'Business rule validation',
        ko: '비즈니스 규칙 검증',
      }),
    },

    // Presets
    presets: {
      custom: t({ en: 'Custom', ko: '사용자 정의' }),
      allValidators: t({ en: 'All Validators', ko: '모든 검증기' }),
      quickCheck: t({ en: 'Quick Check', ko: '빠른 검사' }),
      schemaOnly: t({ en: 'Schema Only', ko: '스키마만' }),
      dataQuality: t({ en: 'Data Quality', ko: '데이터 품질' }),
    },

    // Preset descriptions
    presetDescriptions: {
      allValidators: t({
        en: 'Run all available validators',
        ko: '모든 사용 가능한 검증기 실행',
      }),
      quickCheck: t({
        en: 'Fast validation for common issues',
        ko: '일반적인 문제에 대한 빠른 검증',
      }),
      schemaOnly: t({
        en: 'Structure and type validation',
        ko: '구조 및 타입 검증',
      }),
      dataQuality: t({
        en: 'Completeness and uniqueness checks',
        ko: '완전성 및 유일성 검사',
      }),
    },

    // Actions
    enableAll: t({ en: 'Enable All', ko: '모두 활성화' }),
    disableAll: t({ en: 'Disable All', ko: '모두 비활성화' }),
    configured: t({ en: 'Configured', ko: '설정됨' }),

    // Status
    enabled: t({ en: 'enabled', ko: '활성화' }),
    validators: t({ en: 'validators', ko: '검증기' }),
    noValidatorsMatch: t({
      en: 'No validators match your search criteria.',
      ko: '검색 조건에 맞는 검증기가 없습니다.',
    }),

    // Parameters
    parameters: {
      column: t({ en: 'Column', ko: '열' }),
      columns: t({ en: 'Columns', ko: '열 목록' }),
      addColumn: t({ en: 'Add column...', ko: '열 추가...' }),
      addValue: t({ en: 'Add value...', ko: '값 추가...' }),
      selectColumn: t({ en: 'Select column...', ko: '열 선택...' }),
      requiredField: t({ en: 'This field is required', ko: '필수 입력 항목입니다' }),
    },

    // Severity
    severity: {
      low: t({ en: 'Low', ko: '낮음' }),
      medium: t({ en: 'Medium', ko: '중간' }),
      high: t({ en: 'High', ko: '높음' }),
      critical: t({ en: 'Critical', ko: '심각' }),
    },

    // Parameter types
    parameterTypes: {
      string: t({ en: 'Text', ko: '텍스트' }),
      integer: t({ en: 'Integer', ko: '정수' }),
      float: t({ en: 'Number', ko: '숫자' }),
      boolean: t({ en: 'Yes/No', ko: '예/아니오' }),
      select: t({ en: 'Select', ko: '선택' }),
      multiSelect: t({ en: 'Multi-select', ko: '다중 선택' }),
      regex: t({ en: 'Regex Pattern', ko: '정규식 패턴' }),
      expression: t({ en: 'Expression', ko: '표현식' }),
      schema: t({ en: 'Schema (JSON)', ko: '스키마 (JSON)' }),
    },

    // Tooltips
    tooltips: {
      mostly: t({
        en: 'Acceptable ratio (0.0-1.0). E.g., 0.95 means 5% exceptions allowed.',
        ko: '허용 비율 (0.0-1.0). 예: 0.95는 5% 예외 허용을 의미합니다.',
      }),
      strict: t({
        en: 'If enabled, validation fails strictly on any violation.',
        ko: '활성화하면 모든 위반에 대해 엄격하게 검증에 실패합니다.',
      }),
    },

    // Errors
    errors: {
      loadFailed: t({
        en: 'Failed to load validators',
        ko: '검증기 로드 실패',
      }),
      invalidRegex: t({
        en: 'Invalid regular expression',
        ko: '잘못된 정규식',
      }),
      invalidJson: t({
        en: 'Invalid JSON format',
        ko: '잘못된 JSON 형식',
      }),
      minValue: t({
        en: 'Value must be at least',
        ko: '값은 최소',
      }),
      maxValue: t({
        en: 'Value must be at most',
        ko: '값은 최대',
      }),
    },
  },
} satisfies Dictionary

export default validatorsContent
