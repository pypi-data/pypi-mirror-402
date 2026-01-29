
<img width="2551" height="911" alt="스크린샷 2026-01-08 오전 11 54 18" src="https://github.com/user-attachments/assets/5e6b6d39-ee69-48f3-b0df-577f73bcb03d" />

# truthound-dashboard

[![PyPI version](https://img.shields.io/pypi/v/truthound-dashboard.svg)](https://pypi.org/project/truthound-dashboard/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](https://opensource.org/licenses/Apache-2.0)
[![Powered by Intlayer](https://img.shields.io/badge/Powered%20by-Intlayer-yellow.svg)](https://intlayer.org)
[![Downloads](https://img.shields.io/pepy/dt/truthound-dashboard?color=brightgreen)](https://pepy.tech/project/truthound-dashboard)

A web-based data quality monitoring dashboard for [truthound](https://github.com/seadonggyun4/truthound).

[Documentation](https://truthound.netlify.app) | [PyPI](https://pypi.org/project/truthound-dashboard/)

## Overview
<img width="300" height="300" alt="Truthound_icon" src="https://github.com/user-attachments/assets/90d9e806-8895-45ec-97dc-f8300da4d997" />

truthound-dashboard provides a graphical interface for managing data sources, executing validations, tracking historical results, scheduling automated checks, and configuring notifications. It serves as an alternative to commercial data quality platforms.

## Feature Comparison with GX Cloud

| Feature | GX Cloud (Paid) | truthound-dashboard |
|---------|-----------------|---------------------|
| Data Source Management | Available | Available |
| Schema Learning | Available | Available |
| Validation Execution | Available | Available |
| Validator Registry | Available | Available (150+ validators) |
| Validation History | Available | Available |
| Scheduled Validations | Available | Available |
| Slack Notifications | Available | Available |
| Email Notifications | Available | Available |
| Webhook Notifications | Available | Available |
| Drift Detection | Available | Available (5 methods) |
| Data Profiling | Available | Available |
| PII Scan | Available | Available (GDPR/CCPA/LGPD) |
| Data Masking | Available | Available (redact/hash/fake) |
| Anomaly Detection | Limited | Available (6 algorithms) |
| Data Lineage | Available | Available (3 viz options) |
| Model Monitoring | Available | Available |
| Reports & Export | Available | Available (6 formats) |
| Plugins Marketplace | Not Available | Available |
| Maintenance Tools | Limited | Available |
| Dark Mode | Available | Available |
| Multi-language | Limited | 2 languages (en, ko) + AI translation CLI |
| License | Commercial | Apache 2.0 |

## Requirements

- Python 3.11 or higher
- truthound >= 1.0.5

## Installation

```bash
pip install truthound-dashboard
```

This command automatically installs [truthound](https://github.com/seadonggyun4/truthound) as a dependency.

## Usage

```bash
# Start the dashboard server (default port: 8765)
truthound serve

# Specify a custom port
truthound serve --port 9000

# Enable development mode with hot reload
truthound serve --reload

# Disable automatic browser opening
truthound serve --no-browser
```

The dashboard interface is accessible at `http://localhost:8765`.

## Implemented Features

### Data Source Management
- Supported file formats: CSV, Parquet, JSON
- Supported databases (13 connectors): PostgreSQL, MySQL, SQLite, BigQuery, Snowflake, Redshift, Databricks, Oracle, SQL Server, Spark
- Connection validation and management UI
- Dynamic configuration forms per source type

### Schema Management
- Automated schema generation using `th.learn`
- Manual schema editing in YAML format

### Validation
- On-demand validation execution using `th.check`
- 150+ validators across 15 categories (schema, completeness, uniqueness, distribution, string, datetime, aggregate, cross-table, multi-column, query, table, geospatial, drift, anomaly, privacy)
- Per-validator parameter configuration with UI
- Persistent storage of validation results
- Issue classification by severity (Critical, High, Medium, Low)
- Advanced options: column filtering, min_severity, parallel execution, SQL pushdown
- ML-based caching layer for expensive operations

### Anomaly Detection
- 6 ML algorithms: IsolationForest, LocalOutlierFactor, DBSCAN, OneClassSVM, EllipticEnvelope, Ensemble
- Streaming anomaly detection support
- Explainability with feature contribution analysis
- Batch detection with progress tracking
- Algorithm comparison and agreement scoring

### Drift Monitoring
- 5 detection methods: Kolmogorov-Smirnov, Population Stability Index (PSI), Chi-Square, Jensen-Shannon, Auto
- 4 sampling strategies: Random, Stratified, Reservoir, Systematic
- Column-level distribution comparison
- Drift trend visualization and alerting
- Root cause analysis and remediation suggestions

### Data Lineage
- Interactive lineage graph visualization (D3.js/Mermaid/Cytoscape)
- Column-level lineage tracking
- Impact analysis (upstream/downstream)
- OpenLineage standard integration
- Webhook support for lineage events
- Performance optimization with lazy loading and virtualization

### Schema Evolution
- Automatic schema change detection
- Breaking vs non-breaking change classification
- Version timeline and comparison
- Change notification support

### Profile Comparison
- Profile-to-profile comparison
- Time-series trend analysis
- Quality metric visualization (null%, unique%)
- Historical profile snapshots

### Rule Suggestions
- Profile-based automatic rule generation
- Confidence scoring (high/medium/low)
- Bulk rule application
- Category-based filtering (completeness, uniqueness, distribution, string, datetime)

### Reports & Export
- 6 formats: HTML, PDF, CSV, JSON, Excel, Markdown
- Customizable themes for HTML/PDF reports
- Statistics dashboard (total reports, size, downloads, avg generation time)
- Search and filtering (by name, format, status)
- Report lifecycle management with automatic expiration
- Download tracking and batch cleanup
- Integration with validation schedules and notifications

### Plugins & Extensions
- Plugin marketplace for community extensions
- 4 plugin types: Validators, Reporters, Connectors, Transformers
- 4 security levels: Trusted, Verified, Unverified, Sandboxed
- Custom validator creation with UI (severity, category, parameters)
- Custom reporter creation with template support
- Plugin lifecycle management (install, enable, disable, uninstall)
- Filter by type and status

### Maintenance & System Health
- Auto maintenance scheduling with enable/disable toggle
- Retention policies with configurable ranges:
  - Validation history: 1-365 days
  - Profile snapshots: 1-100 per source
  - Notification logs: 1-365 days
- Manual operations: cleanup, vacuum, cache clear
- Cache statistics monitoring (total, valid, expired entries, hit rate)
- Database optimization (VACUUM/ANALYZE)
- Real-time configuration updates

### Validation History
- Historical record of validation results
- Trend visualization
- Result versioning with 4 strategies (Incremental, Semantic, Timestamp, GitLike)
- Version comparison and rollback support

### Scheduling
- Cron-based scheduling using APScheduler
- Schedule controls: pause, resume, immediate execution

### Notifications
- Supported channels: Slack, Email, Webhook
- Configurable notification rules based on validation outcomes
- Notification delivery logs

### Advanced Notifications
- 9 provider channels: Slack, Email, Webhook, Discord, Telegram, PagerDuty, OpsGenie, Microsoft Teams, GitHub
- Rule-based routing with 11+ rule types (severity, issue count, pass rate, time window, tag, data asset, metadata, status, error)
- Deduplication: 4 window strategies (Sliding, Tumbling, Session, Adaptive), 6 policies
- Throttling: 5 methods (TokenBucket, LeakyBucket, FixedWindow, SlidingWindow, Adaptive)
- Multi-level escalation with state machine
- Incident management and acknowledgment

### Unified Alerts
- Cross-feature alert aggregation (validation, drift, anomaly, schema changes)
- Severity-based filtering (Critical, High, Medium, Low)
- Alert correlation and grouping
- Action tracking (acknowledged, resolved)

### Cross-Table Validation
- Referential integrity checks
- Foreign key validation
- SQL-based cross-table queries
- Automated trigger configuration

### Model Monitoring
- ML model performance tracking
- Metric monitoring (accuracy, precision, recall, F1, AUC-ROC)
- Alert rules for model degradation
- Model registration and versioning

### Automated Triggers
- Data change detection triggers
- Composite triggers (AND/OR combinations)
- Cron-based scheduling
- Interval-based execution
- Preview and testing support

### Drift Detection
- Dataset comparison using `th.compare`
- 5 detection methods: Kolmogorov-Smirnov (KS), Population Stability Index (PSI), Chi-Square, Jensen-Shannon (JS), Auto
- 4 sampling strategies: Random, Stratified, Reservoir, Systematic
- Column-level distribution comparison with visualizations
- Drift trend monitoring and alerting
- Root cause analysis and remediation suggestions
- Large dataset support with chunked processing

### Data Profiling
- Statistical profiling using `th.profile`
- Column-level statistics
- Sample size configuration for large datasets

### PII Scan
- Personal data detection using `th.scan`
- Supported PII types: email, phone, SSN, credit card, IP address, and more
- Regulation compliance: GDPR, CCPA, LGPD
- Configurable confidence threshold

### Data Masking
- Sensitive data protection using `th.mask`
- Three masking strategies: redact (asterisks), hash (SHA256), fake (realistic data)
- Auto-detection of PII columns
- Multiple output formats: CSV, Parquet, JSON

### Business Glossary
- Business term definitions with categories
- Term relationships (synonyms, related terms)
- Term lifecycle management (draft, approved, deprecated)
- Change history tracking

### Data Catalog
- Data asset registration (tables, files, APIs)
- Column-level metadata management
- Column-to-term mapping
- Quality score tracking
- Sensitivity classification (public, internal, confidential, restricted)
- Custom tagging

### Collaboration
- Comments on terms, assets, and columns
- Activity feed for tracking changes

### User Interface
- Light and dark theme support with system preference detection
- Internationalization: 2 built-in languages (English, Korean)
- AI-powered translation CLI to expand to 15+ languages (OpenAI, Anthropic, Mistral, Ollama)
- Type-safe translations using Intlayer framework
- Comprehensive E2E test coverage (197+ tests) for all features

## Internationalization

truthound-dashboard implements internationalization using [Intlayer](https://intlayer.org), a modern i18n framework that provides type-safe translations with component-level content declaration.

### Built-in Languages

The dashboard ships with **2 fully translated languages**:
- **English (en)** - Complete UI translation
- **Korean (ko)** - Complete UI translation

These languages are immediately available without additional configuration or setup.

### Extending Language Support

The dashboard can be extended to support 15+ additional languages using the AI-powered `translate` command. This CLI tool translates all UI content files from the built-in English and Korean to your target language.

**Note:** Additional languages are not included in the default installation and must be generated using the translation CLI before deployment.

#### Supported AI Providers

| Provider | Environment Variable | Models |
|----------|---------------------|--------|
| OpenAI | `OPENAI_API_KEY` | GPT-4o, GPT-4o-mini, GPT-4, GPT-3.5 |
| Anthropic | `ANTHROPIC_API_KEY` | Claude Sonnet 4, Claude Opus 4 |
| Mistral | `MISTRAL_API_KEY` | Mistral Large, Mistral Small |
| Ollama | Not required | Llama 3.2, Mistral, Qwen (local execution) |

#### Configuration

API credentials are configured through environment variables. This approach ensures that sensitive credentials are not exposed in command history or application logs.

**Temporary Session Configuration**

```bash
# OpenAI
export OPENAI_API_KEY=sk-xxxxxxxxxxxx
truthound translate -l fr -p openai

# Anthropic
export ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx
truthound translate -l fr -p anthropic

# Mistral
export MISTRAL_API_KEY=xxxxxxxxxxxx
truthound translate -l fr -p mistral
```

**Persistent Configuration**

```bash
# Add to shell configuration file (~/.bashrc or ~/.zshrc)
echo 'export OPENAI_API_KEY=sk-xxxxxxxxxxxx' >> ~/.zshrc
source ~/.zshrc
```

**Inline Configuration**

```bash
OPENAI_API_KEY=sk-xxx truthound translate -l fr -p openai
```

#### Usage Examples

```bash
# Translate to French using OpenAI
truthound translate -l fr -p openai

# Translate to multiple languages
truthound translate -l ja,zh,de,fr -p anthropic

# Use local Ollama (no API key required)
truthound translate -l fr -p ollama

# Auto-detect available provider
truthound translate -l fr

# Preview files without making changes
truthound translate -l fr --dry-run

# List available providers and their status
truthound translate --list-providers

# List supported language codes
truthound translate --list-languages
```

#### Security Considerations

| Aspect | Risk Level | Description |
|--------|------------|-------------|
| Network transmission | None | API keys are used locally and transmitted only to the selected provider |
| Source code exposure | None | Credentials are injected via environment variables |
| Build artifact inclusion | None | Only translated content is persisted; credentials are not stored |
| API communication | Standard | Requests are made directly to provider endpoints using user credentials |

#### Supported Languages

The translation system supports 36 languages including: Arabic, Bulgarian, Chinese, Croatian, Czech, Danish, Dutch, English, Estonian, Finnish, French, German, Greek, Hebrew, Hindi, Hungarian, Indonesian, Italian, Japanese, Korean, Latvian, Lithuanian, Malay, Norwegian, Polish, Portuguese, Romanian, Russian, Slovak, Slovenian, Spanish, Swedish, Thai, Turkish, Ukrainian, and Vietnamese.

Execute `truthound translate --list-languages` to view the complete list with language codes.

## Technology Stack

**Backend**
- FastAPI
- SQLAlchemy 2.0 (async)
- SQLite with aiosqlite
- APScheduler
- Pydantic 2.x

**Frontend**
- React 18
- TypeScript
- Vite
- TailwindCSS
- shadcn/ui
- Zustand
- [Intlayer](https://intlayer.org) (internationalization)

## Development Setup

```bash
# Clone the repository
git clone https://github.com/seadonggyun4/truthound-dashboard
cd truthound-dashboard

# Install backend dependencies
pip install -e ".[dev]"

# Start the backend server
truthound serve --reload

# In a separate terminal, install frontend dependencies
cd frontend
npm install

# Start the frontend development server
npm run dev

# Alternative: run with mock API (backend not required)
npm run dev:mock
```

## Preview with Mock Data

To explore the dashboard interface without configuring a backend or data sources, the repository includes a mock mode that simulates API responses using [Mock Service Worker (MSW)](https://mswjs.io/).

```bash
# Clone the repository
git clone https://github.com/seadonggyun4/truthound-dashboard
cd truthound-dashboard/frontend

# Install dependencies
npm install

# Start the development server with mock data
npm run dev:mock
```

The mock server provides realistic sample data for all dashboard features, enabling evaluation of the user interface and workflow without external dependencies.

## Testing

```bash
# Run tests
pytest

# Run tests with coverage report
pytest --cov=truthound_dashboard
```

## Documentation

Full documentation is available at [https://truthound.netlify.app](https://truthound.netlify.app).

- [Getting Started](./docs/getting-started.md)
- [Features](./docs/features.md)
- [API Reference](./docs/api.md)
- [Configuration](./docs/configuration.md)

## Related Projects

- [truthound](https://github.com/seadonggyun4/truthound) - Core data validation library
- [truthound-orchestration](https://github.com/seadonggyun4/truthound-orchestration) - Pipeline orchestration integration

## License

This project is licensed under the Apache License 2.0.
