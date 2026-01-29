/**
 * Schema Evolution translations
 *
 * This file contains translations for schema evolution tracking,
 * version history, and change detection features.
 */
import { t, type Dictionary } from 'intlayer'

const schemaEvolutionContent = {
  key: 'schemaEvolution',
  content: {
    // Page title and description
    title: t({ en: 'Schema Evolution', ko: '스키마 변경 이력' }),
    description: t({
      en: 'Track schema changes over time',
      ko: '시간에 따른 스키마 변경 추적',
    }),

    // Version history
    versionHistory: t({ en: 'Version History', ko: '버전 이력' }),
    currentVersion: t({ en: 'Current Version', ko: '현재 버전' }),
    totalVersions: t({ en: 'Total Versions', ko: '전체 버전' }),
    version: t({ en: 'Version', ko: '버전' }),
    columns: t({ en: 'columns', ko: '컬럼' }),

    // Changes
    totalChanges: t({ en: 'Total Changes', ko: '총 변경' }),
    breakingChanges: t({ en: 'Breaking Changes', ko: '호환성 손상 변경' }),
    changesInVersion: t({
      en: 'Changes in this version',
      ko: '이 버전의 변경 사항',
    }),
    noChangesDetected: t({
      en: 'No changes detected in this version.',
      ko: '이 버전에서 변경 사항이 감지되지 않았습니다.',
    }),

    // Change types
    columnAdded: t({ en: 'Added', ko: '추가됨' }),
    columnRemoved: t({ en: 'Removed', ko: '삭제됨' }),
    typeChanged: t({ en: 'Type Changed', ko: '타입 변경' }),

    // Severity
    breaking: t({ en: 'Breaking', ko: '호환성 손상' }),
    safe: t({ en: 'Safe', ko: '안전' }),
    nonBreaking: t({ en: 'Non-breaking', ko: '호환됨' }),

    // Actions
    detectChanges: t({ en: 'Detect Changes', ko: '변경 감지' }),
    detecting: t({ en: 'Detecting...', ko: '감지 중...' }),
    loadingHistory: t({
      en: 'Loading schema history...',
      ko: '스키마 이력 로딩 중...',
    }),

    // Empty state
    noVersionsFound: t({
      en: 'No schema versions found. Run schema learning to create the first version.',
      ko: '스키마 버전이 없습니다. 스키마 학습을 실행하여 첫 버전을 생성하세요.',
    }),

    // Timestamps
    lastChange: t({ en: 'Last change', ko: '마지막 변경' }),
    detectedAt: t({ en: 'Detected at', ko: '감지 시각' }),

    // Type labels
    type: t({ en: 'Type', ko: '타입' }),
    was: t({ en: 'Was', ko: '이전' }),

    // Badges
    current: t({ en: 'Current', ko: '현재' }),
    latest: t({ en: 'Latest', ko: '최신' }),

    // Additional fields
    columnName: t({ en: 'Column', ko: '컬럼' }),
    oldValue: t({ en: 'Old Value', ko: '이전 값' }),
    newValue: t({ en: 'New Value', ko: '새 값' }),
    compatibility: t({ en: 'Compatibility', ko: '호환성' }),
    compatible: t({ en: 'Compatible', ko: '호환됨' }),
    incompatible: t({ en: 'Incompatible', ko: '호환되지 않음' }),
    reason: t({ en: 'Reason', ko: '사유' }),
    warning: t({ en: 'Warning', ko: '경고' }),
    nullableChanged: t({ en: 'Nullable Changed', ko: 'Nullable 변경' }),
    constraintChanged: t({ en: 'Constraint Changed', ko: '제약조건 변경' }),
    columnRenamed: t({ en: 'Renamed', ko: '이름 변경' }),
    compareVersions: t({ en: 'Compare Versions', ko: '버전 비교' }),
    schemaHash: t({ en: 'Schema Hash', ko: '스키마 해시' }),
    selectSource: t({ en: 'Select a source...', ko: '소스 선택...' }),
    selectVersion: t({ en: 'Select version...', ko: '버전 선택...' }),
    refresh: t({ en: 'Refresh', ko: '새로고침' }),
    viewDiff: t({ en: 'View Diff', ko: '변경 비교' }),
    summary: t({ en: 'Summary', ko: '요약' }),
    noSources: t({ en: 'No data sources available', ko: '데이터 소스가 없습니다' }),
    fetchError: t({ en: 'Failed to fetch schema evolution data', ko: '스키마 변경 데이터 가져오기 실패' }),
    timeSinceCreation: t({ en: 'Time since creation', ko: '생성 이후 시간' }),
  },
} satisfies Dictionary

export default schemaEvolutionContent
