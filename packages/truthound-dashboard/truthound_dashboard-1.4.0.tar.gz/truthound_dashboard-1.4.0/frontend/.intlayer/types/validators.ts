/* eslint-disable */
export default {
  "key": "validators",
  "content": {
    "nodeType": "translation",
    "translation": {
      "en": {
        "title": "Validators",
        "selectValidators": "Select Validators",
        "configureValidators": "Configure Validators",
        "categories": {
          "schema": "Schema",
          "completeness": "Completeness",
          "uniqueness": "Uniqueness",
          "distribution": "Distribution",
          "string": "String",
          "datetime": "Datetime",
          "aggregate": "Aggregate",
          "crossTable": "Cross-Table",
          "query": "Query",
          "multiColumn": "Multi-Column",
          "table": "Table",
          "geospatial": "Geospatial",
          "drift": "Drift",
          "anomaly": "Anomaly",
          "privacy": "Privacy",
          "timeSeries": "Time Series",
          "referential": "Referential",
          "streaming": "Streaming",
          "business": "Business"
        },
        "categoryDescriptions": {
          "schema": "Validate structure, columns, and data types",
          "completeness": "Check for null values and missing data",
          "uniqueness": "Detect duplicates and validate keys",
          "distribution": "Validate value ranges and distributions",
          "string": "Pattern matching and format validation",
          "datetime": "Date/time format and range validation",
          "aggregate": "Statistical aggregate checks (mean, sum, etc.)",
          "crossTable": "Multi-table relationships and foreign keys",
          "multiColumn": "Column relationships and calculations",
          "query": "Expression-based custom validation",
          "table": "Table metadata and structure validation",
          "geospatial": "Geographic coordinate validation",
          "drift": "Distribution change detection between datasets",
          "anomaly": "ML-based outlier and anomaly detection",
          "privacy": "PII detection and compliance (GDPR, CCPA)",
          "timeSeries": "Time series data validation",
          "referential": "Referential integrity validation",
          "streaming": "Streaming data validation",
          "business": "Business rule validation"
        },
        "presets": {
          "custom": "Custom",
          "allValidators": "All Validators",
          "quickCheck": "Quick Check",
          "schemaOnly": "Schema Only",
          "dataQuality": "Data Quality"
        },
        "presetDescriptions": {
          "allValidators": "Run all available validators",
          "quickCheck": "Fast validation for common issues",
          "schemaOnly": "Structure and type validation",
          "dataQuality": "Completeness and uniqueness checks"
        },
        "enableAll": "Enable All",
        "disableAll": "Disable All",
        "configured": "Configured",
        "enabled": "enabled",
        "validators": "validators",
        "noValidatorsMatch": "No validators match your search criteria.",
        "parameters": {
          "column": "Column",
          "columns": "Columns",
          "addColumn": "Add column...",
          "addValue": "Add value...",
          "selectColumn": "Select column...",
          "requiredField": "This field is required"
        },
        "severity": {
          "low": "Low",
          "medium": "Medium",
          "high": "High",
          "critical": "Critical"
        },
        "parameterTypes": {
          "string": "Text",
          "integer": "Integer",
          "float": "Number",
          "boolean": "Yes/No",
          "select": "Select",
          "multiSelect": "Multi-select",
          "regex": "Regex Pattern",
          "expression": "Expression",
          "schema": "Schema (JSON)"
        },
        "tooltips": {
          "mostly": "Acceptable ratio (0.0-1.0). E.g., 0.95 means 5% exceptions allowed.",
          "strict": "If enabled, validation fails strictly on any violation."
        },
        "errors": {
          "loadFailed": "Failed to load validators",
          "invalidRegex": "Invalid regular expression",
          "invalidJson": "Invalid JSON format",
          "minValue": "Value must be at least",
          "maxValue": "Value must be at most"
        }
      },
      "ko": {
        "title": "검증기",
        "selectValidators": "검증기 선택",
        "configureValidators": "검증기 설정",
        "categories": {
          "schema": "스키마",
          "completeness": "완전성",
          "uniqueness": "유일성",
          "distribution": "분포",
          "string": "문자열",
          "datetime": "날짜/시간",
          "aggregate": "집계",
          "crossTable": "테이블 간",
          "query": "쿼리",
          "multiColumn": "다중 열",
          "table": "테이블",
          "geospatial": "지리공간",
          "drift": "드리프트",
          "anomaly": "이상 탐지",
          "privacy": "프라이버시",
          "timeSeries": "시계열",
          "referential": "참조",
          "streaming": "스트리밍",
          "business": "비즈니스"
        },
        "categoryDescriptions": {
          "schema": "구조, 열, 데이터 타입 검증",
          "completeness": "Null 값 및 누락 데이터 확인",
          "uniqueness": "중복 탐지 및 키 검증",
          "distribution": "값 범위 및 분포 검증",
          "string": "패턴 매칭 및 형식 검증",
          "datetime": "날짜/시간 형식 및 범위 검증",
          "aggregate": "통계적 집계 검사 (평균, 합계 등)",
          "crossTable": "다중 테이블 관계 및 외래 키",
          "multiColumn": "열 간 관계 및 계산",
          "query": "표현식 기반 사용자 정의 검증",
          "table": "테이블 메타데이터 및 구조 검증",
          "geospatial": "지리적 좌표 검증",
          "drift": "데이터셋 간 분포 변화 감지",
          "anomaly": "ML 기반 이상치 및 이상 탐지",
          "privacy": "PII 탐지 및 규정 준수 (GDPR, CCPA)",
          "timeSeries": "시계열 데이터 검증",
          "referential": "참조 무결성 검증",
          "streaming": "스트리밍 데이터 검증",
          "business": "비즈니스 규칙 검증"
        },
        "presets": {
          "custom": "사용자 정의",
          "allValidators": "모든 검증기",
          "quickCheck": "빠른 검사",
          "schemaOnly": "스키마만",
          "dataQuality": "데이터 품질"
        },
        "presetDescriptions": {
          "allValidators": "모든 사용 가능한 검증기 실행",
          "quickCheck": "일반적인 문제에 대한 빠른 검증",
          "schemaOnly": "구조 및 타입 검증",
          "dataQuality": "완전성 및 유일성 검사"
        },
        "enableAll": "모두 활성화",
        "disableAll": "모두 비활성화",
        "configured": "설정됨",
        "enabled": "활성화",
        "validators": "검증기",
        "noValidatorsMatch": "검색 조건에 맞는 검증기가 없습니다.",
        "parameters": {
          "column": "열",
          "columns": "열 목록",
          "addColumn": "열 추가...",
          "addValue": "값 추가...",
          "selectColumn": "열 선택...",
          "requiredField": "필수 입력 항목입니다"
        },
        "severity": {
          "low": "낮음",
          "medium": "중간",
          "high": "높음",
          "critical": "심각"
        },
        "parameterTypes": {
          "string": "텍스트",
          "integer": "정수",
          "float": "숫자",
          "boolean": "예/아니오",
          "select": "선택",
          "multiSelect": "다중 선택",
          "regex": "정규식 패턴",
          "expression": "표현식",
          "schema": "스키마 (JSON)"
        },
        "tooltips": {
          "mostly": "허용 비율 (0.0-1.0). 예: 0.95는 5% 예외 허용을 의미합니다.",
          "strict": "활성화하면 모든 위반에 대해 엄격하게 검증에 실패합니다."
        },
        "errors": {
          "loadFailed": "검증기 로드 실패",
          "invalidRegex": "잘못된 정규식",
          "invalidJson": "잘못된 JSON 형식",
          "minValue": "값은 최소",
          "maxValue": "값은 최대"
        }
      }
    }
  },
  "localIds": [
    "validators::local::src/content/validators.content.ts"
  ]
} as const;
