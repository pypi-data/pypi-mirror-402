import { t, type Dictionary } from "intlayer";

const pluginsContent = {
  key: "plugins",
  content: {
    // Page titles
    title: t({ en: "Plugin Marketplace", ko: "플러그인 마켓플레이스" }),
    description: t({
      en: "Discover and install plugins to extend dashboard functionality",
      ko: "대시보드 기능을 확장하는 플러그인을 찾아 설치하세요",
    }),

    // Navigation tabs
    tabs: {
      marketplace: t({ en: "Marketplace", ko: "마켓플레이스" }),
      installed: t({ en: "Installed", ko: "설치됨" }),
      validators: t({ en: "Custom Validators", ko: "커스텀 검증기" }),
      reporters: t({ en: "Custom Reporters", ko: "커스텀 리포터" }),
      settings: t({ en: "Settings", ko: "설정" }),
    },

    // Plugin types
    types: {
      validator: t({ en: "Validator", ko: "검증기" }),
      reporter: t({ en: "Reporter", ko: "리포터" }),
      connector: t({ en: "Connector", ko: "커넥터" }),
      transformer: t({ en: "Transformer", ko: "변환기" }),
    },

    // Plugin status
    status: {
      available: t({ en: "Available", ko: "사용 가능" }),
      installed: t({ en: "Installed", ko: "설치됨" }),
      enabled: t({ en: "Enabled", ko: "활성화됨" }),
      disabled: t({ en: "Disabled", ko: "비활성화됨" }),
      updateAvailable: t({ en: "Update Available", ko: "업데이트 가능" }),
      error: t({ en: "Error", ko: "오류" }),
    },

    // Security levels
    security: {
      trusted: t({ en: "Trusted", ko: "신뢰됨" }),
      verified: t({ en: "Verified", ko: "검증됨" }),
      unverified: t({ en: "Unverified", ko: "미검증" }),
      sandboxed: t({ en: "Sandboxed", ko: "샌드박스" }),
    },

    // Plugin sources
    sources: {
      official: t({ en: "Official", ko: "공식" }),
      community: t({ en: "Community", ko: "커뮤니티" }),
      local: t({ en: "Local", ko: "로컬" }),
      private: t({ en: "Private", ko: "비공개" }),
    },

    // Actions
    actions: {
      install: t({ en: "Install", ko: "설치" }),
      uninstall: t({ en: "Uninstall", ko: "제거" }),
      enable: t({ en: "Enable", ko: "활성화" }),
      disable: t({ en: "Disable", ko: "비활성화" }),
      update: t({ en: "Update", ko: "업데이트" }),
      configure: t({ en: "Configure", ko: "설정" }),
      test: t({ en: "Test", ko: "테스트" }),
      preview: t({ en: "Preview", ko: "미리보기" }),
      create: t({ en: "Create", ko: "생성" }),
      edit: t({ en: "Edit", ko: "수정" }),
      delete: t({ en: "Delete", ko: "삭제" }),
      save: t({ en: "Save", ko: "저장" }),
      cancel: t({ en: "Cancel", ko: "취소" }),
      generate: t({ en: "Generate Report", ko: "리포트 생성" }),
      viewDetails: t({ en: "View Details", ko: "상세 보기" }),
    },

    // Search and filters
    search: {
      placeholder: t({ en: "Search plugins...", ko: "플러그인 검색..." }),
      filterByType: t({ en: "Filter by Type", ko: "타입별 필터" }),
      filterByStatus: t({ en: "Filter by Status", ko: "상태별 필터" }),
      filterByCategory: t({ en: "Filter by Category", ko: "카테고리별 필터" }),
      sortBy: t({ en: "Sort by", ko: "정렬" }),
      relevance: t({ en: "Relevance", ko: "관련성" }),
      rating: t({ en: "Rating", ko: "평점" }),
      installs: t({ en: "Installs", ko: "설치 수" }),
      updated: t({ en: "Recently Updated", ko: "최근 업데이트" }),
      name: t({ en: "Name", ko: "이름" }),
    },

    // Plugin card
    card: {
      by: t({ en: "by", ko: "제작" }),
      version: t({ en: "Version", ko: "버전" }),
      installs: t({ en: "installs", ko: "설치" }),
      rating: t({ en: "rating", ko: "평점" }),
      lastUpdated: t({ en: "Last updated", ko: "마지막 업데이트" }),
      permissions: t({ en: "Permissions", ko: "권한" }),
      dependencies: t({ en: "Dependencies", ko: "의존성" }),
    },

    // Plugin details
    details: {
      overview: t({ en: "Overview", ko: "개요" }),
      readme: t({ en: "README", ko: "README" }),
      changelog: t({ en: "Changelog", ko: "변경 로그" }),
      reviews: t({ en: "Reviews", ko: "리뷰" }),
      author: t({ en: "Author", ko: "작성자" }),
      license: t({ en: "License", ko: "라이선스" }),
      homepage: t({ en: "Homepage", ko: "홈페이지" }),
      repository: t({ en: "Repository", ko: "저장소" }),
      keywords: t({ en: "Keywords", ko: "키워드" }),
      categories: t({ en: "Categories", ko: "카테고리" }),
    },

    // Custom validator
    validator: {
      title: t({ en: "Custom Validators", ko: "커스텀 검증기" }),
      description: t({
        en: "Create and manage custom validation rules",
        ko: "커스텀 검증 규칙을 생성하고 관리합니다",
      }),
      createNew: t({ en: "Create Validator", ko: "검증기 생성" }),
      name: t({ en: "Validator Name", ko: "검증기 이름" }),
      displayName: t({ en: "Display Name", ko: "표시 이름" }),
      category: t({ en: "Category", ko: "카테고리" }),
      severity: t({ en: "Severity", ko: "심각도" }),
      tags: t({ en: "Tags", ko: "태그" }),
      parameters: t({ en: "Parameters", ko: "파라미터" }),
      code: t({ en: "Validator Code", ko: "검증기 코드" }),
      testCases: t({ en: "Test Cases", ko: "테스트 케이스" }),
      testData: t({ en: "Test Data", ko: "테스트 데이터" }),
      testResult: t({ en: "Test Result", ko: "테스트 결과" }),
      passed: t({ en: "Passed", ko: "통과" }),
      failed: t({ en: "Failed", ko: "실패" }),
      usageCount: t({ en: "Usage Count", ko: "사용 횟수" }),
      lastUsed: t({ en: "Last Used", ko: "마지막 사용" }),
      verified: t({ en: "Verified", ko: "검증됨" }),
      unverified: t({ en: "Not Verified", ko: "미검증" }),
    },

    // Custom reporter
    reporter: {
      title: t({ en: "Custom Reporters", ko: "커스텀 리포터" }),
      description: t({
        en: "Create and manage custom report templates",
        ko: "커스텀 리포트 템플릿을 생성하고 관리합니다",
      }),
      createNew: t({ en: "Create Reporter", ko: "리포터 생성" }),
      name: t({ en: "Reporter Name", ko: "리포터 이름" }),
      displayName: t({ en: "Display Name", ko: "표시 이름" }),
      outputFormats: t({ en: "Output Formats", ko: "출력 포맷" }),
      configFields: t({ en: "Configuration Fields", ko: "설정 필드" }),
      template: t({ en: "Jinja2 Template", ko: "Jinja2 템플릿" }),
      code: t({ en: "Reporter Code", ko: "리포터 코드" }),
      preview: t({ en: "Preview", ko: "미리보기" }),
      usageCount: t({ en: "Usage Count", ko: "사용 횟수" }),
    },

    // Parameter types
    paramTypes: {
      string: t({ en: "Text", ko: "텍스트" }),
      integer: t({ en: "Integer", ko: "정수" }),
      float: t({ en: "Decimal", ko: "소수" }),
      boolean: t({ en: "Boolean", ko: "불리언" }),
      column: t({ en: "Column", ko: "컬럼" }),
      columnList: t({ en: "Column List", ko: "컬럼 목록" }),
      select: t({ en: "Select", ko: "선택" }),
      multiSelect: t({ en: "Multi-Select", ko: "다중 선택" }),
      regex: t({ en: "Regex Pattern", ko: "정규표현식 패턴" }),
      json: t({ en: "JSON", ko: "JSON" }),
    },

    // Output formats
    outputFormats: {
      pdf: t({ en: "PDF", ko: "PDF" }),
      html: t({ en: "HTML", ko: "HTML" }),
      json: t({ en: "JSON", ko: "JSON" }),
      csv: t({ en: "CSV", ko: "CSV" }),
      excel: t({ en: "Excel", ko: "Excel" }),
      markdown: t({ en: "Markdown", ko: "Markdown" }),
    },

    // Messages
    messages: {
      installSuccess: t({
        en: "Plugin installed successfully",
        ko: "플러그인이 성공적으로 설치되었습니다",
      }),
      installFailed: t({
        en: "Failed to install plugin",
        ko: "플러그인 설치에 실패했습니다",
      }),
      uninstallSuccess: t({
        en: "Plugin uninstalled successfully",
        ko: "플러그인이 성공적으로 제거되었습니다",
      }),
      uninstallFailed: t({
        en: "Failed to uninstall plugin",
        ko: "플러그인 제거에 실패했습니다",
      }),
      enableSuccess: t({
        en: "Plugin enabled successfully",
        ko: "플러그인이 성공적으로 활성화되었습니다",
      }),
      disableSuccess: t({
        en: "Plugin disabled successfully",
        ko: "플러그인이 성공적으로 비활성화되었습니다",
      }),
      createSuccess: t({
        en: "Created successfully",
        ko: "성공적으로 생성되었습니다",
      }),
      updateSuccess: t({
        en: "Updated successfully",
        ko: "성공적으로 업데이트되었습니다",
      }),
      deleteSuccess: t({
        en: "Deleted successfully",
        ko: "성공적으로 삭제되었습니다",
      }),
      testSuccess: t({
        en: "Test completed successfully",
        ko: "테스트가 성공적으로 완료되었습니다",
      }),
      testFailed: t({
        en: "Test failed",
        ko: "테스트에 실패했습니다",
      }),
      codeValidationError: t({
        en: "Code validation failed",
        ko: "코드 검증에 실패했습니다",
      }),
      confirmDelete: t({
        en: "Are you sure you want to delete this?",
        ko: "정말 삭제하시겠습니까?",
      }),
      confirmUninstall: t({
        en: "Are you sure you want to uninstall this plugin?",
        ko: "정말 이 플러그인을 제거하시겠습니까?",
      }),
      noPlugins: t({
        en: "No plugins found",
        ko: "플러그인을 찾을 수 없습니다",
      }),
      noValidators: t({
        en: "No custom validators found",
        ko: "커스텀 검증기를 찾을 수 없습니다",
      }),
      noReporters: t({
        en: "No custom reporters found",
        ko: "커스텀 리포터를 찾을 수 없습니다",
      }),
      validatorCreated: t({
        en: "Validator created successfully",
        ko: "검증기가 성공적으로 생성되었습니다",
      }),
      validatorUpdated: t({
        en: "Validator updated successfully",
        ko: "검증기가 성공적으로 업데이트되었습니다",
      }),
      validatorDeleted: t({
        en: "Validator deleted successfully",
        ko: "검증기가 성공적으로 삭제되었습니다",
      }),
      validatorCreateFailed: t({
        en: "Failed to create validator",
        ko: "검증기 생성에 실패했습니다",
      }),
      validatorUpdateFailed: t({
        en: "Failed to update validator",
        ko: "검증기 업데이트에 실패했습니다",
      }),
      validatorDeleteFailed: t({
        en: "Failed to delete validator",
        ko: "검증기 삭제에 실패했습니다",
      }),
      reporterCreated: t({
        en: "Reporter created successfully",
        ko: "리포터가 성공적으로 생성되었습니다",
      }),
      reporterUpdated: t({
        en: "Reporter updated successfully",
        ko: "리포터가 성공적으로 업데이트되었습니다",
      }),
      reporterDeleted: t({
        en: "Reporter deleted successfully",
        ko: "리포터가 성공적으로 삭제되었습니다",
      }),
      reporterCreateFailed: t({
        en: "Failed to create reporter",
        ko: "리포터 생성에 실패했습니다",
      }),
      reporterUpdateFailed: t({
        en: "Failed to update reporter",
        ko: "리포터 업데이트에 실패했습니다",
      }),
      reporterDeleteFailed: t({
        en: "Failed to delete reporter",
        ko: "리포터 삭제에 실패했습니다",
      }),
      viewDetails: t({
        en: "View Details",
        ko: "상세보기",
      }),
    },

    // Statistics
    stats: {
      totalPlugins: t({ en: "Total Plugins", ko: "전체 플러그인" }),
      totalValidators: t({ en: "Total Validators", ko: "전체 검증기" }),
      totalReporters: t({ en: "Total Reporters", ko: "전체 리포터" }),
      installedPlugins: t({ en: "Installed", ko: "설치됨" }),
      enabledPlugins: t({ en: "Enabled", ko: "활성화됨" }),
    },

    // Security warnings
    securityWarnings: {
      unverifiedPlugin: t({
        en: "This plugin is not verified. Install at your own risk.",
        ko: "이 플러그인은 검증되지 않았습니다. 설치 시 주의하세요.",
      }),
      unverifiedDescription: t({
        en: "Unverified plugins have not been reviewed by the security team. They may contain bugs or vulnerabilities.",
        ko: "미검증 플러그인은 보안 팀의 검토를 거치지 않았습니다. 버그나 취약점이 포함되어 있을 수 있습니다.",
      }),
      sandboxedExecution: t({
        en: "This plugin will run in a sandboxed environment.",
        ko: "이 플러그인은 샌드박스 환경에서 실행됩니다.",
      }),
      permissionsRequired: t({
        en: "This plugin requires the following permissions:",
        ko: "이 플러그인은 다음 권한이 필요합니다:",
      }),
    },

    // Permissions
    permissions: {
      readData: t({ en: "Read Data", ko: "데이터 읽기" }),
      writeData: t({ en: "Write Data", ko: "데이터 쓰기" }),
      networkAccess: t({ en: "Network Access", ko: "네트워크 접근" }),
      fileSystem: t({ en: "File System Access", ko: "파일 시스템 접근" }),
      executeCode: t({ en: "Execute Code", ko: "코드 실행" }),
      sendNotifications: t({ en: "Send Notifications", ko: "알림 전송" }),
      accessSecrets: t({ en: "Access Secrets", ko: "시크릿 접근" }),
    },

    // Editor
    editor: {
      basicInfo: t({ en: "Basic Information", ko: "기본 정보" }),
      codeEditor: t({ en: "Code Editor", ko: "코드 에디터" }),
      parametersEditor: t({ en: "Parameters", ko: "파라미터" }),
      testPanel: t({ en: "Test Panel", ko: "테스트 패널" }),
      addParameter: t({ en: "Add Parameter", ko: "파라미터 추가" }),
      removeParameter: t({ en: "Remove", ko: "제거" }),
      paramName: t({ en: "Parameter Name", ko: "파라미터 이름" }),
      paramType: t({ en: "Type", ko: "타입" }),
      paramDescription: t({ en: "Description", ko: "설명" }),
      paramRequired: t({ en: "Required", ko: "필수" }),
      paramDefault: t({ en: "Default Value", ko: "기본값" }),
      loadTemplate: t({ en: "Load Template", ko: "템플릿 불러오기" }),
      runTest: t({ en: "Run Test", ko: "테스트 실행" }),
      clearOutput: t({ en: "Clear Output", ko: "출력 지우기" }),

      // Validator Editor
      createValidator: t({ en: "Create Validator", ko: "검증기 생성" }),
      editValidator: t({ en: "Edit Validator", ko: "검증기 수정" }),
      createValidatorDescription: t({
        en: "Create a new custom validator with Python code",
        ko: "Python 코드로 새 커스텀 검증기를 생성합니다",
      }),
      editValidatorDescription: t({
        en: "Edit the custom validator code and settings",
        ko: "커스텀 검증기 코드와 설정을 수정합니다",
      }),
      codeTab: t({ en: "Code", ko: "코드" }),
      settingsTab: t({ en: "Settings", ko: "설정" }),
      testTab: t({ en: "Test", ko: "테스트" }),
      validatorCode: t({ en: "Validator Code (Python)", ko: "검증기 코드 (Python)" }),
      codePlaceholder: t({ en: "Enter your validator code here...", ko: "검증기 코드를 입력하세요..." }),
      parameters: t({ en: "Parameters", ko: "파라미터" }),
      noParameters: t({ en: "No parameters defined. Click 'Add Parameter' to define custom parameters.", ko: "정의된 파라미터가 없습니다. '파라미터 추가'를 클릭하여 커스텀 파라미터를 정의하세요." }),
      displayName: t({ en: "Display Name", ko: "표시 이름" }),
      name: t({ en: "Name (identifier)", ko: "이름 (식별자)" }),
      nameHint: t({ en: "Lowercase with underscores, e.g., my_validator", ko: "소문자와 언더스코어 사용, 예: my_validator" }),
      description: t({ en: "Description", ko: "설명" }),
      descriptionPlaceholder: t({ en: "Describe what this validator does...", ko: "이 검증기가 하는 일을 설명하세요..." }),
      category: t({ en: "Category", ko: "카테고리" }),
      severity: t({ en: "Severity", ko: "심각도" }),
      tags: t({ en: "Tags", ko: "태그" }),
      tagPlaceholder: t({ en: "Add a tag and press Enter", ko: "태그를 입력하고 Enter를 누르세요" }),
      addTag: t({ en: "Add Tag", ko: "태그 추가" }),
      enabled: t({ en: "Enabled", ko: "활성화" }),

      // Test Panel
      testParams: t({ en: "Parameter Values", ko: "파라미터 값" }),
      testData: t({ en: "Test Data (JSON)", ko: "테스트 데이터 (JSON)" }),
      testDataPlaceholder: t({ en: "Enter test data in JSON format...", ko: "JSON 형식으로 테스트 데이터를 입력하세요..." }),
      testDataHint: t({ en: "Provide column_name, values, schema, and row_count", ko: "column_name, values, schema, row_count를 제공하세요" }),
      running: t({ en: "Running...", ko: "실행 중..." }),
      testResults: t({ en: "Test Results", ko: "테스트 결과" }),
      passed: t({ en: "Passed", ko: "통과" }),
      failed: t({ en: "Failed", ko: "실패" }),
      error: t({ en: "Error", ko: "오류" }),
      testNoCode: t({ en: "Please write some validator code first", ko: "먼저 검증기 코드를 작성하세요" }),
      testInvalidJson: t({ en: "Invalid JSON in test data", ko: "테스트 데이터의 JSON이 유효하지 않습니다" }),
      testError: t({ en: "An error occurred during testing", ko: "테스트 중 오류가 발생했습니다" }),

      // Reporter Editor
      createReporter: t({ en: "Create Reporter", ko: "리포터 생성" }),
      editReporter: t({ en: "Edit Reporter", ko: "리포터 수정" }),
      createReporterDescription: t({
        en: "Create a new custom reporter with Jinja2 template or Python code",
        ko: "Jinja2 템플릿 또는 Python 코드로 새 커스텀 리포터를 생성합니다",
      }),
      editReporterDescription: t({
        en: "Edit the custom reporter template and settings",
        ko: "커스텀 리포터 템플릿과 설정을 수정합니다",
      }),
      editorTab: t({ en: "Editor", ko: "에디터" }),
      previewTab: t({ en: "Preview", ko: "미리보기" }),
      jinja2Template: t({ en: "Jinja2 Template", ko: "Jinja2 템플릿" }),
      pythonCode: t({ en: "Python Code", ko: "Python 코드" }),
      templatePlaceholder: t({ en: "Enter your Jinja2 template here...", ko: "Jinja2 템플릿을 입력하세요..." }),
      templateHint: t({ en: "Use {{ variable }} for variable interpolation", ko: "변수 보간에 {{ variable }}을 사용하세요" }),
      codeHint: t({ en: "Define a generate_report(data, config, format, metadata) function", ko: "generate_report(data, config, format, metadata) 함수를 정의하세요" }),
      outputFormats: t({ en: "Output Formats", ko: "출력 포맷" }),
      configFields: t({ en: "Configuration Fields", ko: "설정 필드" }),
      noConfigFields: t({ en: "No configuration fields defined", ko: "정의된 설정 필드가 없습니다" }),
      addField: t({ en: "Add Field", ko: "필드 추가" }),
      fieldName: t({ en: "Field Name", ko: "필드 이름" }),
      fieldType: t({ en: "Field Type", ko: "필드 타입" }),
      fieldLabel: t({ en: "Label", ko: "라벨" }),
      fieldDescription: t({ en: "Description", ko: "설명" }),
      fieldOptionsHint: t({ en: "Format: Label:value, or just Label for both", ko: "형식: 라벨:값, 또는 동일할 경우 라벨만" }),
      required: t({ en: "Required", ko: "필수" }),
      defaultValue: t({ en: "Default Value", ko: "기본값" }),
      minValue: t({ en: "Min Value", ko: "최소값" }),
      maxValue: t({ en: "Max Value", ko: "최대값" }),
      options: t({ en: "Options", ko: "옵션" }),
      optionsHint: t({ en: "Comma-separated values", ko: "쉼표로 구분된 값" }),

      // Preview Panel
      reporterConfig: t({ en: "Configuration", ko: "설정" }),
      sampleData: t({ en: "Sample Data (JSON)", ko: "샘플 데이터 (JSON)" }),
      sampleDataPlaceholder: t({ en: "Enter sample data for preview...", ko: "미리보기용 샘플 데이터를 입력하세요..." }),
      sampleDataHint: t({ en: "Data available in template via {{ variable }}", ko: "{{ variable }}을 통해 템플릿에서 사용 가능한 데이터" }),
      generating: t({ en: "Generating...", ko: "생성 중..." }),
      preview: t({ en: "Preview", ko: "미리보기" }),
      previewResult: t({ en: "Preview Result", ko: "미리보기 결과" }),
      previewNoTemplate: t({ en: "Please write a template or code first", ko: "먼저 템플릿 또는 코드를 작성하세요" }),
      previewInvalidJson: t({ en: "Invalid JSON in sample data", ko: "샘플 데이터의 JSON이 유효하지 않습니다" }),
      previewError: t({ en: "An error occurred during preview", ko: "미리보기 중 오류가 발생했습니다" }),

      // Validation
      validationError: t({ en: "Validation Error", ko: "유효성 오류" }),
      nameRequired: t({ en: "Name is required", ko: "이름은 필수입니다" }),
      displayNameRequired: t({ en: "Display name is required", ko: "표시 이름은 필수입니다" }),
      codeRequired: t({ en: "Code is required", ko: "코드는 필수입니다" }),
      templateOrCodeRequired: t({ en: "Template or code is required", ko: "템플릿 또는 코드가 필요합니다" }),

      // Actions
      saving: t({ en: "Saving...", ko: "저장 중..." }),
    },

    // Plugin detail dialog
    detail: {
      overview: t({ en: "Overview", ko: "개요" }),
      changelog: t({ en: "Changelog", ko: "변경 로그" }),
      description: t({ en: "Description", ko: "설명" }),
      permissions: t({ en: "Permissions Required", ko: "필요한 권한" }),
      dependencies: t({ en: "Dependencies", ko: "의존성" }),
      contents: t({ en: "Plugin Contents", ko: "플러그인 내용" }),
      validatorsIncluded: t({ en: "Custom validators included", ko: "포함된 커스텀 검증기" }),
      reportersIncluded: t({ en: "Custom reporters included", ko: "포함된 커스텀 리포터" }),
      type: t({ en: "Type", ko: "타입" }),
      source: t({ en: "Source", ko: "소스" }),
      license: t({ en: "License", ko: "라이선스" }),
      version: t({ en: "Version", ko: "버전" }),
      homepage: t({ en: "Homepage", ko: "홈페이지" }),
      documentation: t({ en: "Documentation", ko: "문서" }),
      noReadme: t({ en: "No README available", ko: "README가 없습니다" }),
      noChangelog: t({ en: "No changelog available", ko: "변경 로그가 없습니다" }),
    },
  },
} satisfies Dictionary;

export default pluginsContent;
