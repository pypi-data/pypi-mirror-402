/**
 * Maintenance component translations.
 *
 * Contains translations for maintenance settings and retention policy UI.
 */
import { t, type Dictionary } from 'intlayer'

const maintenanceContent = {
  key: 'maintenance',
  content: {
    // Page title
    title: t({ en: 'Maintenance', ko: '유지보수' }),
    subtitle: t({
      en: 'Configure retention policies and manage database maintenance',
      ko: '리텐션 정책 구성 및 데이터베이스 유지보수 관리',
    }),

    // Status card
    statusTitle: t({ en: 'Maintenance Status', ko: '유지보수 상태' }),
    statusDescription: t({
      en: 'Current status of automated maintenance tasks',
      ko: '자동 유지보수 작업의 현재 상태',
    }),
    autoMaintenance: t({ en: 'Auto Maintenance', ko: '자동 유지보수' }),
    lastRun: t({ en: 'Last Run', ko: '마지막 실행' }),
    nextRun: t({ en: 'Next Run', ko: '다음 실행' }),
    runCleanup: t({ en: 'Run Cleanup', ko: '정리 실행' }),
    runVacuum: t({ en: 'Run VACUUM', ko: 'VACUUM 실행' }),

    // Retention policy card
    retentionTitle: t({ en: 'Retention Policy', ko: '리텐션 정책' }),
    retentionDescription: t({
      en: 'Configure how long data is retained before automatic cleanup',
      ko: '자동 정리 전 데이터 보관 기간 설정',
    }),
    enableAutoMaintenance: t({ en: 'Enable Auto Maintenance', ko: '자동 유지보수 활성화' }),
    enableAutoMaintenanceDescription: t({
      en: 'Automatically run cleanup tasks daily at 3:00 AM',
      ko: '매일 오전 3시에 자동으로 정리 작업 실행',
    }),

    // Retention fields
    validationRetentionDays: t({
      en: 'Validation Retention (days)',
      ko: '검증 결과 보관 기간 (일)',
    }),
    validationRetentionDaysDescription: t({
      en: 'Number of days to keep validation results',
      ko: '검증 결과를 보관할 일수',
    }),
    profileKeepPerSource: t({
      en: 'Profiles per Source',
      ko: '소스당 프로파일 수',
    }),
    profileKeepPerSourceDescription: t({
      en: 'Number of profiles to keep per data source',
      ko: '데이터 소스당 보관할 프로파일 수',
    }),
    notificationLogRetentionDays: t({
      en: 'Notification Log Retention (days)',
      ko: '알림 로그 보관 기간 (일)',
    }),
    notificationLogRetentionDaysDescription: t({
      en: 'Number of days to keep notification logs',
      ko: '알림 로그를 보관할 일수',
    }),
    runVacuumOnCleanup: t({ en: 'Run VACUUM on Cleanup', ko: '정리 시 VACUUM 실행' }),
    runVacuumOnCleanupDescription: t({
      en: 'Reclaim disk space after cleanup',
      ko: '정리 후 디스크 공간 회수',
    }),

    // Cache card
    cacheTitle: t({ en: 'Cache Statistics', ko: '캐시 통계' }),
    cacheDescription: t({
      en: 'Monitor and manage application cache',
      ko: '애플리케이션 캐시 모니터링 및 관리',
    }),
    totalEntries: t({ en: 'Total Entries', ko: '총 항목' }),
    validEntries: t({ en: 'Valid', ko: '유효' }),
    expiredEntries: t({ en: 'Expired', ko: '만료됨' }),
    hitRate: t({ en: 'Hit Rate', ko: '적중률' }),
    clearCache: t({ en: 'Clear Cache', ko: '캐시 삭제' }),

    // Messages
    loadFailed: t({ en: 'Failed to load maintenance data', ko: '유지보수 데이터 로드 실패' }),
    configSaved: t({ en: 'Configuration saved successfully', ko: '설정이 저장되었습니다' }),
    saveFailed: t({ en: 'Failed to save configuration', ko: '설정 저장 실패' }),
    cleanupComplete: t({ en: 'Cleanup completed.', ko: '정리 완료.' }),
    recordsDeleted: t({ en: 'records deleted', ko: '개 레코드 삭제됨' }),
    cleanupFailed: t({ en: 'Failed to run cleanup', ko: '정리 실행 실패' }),
    vacuumComplete: t({ en: 'VACUUM completed successfully', ko: 'VACUUM이 성공적으로 완료됨' }),
    vacuumFailed: t({ en: 'Failed to run VACUUM', ko: 'VACUUM 실행 실패' }),
    cacheCleared: t({ en: 'Cache cleared successfully', ko: '캐시가 삭제되었습니다' }),
    cacheClearFailed: t({ en: 'Failed to clear cache', ko: '캐시 삭제 실패' }),
  },
} satisfies Dictionary

export default maintenanceContent
