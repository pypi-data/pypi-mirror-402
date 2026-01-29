import { t, type Dictionary } from 'intlayer'

const versioningContent = {
  key: 'versioning',
  content: {
    // Page titles
    title: t({
      en: 'Version History',
      ko: '버전 히스토리',
    }),
    subtitle: t({
      en: 'Track validation result changes over time',
      ko: '시간에 따른 검증 결과 변경 추적',
    }),

    // Version list
    versionList: t({
      en: 'Version List',
      ko: '버전 목록',
    }),
    noVersions: t({
      en: 'No versions available yet. Run a validation to create the first version.',
      ko: '아직 버전이 없습니다. 검증을 실행하여 첫 번째 버전을 생성하세요.',
    }),
    latestVersion: t({
      en: 'Latest Version',
      ko: '최신 버전',
    }),
    version: t({
      en: 'Version',
      ko: '버전',
    }),
    validationId: t({
      en: 'Validation ID',
      ko: '검증 ID',
    }),

    // Version info
    versionNumber: t({
      en: 'Version Number',
      ko: '버전 번호',
    }),
    strategy: t({
      en: 'Strategy',
      ko: '전략',
    }),
    createdAt: t({
      en: 'Created At',
      ko: '생성 시간',
    }),
    parentVersion: t({
      en: 'Parent Version',
      ko: '상위 버전',
    }),
    contentHash: t({
      en: 'Content Hash',
      ko: '콘텐츠 해시',
    }),
    noParent: t({
      en: 'No parent (initial version)',
      ko: '상위 버전 없음 (초기 버전)',
    }),

    // Version strategies
    strategies: {
      incremental: t({
        en: 'Incremental',
        ko: '증분',
      }),
      semantic: t({
        en: 'Semantic',
        ko: '시맨틱',
      }),
      timestamp: t({
        en: 'Timestamp',
        ko: '타임스탬프',
      }),
      gitlike: t({
        en: 'Git-like',
        ko: 'Git 스타일',
      }),
    },

    // Version comparison
    compare: t({
      en: 'Compare',
      ko: '비교',
    }),
    compareVersions: t({
      en: 'Compare Versions',
      ko: '버전 비교',
    }),
    selectVersions: t({
      en: 'Select two versions to compare',
      ko: '비교할 두 버전을 선택하세요',
    }),
    fromVersion: t({
      en: 'From Version',
      ko: '이전 버전',
    }),
    toVersion: t({
      en: 'To Version',
      ko: '최신 버전',
    }),
    noChanges: t({
      en: 'No changes between versions',
      ko: '버전 간 변경 사항이 없습니다',
    }),
    hasChanges: t({
      en: 'Changes detected',
      ko: '변경 사항 감지됨',
    }),

    // Diff details
    issuesAdded: t({
      en: 'Issues Added',
      ko: '추가된 이슈',
    }),
    issuesRemoved: t({
      en: 'Issues Removed',
      ko: '제거된 이슈',
    }),
    issuesChanged: t({
      en: 'Issues Changed',
      ko: '변경된 이슈',
    }),
    changeSummary: t({
      en: 'Change Summary',
      ko: '변경 요약',
    }),
    addedCount: t({
      en: 'Added',
      ko: '추가됨',
    }),
    removedCount: t({
      en: 'Removed',
      ko: '제거됨',
    }),
    changedCount: t({
      en: 'Changed',
      ko: '변경됨',
    }),

    // Version history
    viewHistory: t({
      en: 'View History',
      ko: '히스토리 보기',
    }),
    historyChain: t({
      en: 'Version History Chain',
      ko: '버전 히스토리 체인',
    }),
    showHistory: t({
      en: 'Show Version History',
      ko: '버전 히스토리 표시',
    }),
    hideHistory: t({
      en: 'Hide Version History',
      ko: '버전 히스토리 숨기기',
    }),

    // Actions
    createVersion: t({
      en: 'Create Version',
      ko: '버전 생성',
    }),
    viewDetails: t({
      en: 'View Details',
      ko: '상세 보기',
    }),
    backToSource: t({
      en: 'Back to Source',
      ko: '소스로 돌아가기',
    }),

    // Messages
    versionCreated: t({
      en: 'Version created successfully',
      ko: '버전이 성공적으로 생성되었습니다',
    }),
    loadError: t({
      en: 'Failed to load versions',
      ko: '버전 로드 실패',
    }),
    compareError: t({
      en: 'Failed to compare versions',
      ko: '버전 비교 실패',
    }),

    // Timeline
    timeline: t({
      en: 'Timeline',
      ko: '타임라인',
    }),
    current: t({
      en: 'Current',
      ko: '현재',
    }),
    initial: t({
      en: 'Initial',
      ko: '초기',
    }),
  },
} satisfies Dictionary

export default versioningContent
