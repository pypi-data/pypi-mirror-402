/**
 * Lineage page translations.
 *
 * Contains translations for the data lineage visualization page.
 */
import { t, type Dictionary } from 'intlayer'

const lineageContent = {
  key: 'lineage',
  content: {
    title: t({ en: 'Data Lineage', ko: '데이터 계보' }),
    subtitle: t({
      en: 'Visualize data flow and dependencies',
      ko: '데이터 흐름 및 종속성 시각화',
    }),

    // Actions
    addNode: t({ en: 'Add Node', ko: '노드 추가' }),
    addEdge: t({ en: 'Add Edge', ko: '엣지 추가' }),
    deleteNode: t({ en: 'Delete Node', ko: '노드 삭제' }),
    deleteEdge: t({ en: 'Delete Edge', ko: '엣지 삭제' }),
    fitView: t({ en: 'Fit View', ko: '화면 맞춤' }),
    autoLayout: t({ en: 'Auto Layout', ko: '자동 배치' }),
    autoDiscover: t({ en: 'Auto Discover', ko: '자동 탐색' }),
    savePositions: t({ en: 'Save Positions', ko: '위치 저장' }),
    analyzeImpact: t({ en: 'Analyze Impact', ko: '영향 분석' }),
    refresh: t({ en: 'Refresh', ko: '새로고침' }),

    // Node types
    nodeTypes: {
      source: t({ en: 'Source', ko: '소스' }),
      transform: t({ en: 'Transform', ko: '변환' }),
      sink: t({ en: 'Sink', ko: '싱크' }),
    },

    // Edge types
    edgeTypes: {
      derives_from: t({ en: 'Derives From', ko: '파생됨' }),
      transforms_to: t({ en: 'Transforms To', ko: '변환됨' }),
      feeds_into: t({ en: 'Feeds Into', ko: '공급됨' }),
    },

    // Form fields
    nodeName: t({ en: 'Node Name', ko: '노드 이름' }),
    nodeType: t({ en: 'Node Type', ko: '노드 유형' }),
    linkedSource: t({ en: 'Linked Source', ko: '연결된 소스' }),
    sourceNode: t({ en: 'Source Node', ko: '소스 노드' }),
    targetNode: t({ en: 'Target Node', ko: '대상 노드' }),
    edgeType: t({ en: 'Edge Type', ko: '엣지 유형' }),
    selectNode: t({ en: 'Select a node', ko: '노드 선택' }),
    selectType: t({ en: 'Select a type', ko: '유형 선택' }),
    description: t({ en: 'Description', ko: '설명' }),
    metadata: t({ en: 'Metadata', ko: '메타데이터' }),

    // Node details panel
    nodeDetails: t({ en: 'Node Details', ko: '노드 상세' }),
    noNodeSelected: t({ en: 'Select a node to view details', ko: '상세 정보를 보려면 노드를 선택하세요' }),
    connectedNodes: t({ en: 'Connected Nodes', ko: '연결된 노드' }),
    upstream: t({ en: 'Upstream', ko: '상위' }),
    downstream: t({ en: 'Downstream', ko: '하위' }),
    createdAt: t({ en: 'Created', ko: '생성일' }),
    updatedAt: t({ en: 'Updated', ko: '수정일' }),

    // Impact analysis
    impactAnalysis: t({ en: 'Impact Analysis', ko: '영향 분석' }),
    impactDescription: t({
      en: 'View upstream and downstream dependencies',
      ko: '상위 및 하위 종속성 확인',
    }),
    affectedUpstream: t({ en: 'Affected Upstream', ko: '영향받는 상위' }),
    affectedDownstream: t({ en: 'Affected Downstream', ko: '영향받는 하위' }),
    analysisDepth: t({ en: 'Analysis Depth', ko: '분석 깊이' }),

    // Auto-discovery
    discovering: t({ en: 'Discovering...', ko: '탐색 중...' }),
    discoveryComplete: t({ en: 'Discovery complete', ko: '탐색 완료' }),
    discoveryFailed: t({ en: 'Discovery failed', ko: '탐색 실패' }),
    nodesDiscovered: t({ en: 'nodes discovered', ko: '개의 노드 발견' }),
    edgesDiscovered: t({ en: 'edges discovered', ko: '개의 엣지 발견' }),

    // Empty states
    noLineageYet: t({ en: 'No lineage data yet', ko: '계보 데이터 없음' }),
    noLineageDesc: t({
      en: 'Add nodes manually or use auto-discovery to map your data flow',
      ko: '노드를 직접 추가하거나 자동 탐색을 사용하여 데이터 흐름을 매핑하세요',
    }),

    // Confirmations
    confirmDeleteNode: t({
      en: 'Are you sure you want to delete this node? This will also remove all connected edges.',
      ko: '이 노드를 삭제하시겠습니까? 연결된 모든 엣지도 함께 삭제됩니다.',
    }),
    confirmDeleteEdge: t({
      en: 'Are you sure you want to delete this edge?',
      ko: '이 엣지를 삭제하시겠습니까?',
    }),

    // Success messages
    nodeCreated: t({ en: 'Node created successfully', ko: '노드가 생성되었습니다' }),
    nodeUpdated: t({ en: 'Node updated successfully', ko: '노드가 수정되었습니다' }),
    nodeDeleted: t({ en: 'Node deleted successfully', ko: '노드가 삭제되었습니다' }),
    edgeCreated: t({ en: 'Edge created successfully', ko: '엣지가 생성되었습니다' }),
    edgeDeleted: t({ en: 'Edge deleted successfully', ko: '엣지가 삭제되었습니다' }),
    positionsSaved: t({ en: 'Positions saved', ko: '위치가 저장되었습니다' }),

    // Error messages
    errorLoadingLineage: t({ en: 'Failed to load lineage', ko: '계보 로드 실패' }),
    errorCreatingNode: t({ en: 'Failed to create node', ko: '노드 생성 실패' }),
    errorDeletingNode: t({ en: 'Failed to delete node', ko: '노드 삭제 실패' }),
    errorCreatingEdge: t({ en: 'Failed to create edge', ko: '엣지 생성 실패' }),
    errorDeletingEdge: t({ en: 'Failed to delete edge', ko: '엣지 삭제 실패' }),
    errorSavingPositions: t({ en: 'Failed to save positions', ko: '위치 저장 실패' }),

    // Stats
    totalNodes: t({ en: 'Total Nodes', ko: '전체 노드' }),
    totalEdges: t({ en: 'Total Edges', ko: '전체 엣지' }),
    sources: t({ en: 'Sources', ko: '소스' }),
    transforms: t({ en: 'Transforms', ko: '변환' }),
    sinks: t({ en: 'Sinks', ko: '싱크' }),

    // Controls
    zoomIn: t({ en: 'Zoom In', ko: '확대' }),
    zoomOut: t({ en: 'Zoom Out', ko: '축소' }),
    resetZoom: t({ en: 'Reset Zoom', ko: '줌 초기화' }),
    toggleMinimap: t({ en: 'Toggle Minimap', ko: '미니맵 토글' }),
    toggleControls: t({ en: 'Toggle Controls', ko: '컨트롤 토글' }),

    // Renderer selector
    renderers: {
      selectRenderer: t({ en: 'Select Renderer', ko: '렌더러 선택' }),
      reactflow: t({ en: 'React Flow', ko: 'React Flow' }),
      cytoscape: t({ en: 'Cytoscape', ko: 'Cytoscape' }),
      mermaid: t({ en: 'Mermaid', ko: 'Mermaid' }),
      reactflowDesc: t({ en: 'Interactive, drag & drop', ko: '인터랙티브, 드래그 앤 드롭' }),
      cytoscapeDesc: t({ en: 'High performance, large graphs', ko: '고성능, 대규모 그래프' }),
      mermaidDesc: t({ en: 'Export, documentation', ko: '내보내기, 문서화' }),
    },

    // Cytoscape layouts
    layouts: {
      selectLayout: t({ en: 'Select Layout', ko: '레이아웃 선택' }),
      dagre: t({ en: 'Dagre (Hierarchical)', ko: 'Dagre (계층형)' }),
      breadthfirst: t({ en: 'Breadth First', ko: '너비 우선' }),
      cose: t({ en: 'CoSE (Force-directed)', ko: 'CoSE (힘 기반)' }),
      circle: t({ en: 'Circle', ko: '원형' }),
      grid: t({ en: 'Grid', ko: '그리드' }),
      concentric: t({ en: 'Concentric', ko: '동심원' }),
    },

    // Mermaid specific
    mermaid: {
      direction: t({ en: 'Direction', ko: '방향' }),
      leftToRight: t({ en: 'Left to Right', ko: '좌에서 우로' }),
      topToBottom: t({ en: 'Top to Bottom', ko: '위에서 아래로' }),
      rightToLeft: t({ en: 'Right to Left', ko: '우에서 좌로' }),
      bottomToTop: t({ en: 'Bottom to Top', ko: '아래에서 위로' }),
      style: t({ en: 'Style', ko: '스타일' }),
      grouped: t({ en: 'Grouped', ko: '그룹화' }),
      simple: t({ en: 'Simple', ko: '단순' }),
      showCode: t({ en: 'Show Mermaid Code', ko: 'Mermaid 코드 보기' }),
      hideCode: t({ en: 'Hide Mermaid Code', ko: 'Mermaid 코드 숨기기' }),
      copy: t({ en: 'Copy', ko: '복사' }),
      copyCode: t({ en: 'Copy Mermaid Code', ko: 'Mermaid 코드 복사' }),
      downloadMermaid: t({ en: 'Download Mermaid (.mmd)', ko: 'Mermaid 다운로드 (.mmd)' }),
      downloadSvg: t({ en: 'Download SVG', ko: 'SVG 다운로드' }),
      codeCopied: t({ en: 'Mermaid code copied to clipboard', ko: 'Mermaid 코드가 클립보드에 복사되었습니다' }),
      copyFailed: t({ en: 'Failed to copy to clipboard', ko: '클립보드 복사 실패' }),
      fileDownloaded: t({ en: 'File downloaded', ko: '파일이 다운로드되었습니다' }),
      svgDownloaded: t({ en: 'SVG downloaded', ko: 'SVG가 다운로드되었습니다' }),
      renderError: t({ en: 'Failed to render diagram', ko: '다이어그램 렌더링 실패' }),
    },

    // Export panel
    export: {
      export: t({ en: 'Export', ko: '내보내기' }),
      copyMermaid: t({ en: 'Copy as Mermaid', ko: 'Mermaid로 복사' }),
      copyJson: t({ en: 'Copy as JSON', ko: 'JSON으로 복사' }),
      downloadMermaid: t({ en: 'Download Mermaid (.mmd)', ko: 'Mermaid 다운로드 (.mmd)' }),
      downloadJson: t({ en: 'Download JSON (.json)', ko: 'JSON 다운로드 (.json)' }),
      downloadSvg: t({ en: 'Download SVG (.svg)', ko: 'SVG 다운로드 (.svg)' }),
      downloadPng: t({ en: 'Download PNG (.png)', ko: 'PNG 다운로드 (.png)' }),
      mermaidCopied: t({ en: 'Mermaid code copied', ko: 'Mermaid 코드가 복사되었습니다' }),
      jsonCopied: t({ en: 'JSON data copied', ko: 'JSON 데이터가 복사되었습니다' }),
      copyFailed: t({ en: 'Failed to copy', ko: '복사 실패' }),
      fileDownloaded: t({ en: 'File downloaded', ko: '파일이 다운로드되었습니다' }),
      svgDownloaded: t({ en: 'SVG downloaded', ko: 'SVG가 다운로드되었습니다' }),
      pngDownloaded: t({ en: 'PNG downloaded', ko: 'PNG가 다운로드되었습니다' }),
      noSvgFound: t({ en: 'No diagram found to export', ko: '내보낼 다이어그램을 찾을 수 없습니다' }),
      exportFailed: t({ en: 'Export failed', ko: '내보내기 실패' }),
    },

    // Renderer preference
    rendererPreference: t({ en: 'Renderer Preference', ko: '렌더러 기본 설정' }),
    savedRendererPreference: t({ en: 'Renderer preference saved', ko: '렌더러 기본 설정이 저장되었습니다' }),

    // OpenLineage Webhooks
    openLineageSettings: t({ en: 'OpenLineage Settings', ko: 'OpenLineage 설정' }),
    webhooks: t({ en: 'Webhooks', ko: '웹훅' }),
    webhookConfig: t({ en: 'Webhook Configuration', ko: '웹훅 설정' }),
    webhookConfigDesc: t({
      en: 'Configure webhooks to emit OpenLineage events to external systems',
      ko: '외부 시스템에 OpenLineage 이벤트를 전송할 웹훅 설정',
    }),
    addWebhook: t({ en: 'Add Webhook', ko: '웹훅 추가' }),
    editWebhook: t({ en: 'Edit Webhook', ko: '웹훅 수정' }),
    webhookName: t({ en: 'Webhook Name', ko: '웹훅 이름' }),
    webhookUrl: t({ en: 'Webhook URL', ko: '웹훅 URL' }),
    webhookUrlPlaceholder: t({
      en: 'https://api.example.com/v1/lineage',
      ko: 'https://api.example.com/v1/lineage',
    }),
    apiKey: t({ en: 'API Key', ko: 'API 키' }),
    apiKeyOptional: t({ en: 'API Key (Optional)', ko: 'API 키 (선택)' }),
    apiKeyPlaceholder: t({ en: 'Bearer token for authentication', ko: '인증용 Bearer 토큰' }),
    customHeaders: t({ en: 'Custom Headers', ko: '사용자 정의 헤더' }),
    headerKey: t({ en: 'Header Key', ko: '헤더 키' }),
    headerValue: t({ en: 'Header Value', ko: '헤더 값' }),
    addHeader: t({ en: 'Add Header', ko: '헤더 추가' }),
    eventTypes: t({ en: 'Event Types', ko: '이벤트 유형' }),
    eventTypesDesc: t({
      en: 'Types of OpenLineage events to emit',
      ko: '전송할 OpenLineage 이벤트 유형',
    }),
    allEvents: t({ en: 'All Events', ko: '모든 이벤트' }),
    jobEventsOnly: t({ en: 'Job Events Only', ko: '작업 이벤트만' }),
    datasetEventsOnly: t({ en: 'Dataset Events Only', ko: '데이터셋 이벤트만' }),
    batchSize: t({ en: 'Batch Size', ko: '배치 크기' }),
    batchSizeDesc: t({ en: 'Number of events per HTTP request', ko: 'HTTP 요청당 이벤트 수' }),
    timeout: t({ en: 'Timeout (seconds)', ko: '타임아웃 (초)' }),
    timeoutDesc: t({ en: 'Request timeout in seconds', ko: '요청 타임아웃 (초)' }),
    activeWebhook: t({ en: 'Active', ko: '활성화' }),
    inactiveWebhook: t({ en: 'Inactive', ko: '비활성화' }),
    testConnection: t({ en: 'Test Connection', ko: '연결 테스트' }),
    testing: t({ en: 'Testing...', ko: '테스트 중...' }),

    // Webhook Status
    webhookStatus: t({ en: 'Status', ko: '상태' }),
    lastSent: t({ en: 'Last Sent', ko: '마지막 전송' }),
    neverSent: t({ en: 'Never sent', ko: '전송된 적 없음' }),
    successCount: t({ en: 'Success', ko: '성공' }),
    failureCount: t({ en: 'Failures', ko: '실패' }),
    successRate: t({ en: 'Success Rate', ko: '성공률' }),
    lastError: t({ en: 'Last Error', ko: '마지막 오류' }),
    responseTime: t({ en: 'Response Time', ko: '응답 시간' }),
    statusCode: t({ en: 'Status Code', ko: '상태 코드' }),

    // Webhook Messages
    webhookCreated: t({ en: 'Webhook created successfully', ko: '웹훅이 생성되었습니다' }),
    webhookUpdated: t({ en: 'Webhook updated successfully', ko: '웹훅이 수정되었습니다' }),
    webhookDeleted: t({ en: 'Webhook deleted successfully', ko: '웹훅이 삭제되었습니다' }),
    webhookTestSuccess: t({ en: 'Connection successful', ko: '연결 성공' }),
    webhookTestFailed: t({ en: 'Connection failed', ko: '연결 실패' }),
    confirmDeleteWebhook: t({
      en: 'Are you sure you want to delete this webhook?',
      ko: '이 웹훅을 삭제하시겠습니까?',
    }),

    // No webhooks state
    noWebhooks: t({ en: 'No webhooks configured', ko: '설정된 웹훅 없음' }),
    noWebhooksDesc: t({
      en: 'Add a webhook to emit OpenLineage events to external systems like Marquez or DataHub',
      ko: 'Marquez나 DataHub 같은 외부 시스템에 OpenLineage 이벤트를 전송하려면 웹훅을 추가하세요',
    }),

    // Error messages
    errorLoadingWebhooks: t({ en: 'Failed to load webhooks', ko: '웹훅 로드 실패' }),
    errorCreatingWebhook: t({ en: 'Failed to create webhook', ko: '웹훅 생성 실패' }),
    errorUpdatingWebhook: t({ en: 'Failed to update webhook', ko: '웹훅 수정 실패' }),
    errorDeletingWebhook: t({ en: 'Failed to delete webhook', ko: '웹훅 삭제 실패' }),
    errorTestingWebhook: t({ en: 'Failed to test webhook', ko: '웹훅 테스트 실패' }),

    // Performance Mode
    performanceMode: t({ en: 'Performance Mode', ko: '성능 모드' }),
    performanceInfo: t({ en: 'Performance', ko: '성능' }),
    performanceOptimizations: t({ en: 'Performance Optimizations', ko: '성능 최적화' }),
    performanceOptimizationsDesc: t({
      en: 'Automatic optimizations for large graphs including node clustering, viewport culling, and lazy loading.',
      ko: '노드 클러스터링, 뷰포트 컬링, 지연 로딩을 포함한 대규모 그래프를 위한 자동 최적화.',
    }),
    clusteringThreshold: t({ en: 'Clustering Threshold', ko: '클러스터링 임계값' }),
    virtualizationThreshold: t({ en: 'Virtualization Threshold', ko: '가상화 임계값' }),
    warningThreshold: t({ en: 'Warning Threshold', ko: '경고 임계값' }),
    forcePerformanceMode: t({ en: 'Force Performance Mode', ko: '성능 모드 강제 적용' }),
    largeGraphWarning: t({
      en: 'Large graph detected. Performance optimizations have been automatically enabled.',
      ko: '대규모 그래프가 감지되었습니다. 성능 최적화가 자동으로 활성화되었습니다.',
    }),
    enablePerformanceMode: t({
      en: 'Consider enabling performance mode for smoother interaction.',
      ko: '더 부드러운 상호작용을 위해 성능 모드 활성화를 고려하세요.',
    }),

    // Clustering
    cluster: t({ en: 'Cluster', ko: '클러스터' }),
    nodesClustered: t({ en: 'nodes clustered', ko: '개의 노드 클러스터링됨' }),
    expandCluster: t({ en: 'Expand cluster', ko: '클러스터 확장' }),
    collapseCluster: t({ en: 'Collapse cluster', ko: '클러스터 축소' }),
    clickToExpand: t({ en: 'Click to expand', ko: '클릭하여 확장' }),
    clickToCollapse: t({ en: 'Click to collapse', ko: '클릭하여 축소' }),

    // Minimap
    minimap: t({ en: 'Minimap', ko: '미니맵' }),
    minimapClickToNavigate: t({ en: 'Click to navigate', ko: '클릭하여 이동' }),
    minimapDoubleClickToFit: t({ en: 'Double-click to fit view', ko: '더블클릭하여 화면에 맞춤' }),
    visibleNodes: t({ en: 'Visible Nodes', ko: '표시된 노드' }),

    // Performance metrics
    fps: t({ en: 'FPS', ko: 'FPS' }),
    renderTime: t({ en: 'Render Time', ko: '렌더링 시간' }),
    memoryUsage: t({ en: 'Memory Usage', ko: '메모리 사용량' }),

    // Column-level lineage
    columnLineage: {
      title: t({ en: 'Column Lineage', ko: '컬럼 계보' }),
      showColumnLineage: t({ en: 'Show Columns', ko: '컬럼 표시' }),
      hideColumnLineage: t({ en: 'Hide Columns', ko: '컬럼 숨기기' }),
      errorLoadingData: t({ en: 'Failed to load column lineage data', ko: '컬럼 계보 데이터 로드 실패' }),
      impactMode: t({ en: 'Impact Mode', ko: '영향 모드' }),
      columnLevel: t({ en: 'Column Level', ko: '컬럼 수준' }),
      tableLevel: t({ en: 'Table Level', ko: '테이블 수준' }),
      impactAnalysisActive: t({ en: 'Impact Analysis Active', ko: '영향 분석 활성화' }),
      graphView: t({ en: 'Graph View', ko: '그래프 보기' }),
      tableView: t({ en: 'Table View', ko: '테이블 보기' }),

      // Panel
      searchPlaceholder: t({ en: 'Search columns...', ko: '컬럼 검색...' }),
      filterByType: t({ en: 'Filter by type', ko: '유형별 필터' }),
      allTypes: t({ en: 'All types', ko: '모든 유형' }),
      mappingsCount: t({ en: 'mappings', ko: '개 매핑' }),
      typesCount: t({ en: 'types', ko: '개 유형' }),
      noMappings: t({ en: 'No column mappings found', ko: '컬럼 매핑을 찾을 수 없습니다' }),

      // Transformation types
      transformationTypes: {
        direct: t({ en: 'Direct', ko: '직접' }),
        derived: t({ en: 'Derived', ko: '파생' }),
        aggregated: t({ en: 'Aggregated', ko: '집계' }),
        filtered: t({ en: 'Filtered', ko: '필터링' }),
        joined: t({ en: 'Joined', ko: '조인' }),
        renamed: t({ en: 'Renamed', ko: '이름 변경' }),
        cast: t({ en: 'Cast', ko: '형변환' }),
        computed: t({ en: 'Computed', ko: '계산됨' }),
      },

      // Edge
      columnMappings: t({ en: 'column mappings', ko: '개 컬럼 매핑' }),
      noColumnMappings: t({ en: 'No column mappings', ko: '컬럼 매핑 없음' }),
      moreMappings: t({ en: 'more mappings', ko: '개 더 보기' }),

      // Table
      searchColumns: t({ en: 'Search columns...', ko: '컬럼 검색...' }),
      sourceColumn: t({ en: 'Source Column', ko: '소스 컬럼' }),
      targetColumn: t({ en: 'Target Column', ko: '대상 컬럼' }),
      transformation: t({ en: 'Transformation', ko: '변환' }),
      confidence: t({ en: 'Confidence', ko: '신뢰도' }),
      noResults: t({ en: 'No results found', ko: '결과를 찾을 수 없습니다' }),
      ofTotal: t({ en: 'of', ko: '/' }),
      mappings: t({ en: 'mappings', ko: '개 매핑' }),

      // Impact analysis
      impactAnalysis: t({ en: 'Column Impact Analysis', ko: '컬럼 영향 분석' }),
      impactDescription: t({
        en: 'View all downstream columns affected by changes',
        ko: '변경으로 영향받는 모든 하위 컬럼 확인',
      }),
      selectColumnToAnalyze: t({
        en: 'Select a column to analyze its downstream impact',
        ko: '하위 영향을 분석할 컬럼을 선택하세요',
      }),
      analyzing: t({ en: 'Analyzing impact...', ko: '영향 분석 중...' }),
      affected: t({ en: 'affected', ko: '개 영향' }),
      affectedColumns: t({ en: 'Affected Columns', ko: '영향받는 컬럼' }),
      affectedTables: t({ en: 'Affected Tables', ko: '영향받는 테이블' }),
      searchAffected: t({ en: 'Search affected columns...', ko: '영향받는 컬럼 검색...' }),
      columns: t({ en: 'columns', ko: '개 컬럼' }),
      depth: t({ en: 'Depth', ko: '깊이' }),
      impactPath: t({ en: 'Impact Path', ko: '영향 경로' }),
      morePaths: t({ en: 'more paths', ko: '개 추가 경로' }),
      noMatchingColumns: t({ en: 'No matching columns found', ko: '일치하는 컬럼을 찾을 수 없습니다' }),
      noDownstreamImpact: t({
        en: 'No downstream columns are affected',
        ko: '영향받는 하위 컬럼이 없습니다',
      }),
      criticalImpactWarning: t({
        en: 'Critical: Changes to this column may affect many downstream systems. Review all dependencies carefully.',
        ko: '중요: 이 컬럼을 변경하면 많은 하위 시스템에 영향을 줄 수 있습니다. 모든 종속성을 신중하게 검토하세요.',
      }),
      highImpactWarning: t({
        en: 'Changes to this column may affect multiple downstream columns. Review dependencies before making changes.',
        ko: '이 컬럼을 변경하면 여러 하위 컬럼에 영향을 줄 수 있습니다. 변경하기 전에 종속성을 검토하세요.',
      }),

      // Node details tabs
      detailsTab: t({ en: 'Details', ko: '상세' }),
      columnsTab: t({ en: 'Columns', ko: '컬럼' }),
      lineageTab: t({ en: 'Lineage', ko: '계보' }),
      noColumnsAvailable: t({ en: 'No columns available', ko: '사용 가능한 컬럼이 없습니다' }),
      incomingMappings: t({ en: 'Incoming Mappings', ko: '들어오는 매핑' }),
      outgoingMappings: t({ en: 'Outgoing Mappings', ko: '나가는 매핑' }),
    },

    // Anomaly Integration
    anomaly: {
      // Toggle controls
      showAnomalies: t({ en: 'Show Anomalies', ko: '이상 징후 표시' }),
      hideAnomalies: t({ en: 'Hide Anomalies', ko: '이상 징후 숨기기' }),

      // Legend
      legend: t({ en: 'Anomaly Legend', ko: '이상 징후 범례' }),
      showLegend: t({ en: 'Show Legend', ko: '범례 표시' }),
      hideLegend: t({ en: 'Hide Legend', ko: '범례 숨기기' }),
      filterByStatus: t({ en: 'Filter by Status', ko: '상태별 필터' }),
      selectAll: t({ en: 'Select All', ko: '모두 선택' }),
      deselectAll: t({ en: 'Deselect All', ko: '모두 해제' }),
      nodeStatus: t({ en: 'Node Anomaly Status', ko: '노드 이상 상태' }),
      noNodesVisible: t({ en: 'All nodes hidden by filter', ko: '필터로 모든 노드가 숨겨짐' }),

      // Impact paths
      impactPaths: t({ en: 'Impact Paths', ko: '영향 경로' }),
      showPaths: t({ en: 'Show', ko: '표시' }),
      hidePaths: t({ en: 'Hide', ko: '숨기기' }),

      // Status levels
      statusLevels: {
        unknown: t({ en: 'Unknown', ko: '알 수 없음' }),
        clean: t({ en: 'Clean', ko: '정상' }),
        low: t({ en: 'Low', ko: '낮음' }),
        medium: t({ en: 'Medium', ko: '중간' }),
        high: t({ en: 'High', ko: '높음' }),
      },

      // Status descriptions
      statusDescriptions: {
        unknown: t({ en: 'No anomaly detection run', ko: '이상 탐지 미실행' }),
        clean: t({ en: 'No anomalies detected', ko: '이상 없음' }),
        low: t({ en: '0-5% anomaly rate', ko: '0-5% 이상률' }),
        medium: t({ en: '5-15% anomaly rate', ko: '5-15% 이상률' }),
        high: t({ en: '15%+ anomaly rate', ko: '15% 이상 이상률' }),
      },

      // Severity levels
      severityLevels: {
        unknown: t({ en: 'Unknown', ko: '알 수 없음' }),
        none: t({ en: 'None', ko: '없음' }),
        low: t({ en: 'Low Impact', ko: '낮은 영향' }),
        medium: t({ en: 'Medium Impact', ko: '중간 영향' }),
        high: t({ en: 'High Impact', ko: '높은 영향' }),
        critical: t({ en: 'Critical Impact', ko: '심각한 영향' }),
      },

      // Tooltip content
      anomalyRate: t({ en: 'Anomaly Rate', ko: '이상률' }),
      anomalyCount: t({ en: 'Anomaly Count', ko: '이상 수' }),
      algorithm: t({ en: 'Algorithm', ko: '알고리즘' }),
      lastScan: t({ en: 'Last Scan', ko: '마지막 스캔' }),
      never: t({ en: 'Never', ko: '없음' }),
      impactedByUpstream: t({
        en: 'Potentially impacted by upstream anomalies',
        ko: '상위 이상 징후로 잠재적 영향',
      }),

      // Impact analysis
      analyzeAnomalyImpact: t({ en: 'Analyze Anomaly Impact', ko: '이상 영향 분석' }),
      anomalyImpactAnalysis: t({ en: 'Anomaly Impact Analysis', ko: '이상 영향 분석' }),
      sourceAnomaly: t({ en: 'Source Anomaly', ko: '소스 이상' }),
      impactedDownstream: t({ en: 'Impacted Downstream', ko: '영향받는 하위' }),
      overallSeverity: t({ en: 'Overall Severity', ko: '전체 심각도' }),
      propagationPath: t({ en: 'Propagation Path', ko: '전파 경로' }),
      noImpactedNodes: t({ en: 'No downstream nodes impacted', ko: '영향받는 하위 노드 없음' }),
      analysisRequiresSource: t({
        en: 'Anomaly impact analysis requires a node linked to a data source',
        ko: '이상 영향 분석은 데이터 소스에 연결된 노드가 필요합니다',
      }),

      // Error messages
      errorLoadingAnomalies: t({
        en: 'Failed to load anomaly data',
        ko: '이상 데이터 로드 실패',
      }),
      errorAnalyzingImpact: t({
        en: 'Failed to analyze anomaly impact',
        ko: '이상 영향 분석 실패',
      }),
    },
  },
} satisfies Dictionary

export default lineageContent
