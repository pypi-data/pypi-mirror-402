/**
 * Privacy (PII Scan & Data Masking) translations.
 *
 * Contains translations for PII detection and data masking features.
 */
import { t, type Dictionary } from 'intlayer'

const privacyContent = {
  key: 'privacy',
  content: {
    title: t({ en: 'Privacy & Compliance', ko: '프라이버시 & 컴플라이언스' }),
    subtitle: t({
      en: 'Detect and protect sensitive personal information',
      ko: '민감한 개인정보 탐지 및 보호',
    }),

    // Tabs
    tabs: {
      scan: t({ en: 'PII Scan', ko: 'PII 스캔' }),
      mask: t({ en: 'Data Masking', ko: '데이터 마스킹' }),
      history: t({ en: 'History', ko: '이력' }),
    },

    // PII Scan Section
    scan: {
      title: t({ en: 'PII Detection', ko: 'PII 탐지' }),
      subtitle: t({
        en: 'Scan data sources to detect personally identifiable information',
        ko: '데이터 소스를 스캔하여 개인 식별 정보 탐지',
      }),
      runScan: t({ en: 'Run Scan', ko: '스캔 실행' }),
      scanning: t({ en: 'Scanning...', ko: '스캔 중...' }),
      scanComplete: t({ en: 'Scan complete', ko: '스캔 완료' }),
      scanFailed: t({ en: 'Scan failed', ko: '스캔 실패' }),
      columnsScanned: t({ en: 'Columns Scanned', ko: '스캔된 컬럼' }),
      columnsWithPII: t({ en: 'Columns with PII', ko: 'PII 포함 컬럼' }),
      totalFindings: t({ en: 'Total Findings', ko: '총 발견' }),
      avgConfidence: t({ en: 'Avg. Confidence', ko: '평균 신뢰도' }),
    },

    // PII Types
    piiTypes: {
      email: t({ en: 'Email', ko: '이메일' }),
      phone: t({ en: 'Phone Number', ko: '전화번호' }),
      ssn: t({ en: 'SSN', ko: '주민등록번호' }),
      credit_card: t({ en: 'Credit Card', ko: '신용카드' }),
      ip_address: t({ en: 'IP Address', ko: 'IP 주소' }),
      date_of_birth: t({ en: 'Date of Birth', ko: '생년월일' }),
      address: t({ en: 'Address', ko: '주소' }),
      name: t({ en: 'Name', ko: '이름' }),
      passport: t({ en: 'Passport', ko: '여권번호' }),
      driver_license: t({ en: 'Driver License', ko: '운전면허' }),
    },

    // Regulations
    regulations: {
      title: t({ en: 'Regulations', ko: '규정' }),
      gdpr: t({ en: 'GDPR', ko: 'GDPR' }),
      ccpa: t({ en: 'CCPA', ko: 'CCPA' }),
      lgpd: t({ en: 'LGPD', ko: 'LGPD' }),
      hipaa: t({ en: 'HIPAA', ko: 'HIPAA' }),
      pci_dss: t({ en: 'PCI-DSS', ko: 'PCI-DSS' }),
    },

    // Data Masking Section
    mask: {
      title: t({ en: 'Data Masking', ko: '데이터 마스킹' }),
      subtitle: t({
        en: 'Apply masking strategies to protect sensitive data',
        ko: '민감한 데이터 보호를 위한 마스킹 전략 적용',
      }),
      runMask: t({ en: 'Apply Masking', ko: '마스킹 적용' }),
      masking: t({ en: 'Masking...', ko: '마스킹 중...' }),
      maskComplete: t({ en: 'Masking complete', ko: '마스킹 완료' }),
      maskFailed: t({ en: 'Masking failed', ko: '마스킹 실패' }),
      columnsMasked: t({ en: 'Columns Masked', ko: '마스킹된 컬럼' }),
      outputPath: t({ en: 'Output Path', ko: '출력 경로' }),
      downloadMasked: t({ en: 'Download Masked Data', ko: '마스킹된 데이터 다운로드' }),
    },

    // Masking Strategies
    strategies: {
      title: t({ en: 'Masking Strategy', ko: '마스킹 전략' }),
      redact: t({ en: 'Redact', ko: '삭제' }),
      redactDesc: t({
        en: 'Replace sensitive values with asterisks or placeholder text',
        ko: '민감한 값을 별표 또는 플레이스홀더 텍스트로 대체',
      }),
      hash: t({ en: 'Hash', ko: '해시' }),
      hashDesc: t({
        en: 'Apply one-way hashing to preserve referential integrity',
        ko: '참조 무결성 유지를 위한 단방향 해싱 적용',
      }),
      fake: t({ en: 'Fake', ko: '가짜 데이터' }),
      fakeDesc: t({
        en: 'Generate realistic fake data while preserving format',
        ko: '형식을 유지하면서 현실적인 가짜 데이터 생성',
      }),
    },

    // Configuration
    config: {
      selectSource: t({ en: 'Select Data Source', ko: '데이터 소스 선택' }),
      selectColumns: t({ en: 'Select Columns', ko: '컬럼 선택' }),
      allColumns: t({ en: 'All Columns', ko: '모든 컬럼' }),
      minConfidence: t({ en: 'Minimum Confidence', ko: '최소 신뢰도' }),
      minConfidenceDesc: t({
        en: 'Minimum confidence threshold for PII detection',
        ko: 'PII 탐지를 위한 최소 신뢰도 임계값',
      }),
      selectRegulations: t({ en: 'Select Regulations', ko: '규정 선택' }),
    },

    // Results Table
    table: {
      column: t({ en: 'Column', ko: '컬럼' }),
      piiType: t({ en: 'PII Type', ko: 'PII 유형' }),
      confidence: t({ en: 'Confidence', ko: '신뢰도' }),
      sampleCount: t({ en: 'Sample Count', ko: '샘플 수' }),
      regulation: t({ en: 'Regulation', ko: '규정' }),
      status: t({ en: 'Status', ko: '상태' }),
      actions: t({ en: 'Actions', ko: '작업' }),
    },

    // Risk Levels
    risk: {
      critical: t({ en: 'Critical', ko: '심각' }),
      high: t({ en: 'High', ko: '높음' }),
      medium: t({ en: 'Medium', ko: '중간' }),
      low: t({ en: 'Low', ko: '낮음' }),
    },

    // Empty States
    empty: {
      noScans: t({ en: 'No scans yet', ko: '스캔 기록 없음' }),
      noScansDesc: t({
        en: 'Run a PII scan to detect sensitive data in your sources',
        ko: '소스에서 민감한 데이터를 탐지하려면 PII 스캔을 실행하세요',
      }),
      noMasks: t({ en: 'No masking operations yet', ko: '마스킹 작업 없음' }),
      noMasksDesc: t({
        en: 'Apply masking to protect sensitive data',
        ko: '민감한 데이터 보호를 위해 마스킹을 적용하세요',
      }),
      noPIIFound: t({ en: 'No PII detected', ko: 'PII가 감지되지 않았습니다' }),
      noPIIFoundDesc: t({
        en: 'Great! No personally identifiable information was found',
        ko: '좋습니다! 개인 식별 정보가 발견되지 않았습니다',
      }),
    },

    // History
    history: {
      scanHistory: t({ en: 'Scan History', ko: '스캔 이력' }),
      maskHistory: t({ en: 'Masking History', ko: '마스킹 이력' }),
      ranAt: t({ en: 'Ran at', ko: '실행 시간' }),
      duration: t({ en: 'Duration', ko: '소요 시간' }),
      viewDetails: t({ en: 'View Details', ko: '상세 보기' }),
    },

    // Actions
    actions: {
      maskColumn: t({ en: 'Mask Column', ko: '컬럼 마스킹' }),
      ignoreColumn: t({ en: 'Ignore', ko: '무시' }),
      markSafe: t({ en: 'Mark as Safe', ko: '안전으로 표시' }),
      exportReport: t({ en: 'Export Report', ko: '보고서 내보내기' }),
    },

    // Messages
    messages: {
      selectSourceFirst: t({
        en: 'Please select a data source first',
        ko: '먼저 데이터 소스를 선택하세요',
      }),
      scanStarted: t({ en: 'Scan started', ko: '스캔이 시작되었습니다' }),
      maskingStarted: t({ en: 'Masking started', ko: '마스킹이 시작되었습니다' }),
    },
  },
} satisfies Dictionary

export default privacyContent
