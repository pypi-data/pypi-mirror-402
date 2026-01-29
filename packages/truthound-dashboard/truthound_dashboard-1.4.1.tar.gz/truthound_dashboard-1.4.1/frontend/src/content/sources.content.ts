/**
 * Data sources page translations.
 *
 * Contains translations for the data sources management page.
 */
import { t, type Dictionary } from 'intlayer'

const sourcesContent = {
  key: 'sources',
  content: {
    title: t({ en: 'Data Sources', ko: '데이터 소스',
  }),
    subtitle: t({
      en: 'Manage your data sources and validations',
      ko: '데이터 소스 및 검증 관리',
  }),

    // Actions
    addSource: t({ en: 'Add Source', ko: '소스 추가',
  }),
    addFirstSource: t({
      en: 'Add Your First Source',
      ko: '첫 번째 소스 추가하기',
  }),
    editSource: t({ en: 'Edit Source', ko: '소스 편집',
  }),
    deleteSource: t({ en: 'Delete Source', ko: '소스 삭제',
  }),

    // Empty states
    noSources: t({
      en: 'No data sources configured',
      ko: '설정된 데이터 소스가 없습니다',
  }),
    noSourcesYet: t({ en: 'No sources yet', ko: '소스가 없습니다',
  }),
    noSourcesDesc: t({
      en: 'Add your first data source to start monitoring data quality',
      ko: '데이터 품질 모니터링을 시작하려면 첫 번째 소스를 추가하세요',
  }),

    // Fields
    sourceName: t({ en: 'Source Name', ko: '소스 이름',
  }),
    sourceType: t({ en: 'Source Type', ko: '소스 유형',
  }),
    sourcePath: t({ en: 'Path / Connection', ko: '경로 / 연결',
  }),
    lastValidated: t({ en: 'Last validated', ko: '마지막 검증',
  }),
    never: t({ en: 'Never', ko: '없음',
  }),

    // Validation
    validate: t({ en: 'Validate', ko: '검증',
  }),
    loadError: t({ en: 'Failed to load sources', ko: '소스를 불러오지 못했습니다',
  }),
    deleteSuccess: t({
      en: 'Source deleted successfully',
      ko: '소스가 삭제되었습니다',
  }),
    deleteFailed: t({
      en: 'Failed to delete source',
      ko: '소스 삭제에 실패했습니다',
  }),
    validationStarted: t({ en: 'Validation Started', ko: '검증 시작',
  }),
    runningValidation: t({
      en: 'Running validation...',
      ko: '검증 실행 중...',
  }),
    validationPassed: t({ en: 'Validation Passed', ko: '검증 통과',
  }),
    validationFailed: t({ en: 'Validation Failed', ko: '검증 실패',
  }),
    validationError: t({
      en: 'Failed to run validation',
      ko: '검증 실행에 실패했습니다',
  }),

    // Confirmation
    confirmDelete: t({
      en: 'Are you sure you want to delete this source? This will also delete all related schemas, rules, and validations.',
      ko: '이 소스를 삭제하시겠습니까? 관련된 모든 스키마, 규칙, 검증 결과도 함께 삭제됩니다.',
  }),

    // Source types
    types: {
      file: t({ en: 'File', ko: '파일' }),
      csv: t({ en: 'CSV File', ko: 'CSV 파일' }),
      parquet: t({ en: 'Parquet File', ko: 'Parquet 파일' }),
      json: t({ en: 'JSON File', ko: 'JSON 파일' }),
      database: t({ en: 'Database', ko: '데이터베이스' }),
      postgresql: t({ en: 'PostgreSQL', ko: 'PostgreSQL' }),
      mysql: t({ en: 'MySQL', ko: 'MySQL' }),
      sqlite: t({ en: 'SQLite', ko: 'SQLite' }),
      oracle: t({ en: 'Oracle', ko: 'Oracle' }),
      sqlserver: t({ en: 'SQL Server', ko: 'SQL Server' }),
      snowflake: t({ en: 'Snowflake', ko: 'Snowflake' }),
      bigquery: t({ en: 'BigQuery', ko: 'BigQuery' }),
      redshift: t({ en: 'Amazon Redshift', ko: 'Amazon Redshift' }),
      databricks: t({ en: 'Databricks', ko: 'Databricks' }),
      spark: t({ en: 'Apache Spark', ko: 'Apache Spark' }),
    },

    // Source categories
    categories: {
      all: t({ en: 'All', ko: '전체' }),
      file: t({ en: 'Files', ko: '파일' }),
      database: t({ en: 'Databases', ko: '데이터베이스' }),
      warehouse: t({ en: 'Data Warehouses', ko: '데이터 웨어하우스' }),
      bigdata: t({ en: 'Big Data', ko: '빅데이터' }),
    },

    // Add source dialog
    dialog: {
      title: t({ en: 'Add Data Source', ko: '데이터 소스 추가' }),
      description: t({
        en: 'Connect to a new data source for validation and monitoring.',
        ko: '검증 및 모니터링을 위해 새로운 데이터 소스에 연결합니다.',
      }),
      selectType: t({ en: 'Select Type', ko: '유형 선택' }),
      configure: t({ en: 'Configure', ko: '구성' }),
      testCreate: t({ en: 'Test & Create', ko: '테스트 및 생성' }),
      sourceName: t({ en: 'Source Name', ko: '소스 이름' }),
      sourceNamePlaceholder: t({
        en: 'e.g., Production Database',
        ko: '예: 프로덕션 데이터베이스',
      }),
      sourceDescription: t({ en: 'Description', ko: '설명' }),
      sourceDescriptionPlaceholder: t({
        en: 'Optional description',
        ko: '선택적 설명',
      }),
      required: t({ en: 'Required', ko: '필수' }),
      optional: t({ en: 'Optional', ko: '선택' }),
      next: t({ en: 'Next', ko: '다음' }),
      back: t({ en: 'Back', ko: '이전' }),
      cancel: t({ en: 'Cancel', ko: '취소' }),
      createSource: t({ en: 'Create Source', ko: '소스 생성' }),
      creating: t({ en: 'Creating...', ko: '생성 중...' }),
      docs: t({ en: 'Docs', ko: '문서' }),
    },

    // Test connection
    testConnection: {
      title: t({ en: 'Test Connection', ko: '연결 테스트' }),
      description: t({
        en: 'Verify the connection before creating the source.',
        ko: '소스를 생성하기 전에 연결을 확인합니다.',
      }),
      test: t({ en: 'Test Connection', ko: '연결 테스트' }),
      testing: t({ en: 'Testing...', ko: '테스트 중...' }),
      success: t({ en: 'Connection successful!', ko: '연결 성공!' }),
      failed: t({ en: 'Connection failed', ko: '연결 실패' }),
    },

    // Connection summary
    summary: {
      title: t({ en: 'Connection Summary', ko: '연결 요약' }),
      name: t({ en: 'Name', ko: '이름' }),
      type: t({ en: 'Type', ko: '유형' }),
      description: t({ en: 'Description', ko: '설명' }),
    },

    // Success/Error messages
    createSuccess: t({
      en: 'Source created successfully',
      ko: '소스가 성공적으로 생성되었습니다',
    }),
    createFailed: t({
      en: 'Failed to create source',
      ko: '소스 생성에 실패했습니다',
    }),
    loadTypesError: t({
      en: 'Failed to load source types',
      ko: '소스 유형을 불러오지 못했습니다',
    }),
    validationErrorMsg: t({
      en: 'Please select a source type',
      ko: '소스 유형을 선택하세요',
    }),
    nameRequired: t({ en: 'Name is required', ko: '이름은 필수입니다' }),
    fieldRequired: t({ en: 'is required', ko: '필수 항목입니다' }),

    // Edit source dialog
    edit: {
      description: t({
        en: 'Edit source configuration and connection settings.',
        ko: '소스 구성 및 연결 설정을 편집합니다.',
      }),
      generalTab: t({ en: 'General', ko: '일반' }),
      connectionTab: t({ en: 'Connection', ko: '연결' }),
      sourceInfo: t({ en: 'Source Information', ko: '소스 정보' }),
      createdAt: t({ en: 'Created', ko: '생성일' }),
      sensitiveFieldsNotice: t({
        en: 'Sensitive fields are masked for security.',
        ko: '보안을 위해 민감한 필드는 마스킹됩니다.',
      }),
      sensitiveFieldsHint: t({
        en: 'Leave password fields empty to keep the existing value.',
        ko: '기존 값을 유지하려면 비밀번호 필드를 비워두세요.',
      }),
      testConnectionHint: t({
        en: 'Test the connection with current settings.',
        ko: '현재 설정으로 연결을 테스트합니다.',
      }),
      sensitiveFieldsModified: t({
        en: '{count} sensitive field(s) modified',
        ko: '{count}개의 민감한 필드가 수정됨',
      }),
      saving: t({ en: 'Saving...', ko: '저장 중...' }),
      updateSuccess: t({
        en: 'Source updated successfully',
        ko: '소스가 성공적으로 업데이트되었습니다',
      }),
      updateFailed: t({
        en: 'Failed to update source',
        ko: '소스 업데이트에 실패했습니다',
      }),
      unsupportedType: t({
        en: 'Unable to load configuration for this source type.',
        ko: '이 소스 유형의 구성을 불러올 수 없습니다.',
      }),
    },

    // Connection info display
    connectionInfo: {
      title: t({ en: 'Connection Details', ko: '연결 세부 정보' }),
      showValue: t({ en: 'Show', ko: '표시' }),
      hideValue: t({ en: 'Hide', ko: '숨기기' }),
      masked: t({ en: '(masked)', ko: '(마스킹됨)' }),
      notSet: t({ en: 'Not set', ko: '설정되지 않음' }),
    },
  },
} satisfies Dictionary

export default sourcesContent
