/* eslint-disable */
export default {
  "key": "privacy",
  "content": {
    "nodeType": "translation",
    "translation": {
      "en": {
        "title": "Privacy & Compliance",
        "subtitle": "Detect and protect sensitive personal information",
        "tabs": {
          "scan": "PII Scan",
          "mask": "Data Masking",
          "history": "History"
        },
        "scan": {
          "title": "PII Detection",
          "subtitle": "Scan data sources to detect personally identifiable information",
          "runScan": "Run Scan",
          "scanning": "Scanning...",
          "scanComplete": "Scan complete",
          "scanFailed": "Scan failed",
          "columnsScanned": "Columns Scanned",
          "columnsWithPII": "Columns with PII",
          "totalFindings": "Total Findings",
          "avgConfidence": "Avg. Confidence"
        },
        "piiTypes": {
          "email": "Email",
          "phone": "Phone Number",
          "ssn": "SSN",
          "credit_card": "Credit Card",
          "ip_address": "IP Address",
          "date_of_birth": "Date of Birth",
          "address": "Address",
          "name": "Name",
          "passport": "Passport",
          "driver_license": "Driver License"
        },
        "regulations": {
          "title": "Regulations",
          "gdpr": "GDPR",
          "ccpa": "CCPA",
          "lgpd": "LGPD",
          "hipaa": "HIPAA",
          "pci_dss": "PCI-DSS"
        },
        "mask": {
          "title": "Data Masking",
          "subtitle": "Apply masking strategies to protect sensitive data",
          "runMask": "Apply Masking",
          "masking": "Masking...",
          "maskComplete": "Masking complete",
          "maskFailed": "Masking failed",
          "columnsMasked": "Columns Masked",
          "outputPath": "Output Path",
          "downloadMasked": "Download Masked Data"
        },
        "strategies": {
          "title": "Masking Strategy",
          "redact": "Redact",
          "redactDesc": "Replace sensitive values with asterisks or placeholder text",
          "hash": "Hash",
          "hashDesc": "Apply one-way hashing to preserve referential integrity",
          "fake": "Fake",
          "fakeDesc": "Generate realistic fake data while preserving format"
        },
        "config": {
          "selectSource": "Select Data Source",
          "selectColumns": "Select Columns",
          "allColumns": "All Columns",
          "minConfidence": "Minimum Confidence",
          "minConfidenceDesc": "Minimum confidence threshold for PII detection",
          "selectRegulations": "Select Regulations"
        },
        "table": {
          "column": "Column",
          "piiType": "PII Type",
          "confidence": "Confidence",
          "sampleCount": "Sample Count",
          "regulation": "Regulation",
          "status": "Status",
          "actions": "Actions"
        },
        "risk": {
          "critical": "Critical",
          "high": "High",
          "medium": "Medium",
          "low": "Low"
        },
        "empty": {
          "noScans": "No scans yet",
          "noScansDesc": "Run a PII scan to detect sensitive data in your sources",
          "noMasks": "No masking operations yet",
          "noMasksDesc": "Apply masking to protect sensitive data",
          "noPIIFound": "No PII detected",
          "noPIIFoundDesc": "Great! No personally identifiable information was found"
        },
        "history": {
          "scanHistory": "Scan History",
          "maskHistory": "Masking History",
          "ranAt": "Ran at",
          "duration": "Duration",
          "viewDetails": "View Details"
        },
        "actions": {
          "maskColumn": "Mask Column",
          "ignoreColumn": "Ignore",
          "markSafe": "Mark as Safe",
          "exportReport": "Export Report"
        },
        "messages": {
          "selectSourceFirst": "Please select a data source first",
          "scanStarted": "Scan started",
          "maskingStarted": "Masking started"
        }
      },
      "ko": {
        "title": "프라이버시 & 컴플라이언스",
        "subtitle": "민감한 개인정보 탐지 및 보호",
        "tabs": {
          "scan": "PII 스캔",
          "mask": "데이터 마스킹",
          "history": "이력"
        },
        "scan": {
          "title": "PII 탐지",
          "subtitle": "데이터 소스를 스캔하여 개인 식별 정보 탐지",
          "runScan": "스캔 실행",
          "scanning": "스캔 중...",
          "scanComplete": "스캔 완료",
          "scanFailed": "스캔 실패",
          "columnsScanned": "스캔된 컬럼",
          "columnsWithPII": "PII 포함 컬럼",
          "totalFindings": "총 발견",
          "avgConfidence": "평균 신뢰도"
        },
        "piiTypes": {
          "email": "이메일",
          "phone": "전화번호",
          "ssn": "주민등록번호",
          "credit_card": "신용카드",
          "ip_address": "IP 주소",
          "date_of_birth": "생년월일",
          "address": "주소",
          "name": "이름",
          "passport": "여권번호",
          "driver_license": "운전면허"
        },
        "regulations": {
          "title": "규정",
          "gdpr": "GDPR",
          "ccpa": "CCPA",
          "lgpd": "LGPD",
          "hipaa": "HIPAA",
          "pci_dss": "PCI-DSS"
        },
        "mask": {
          "title": "데이터 마스킹",
          "subtitle": "민감한 데이터 보호를 위한 마스킹 전략 적용",
          "runMask": "마스킹 적용",
          "masking": "마스킹 중...",
          "maskComplete": "마스킹 완료",
          "maskFailed": "마스킹 실패",
          "columnsMasked": "마스킹된 컬럼",
          "outputPath": "출력 경로",
          "downloadMasked": "마스킹된 데이터 다운로드"
        },
        "strategies": {
          "title": "마스킹 전략",
          "redact": "삭제",
          "redactDesc": "민감한 값을 별표 또는 플레이스홀더 텍스트로 대체",
          "hash": "해시",
          "hashDesc": "참조 무결성 유지를 위한 단방향 해싱 적용",
          "fake": "가짜 데이터",
          "fakeDesc": "형식을 유지하면서 현실적인 가짜 데이터 생성"
        },
        "config": {
          "selectSource": "데이터 소스 선택",
          "selectColumns": "컬럼 선택",
          "allColumns": "모든 컬럼",
          "minConfidence": "최소 신뢰도",
          "minConfidenceDesc": "PII 탐지를 위한 최소 신뢰도 임계값",
          "selectRegulations": "규정 선택"
        },
        "table": {
          "column": "컬럼",
          "piiType": "PII 유형",
          "confidence": "신뢰도",
          "sampleCount": "샘플 수",
          "regulation": "규정",
          "status": "상태",
          "actions": "작업"
        },
        "risk": {
          "critical": "심각",
          "high": "높음",
          "medium": "중간",
          "low": "낮음"
        },
        "empty": {
          "noScans": "스캔 기록 없음",
          "noScansDesc": "소스에서 민감한 데이터를 탐지하려면 PII 스캔을 실행하세요",
          "noMasks": "마스킹 작업 없음",
          "noMasksDesc": "민감한 데이터 보호를 위해 마스킹을 적용하세요",
          "noPIIFound": "PII가 감지되지 않았습니다",
          "noPIIFoundDesc": "좋습니다! 개인 식별 정보가 발견되지 않았습니다"
        },
        "history": {
          "scanHistory": "스캔 이력",
          "maskHistory": "마스킹 이력",
          "ranAt": "실행 시간",
          "duration": "소요 시간",
          "viewDetails": "상세 보기"
        },
        "actions": {
          "maskColumn": "컬럼 마스킹",
          "ignoreColumn": "무시",
          "markSafe": "안전으로 표시",
          "exportReport": "보고서 내보내기"
        },
        "messages": {
          "selectSourceFirst": "먼저 데이터 소스를 선택하세요",
          "scanStarted": "스캔이 시작되었습니다",
          "maskingStarted": "마스킹이 시작되었습니다"
        }
      }
    }
  },
  "localIds": [
    "privacy::local::src/content/privacy.content.ts"
  ]
} as const;
