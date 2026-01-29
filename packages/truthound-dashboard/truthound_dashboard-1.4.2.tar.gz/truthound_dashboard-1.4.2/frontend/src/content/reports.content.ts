/**
 * Reports component translations.
 *
 * Contains translations for report download functionality including
 * language selection for 15-language i18n support and report history.
 */
import { t, type Dictionary } from 'intlayer'

const reportsContent = {
  key: 'reports',
  content: {
    // Page header
    pageTitle: t({ en: 'Reports', ko: '리포트' }),
    pageDescription: t({
      en: 'View and manage generated validation reports',
      ko: '생성된 검증 리포트 조회 및 관리',
    }),

    // Download button
    downloadReport: t({ en: 'Download Report', ko: '리포트 다운로드' }),
    selectFormat: t({ en: 'Select Format', ko: '형식 선택' }),
    selectTheme: t({ en: 'Select Theme', ko: '테마 선택' }),
    selectLanguage: t({ en: 'Report Language', ko: '리포트 언어' }),

    // Formats
    formatHtml: t({ en: 'HTML', ko: 'HTML' }),
    formatCsv: t({ en: 'CSV', ko: 'CSV' }),
    formatJson: t({ en: 'JSON', ko: 'JSON' }),
    formatMarkdown: t({ en: 'Markdown', ko: 'Markdown' }),
    formatPdf: t({ en: 'PDF', ko: 'PDF' }),
    formatJunit: t({ en: 'JUnit XML (CI/CD)', ko: 'JUnit XML (CI/CD)' }),
    formatExcel: t({ en: 'Excel', ko: 'Excel' }),

    // Themes
    themeLight: t({ en: 'Light', ko: '라이트' }),
    themeDark: t({ en: 'Dark', ko: '다크' }),
    themeProfessional: t({ en: 'Professional', ko: '프로페셔널' }),
    themeMinimal: t({ en: 'Minimal', ko: '미니멀' }),
    themeHighContrast: t({ en: 'High Contrast', ko: '고대비' }),

    // Languages (15 supported languages per truthound docs)
    languageEnglish: t({ en: 'English', ko: '영어' }),
    languageKorean: t({ en: 'Korean', ko: '한국어' }),
    languageJapanese: t({ en: 'Japanese', ko: '일본어' }),
    languageChinese: t({ en: 'Chinese', ko: '중국어' }),
    languageGerman: t({ en: 'German', ko: '독일어' }),
    languageFrench: t({ en: 'French', ko: '프랑스어' }),
    languageSpanish: t({ en: 'Spanish', ko: '스페인어' }),
    languagePortuguese: t({ en: 'Portuguese', ko: '포르투갈어' }),
    languageItalian: t({ en: 'Italian', ko: '이탈리아어' }),
    languageRussian: t({ en: 'Russian', ko: '러시아어' }),
    languageArabic: t({ en: 'Arabic', ko: '아랍어' }),
    languageThai: t({ en: 'Thai', ko: '태국어' }),
    languageVietnamese: t({ en: 'Vietnamese', ko: '베트남어' }),
    languageIndonesian: t({ en: 'Indonesian', ko: '인도네시아어' }),
    languageTurkish: t({ en: 'Turkish', ko: '터키어' }),

    // Messages
    downloadSuccess: t({ en: 'Download Started', ko: '다운로드 시작됨' }),
    reportDownloaded: t({ en: 'report downloaded', ko: '리포트 다운로드됨' }),
    downloadFailed: t({ en: 'Failed to download report', ko: '리포트 다운로드 실패' }),

    // Preview
    previewReport: t({ en: 'Preview Report', ko: '리포트 미리보기' }),

    // Custom Reporters
    customReporters: t({ en: 'Custom Reporters', ko: '커스텀 리포터' }),
    noConfigRequired: t({ en: 'No configuration required.', ko: '설정이 필요하지 않습니다.' }),
    generateReport: t({ en: 'Generate Report', ko: '리포트 생성' }),
    generating: t({ en: 'Generating...', ko: '생성 중...' }),
    customReportDownloaded: t({ en: 'Custom report downloaded', ko: '커스텀 리포트 다운로드됨' }),
    configureReporter: t({ en: 'Configure and generate custom report', ko: '커스텀 리포트 설정 및 생성' }),
    clickToGenerate: t({ en: 'Click generate to create the report', ko: '생성 버튼을 클릭하여 리포트 생성' }),

    // Language selection
    languageSelectionHint: t({
      en: 'Select the language for report content (15 languages supported)',
      ko: '리포트 콘텐츠 언어 선택 (15개 언어 지원)',
    }),
    defaultLanguage: t({ en: 'Default (English)', ko: '기본값 (영어)' }),

    // Report History
    reportHistory: t({ en: 'Report History', ko: '리포트 이력' }),
    historyDescription: t({
      en: 'Browse and download previously generated reports',
      ko: '이전에 생성된 리포트 조회 및 다운로드',
    }),
    noReports: t({ en: 'No reports found', ko: '리포트가 없습니다' }),
    noReportsDescription: t({
      en: 'Generate a report from a validation result to see it here',
      ko: '검증 결과에서 리포트를 생성하면 여기에 표시됩니다',
    }),

    // Statistics
    statistics: t({ en: 'Statistics', ko: '통계' }),
    totalReports: t({ en: 'Total Reports', ko: '총 리포트' }),
    totalSize: t({ en: 'Total Size', ko: '총 용량' }),
    totalDownloads: t({ en: 'Total Downloads', ko: '총 다운로드' }),
    avgGenerationTime: t({ en: 'Avg. Generation Time', ko: '평균 생성 시간' }),
    expiredReports: t({ en: 'Expired Reports', ko: '만료된 리포트' }),
    reportersUsed: t({ en: 'Reporters Used', ko: '사용된 리포터' }),

    // Report Status
    statusPending: t({ en: 'Pending', ko: '대기 중' }),
    statusGenerating: t({ en: 'Generating', ko: '생성 중' }),
    statusCompleted: t({ en: 'Completed', ko: '완료' }),
    statusFailed: t({ en: 'Failed', ko: '실패' }),
    statusExpired: t({ en: 'Expired', ko: '만료' }),

    // Filters
    filterByFormat: t({ en: 'Filter by Format', ko: '형식별 필터' }),
    filterByStatus: t({ en: 'Filter by Status', ko: '상태별 필터' }),
    filterBySource: t({ en: 'Filter by Source', ko: '소스별 필터' }),
    includeExpired: t({ en: 'Include Expired', ko: '만료된 항목 포함' }),
    searchPlaceholder: t({ en: 'Search reports...', ko: '리포트 검색...' }),
    allFormats: t({ en: 'All Formats', ko: '모든 형식' }),
    allStatuses: t({ en: 'All Statuses', ko: '모든 상태' }),
    allSources: t({ en: 'All Sources', ko: '모든 소스' }),

    // Actions
    download: t({ en: 'Download', ko: '다운로드' }),
    delete: t({ en: 'Delete', ko: '삭제' }),
    regenerate: t({ en: 'Regenerate', ko: '재생성' }),
    viewDetails: t({ en: 'View Details', ko: '상세 보기' }),
    bulkGenerate: t({ en: 'Bulk Generate', ko: '일괄 생성' }),
    cleanupExpired: t({ en: 'Cleanup Expired', ko: '만료 정리' }),
    manageReporters: t({ en: 'Manage Reporters', ko: '리포터 관리' }),

    // Report Details
    reportName: t({ en: 'Report Name', ko: '리포트 이름' }),
    format: t({ en: 'Format', ko: '형식' }),
    status: t({ en: 'Status', ko: '상태' }),
    source: t({ en: 'Source', ko: '소스' }),
    validation: t({ en: 'Validation', ko: '검증' }),
    reporter: t({ en: 'Reporter', ko: '리포터' }),
    theme: t({ en: 'Theme', ko: '테마' }),
    locale: t({ en: 'Language', ko: '언어' }),
    fileSize: t({ en: 'File Size', ko: '파일 크기' }),
    generationTime: t({ en: 'Generation Time', ko: '생성 시간' }),
    downloadCount: t({ en: 'Download Count', ko: '다운로드 횟수' }),
    createdAt: t({ en: 'Created At', ko: '생성일' }),
    expiresAt: t({ en: 'Expires At', ko: '만료일' }),
    errorMessage: t({ en: 'Error Message', ko: '오류 메시지' }),
    neverExpires: t({ en: 'Never Expires', ko: '만료 없음' }),
    noSource: t({ en: 'No Source', ko: '소스 없음' }),
    noReporter: t({ en: 'Standard Reporter', ko: '기본 리포터' }),

    // Bulk Actions
    bulkGenerateTitle: t({ en: 'Bulk Generate Reports', ko: '리포트 일괄 생성' }),
    bulkGenerateDescription: t({
      en: 'Generate reports for multiple validations at once',
      ko: '여러 검증에 대한 리포트를 한 번에 생성',
    }),
    selectValidations: t({ en: 'Select Validations', ko: '검증 선택' }),
    selectedCount: t({ en: 'selected', ko: '개 선택됨' }),
    generateSelected: t({ en: 'Generate Selected', ko: '선택 항목 생성' }),
    bulkSuccess: t({ en: 'Bulk generation completed', ko: '일괄 생성 완료' }),
    bulkPartialSuccess: t({
      en: 'Bulk generation partially completed',
      ko: '일괄 생성 부분 완료',
    }),

    // Cleanup
    cleanupTitle: t({ en: 'Cleanup Expired Reports', ko: '만료된 리포트 정리' }),
    cleanupDescription: t({
      en: 'Delete all expired reports to free up storage',
      ko: '저장 공간 확보를 위해 만료된 모든 리포트 삭제',
    }),
    cleanupConfirm: t({
      en: 'Are you sure you want to delete all expired reports?',
      ko: '만료된 모든 리포트를 삭제하시겠습니까?',
    }),
    cleanupSuccess: t({ en: 'reports deleted', ko: '개 리포트 삭제됨' }),

    // Delete Confirmation
    deleteConfirmTitle: t({ en: 'Delete Report', ko: '리포트 삭제' }),
    deleteConfirmMessage: t({
      en: 'Are you sure you want to delete this report? This action cannot be undone.',
      ko: '이 리포트를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.',
    }),
    deleteSuccess: t({ en: 'Report deleted successfully', ko: '리포트가 삭제되었습니다' }),
  },
} satisfies Dictionary

export default reportsContent
