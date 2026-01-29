"""Database connection factory and utilities.

Provides utilities for building connection strings and testing connections
for various database types supported by truthound.

Supported Source Types:
    - file: CSV, Parquet, JSON, Excel files
    - postgresql: PostgreSQL database
    - mysql: MySQL database
    - sqlite: SQLite database
    - snowflake: Snowflake data warehouse
    - bigquery: Google BigQuery
    - redshift: Amazon Redshift
    - databricks: Databricks (Unity Catalog / Delta Lake)
    - oracle: Oracle Database
    - sqlserver: Microsoft SQL Server
    - spark: Apache Spark (via JDBC or Hive)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote_plus


class SourceType(str, Enum):
    """Supported data source types."""

    FILE = "file"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"
    REDSHIFT = "redshift"
    DATABRICKS = "databricks"
    ORACLE = "oracle"
    SQLSERVER = "sqlserver"
    SPARK = "spark"


class FieldType(str, Enum):
    """Field types for configuration forms."""

    TEXT = "text"
    PASSWORD = "password"
    NUMBER = "number"
    SELECT = "select"
    BOOLEAN = "boolean"
    FILE_PATH = "file_path"
    TEXTAREA = "textarea"


@dataclass
class FieldDefinition:
    """Definition of a configuration field for UI rendering."""

    name: str
    label: str
    type: FieldType = FieldType.TEXT
    required: bool = False
    placeholder: str = ""
    description: str = ""
    default: Any = None
    options: list[dict[str, str]] = field(default_factory=list)
    min_value: int | None = None
    max_value: int | None = None
    depends_on: str | None = None
    depends_value: Any = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        result = {
            "name": self.name,
            "label": self.label,
            "type": self.type.value,
            "required": self.required,
            "placeholder": self.placeholder,
            "description": self.description,
        }
        if self.default is not None:
            result["default"] = self.default
        if self.options:
            result["options"] = self.options
        if self.min_value is not None:
            result["min_value"] = self.min_value
        if self.max_value is not None:
            result["max_value"] = self.max_value
        if self.depends_on:
            result["depends_on"] = self.depends_on
            result["depends_value"] = self.depends_value
        return result


@dataclass
class SourceTypeDefinition:
    """Complete definition of a source type for UI rendering."""

    type: str
    name: str
    description: str
    icon: str
    category: Literal["file", "database", "warehouse", "bigdata"]
    fields: list[FieldDefinition]
    docs_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "type": self.type,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "fields": [f.to_dict() for f in self.fields],
            "required_fields": [f.name for f in self.fields if f.required],
            "optional_fields": [f.name for f in self.fields if not f.required],
            "docs_url": self.docs_url,
        }


class ConnectionBuilder(ABC):
    """Abstract base class for connection string builders."""

    source_type: SourceType

    @abstractmethod
    def build(self, config: dict[str, Any]) -> str:
        """Build connection string from configuration.

        Args:
            config: Database-specific configuration.

        Returns:
            Connection string.

        Raises:
            ValueError: If required config is missing.
        """
        pass

    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Validate configuration and return list of errors.

        Args:
            config: Configuration to validate.

        Returns:
            List of error messages (empty if valid).
        """
        pass

    @classmethod
    @abstractmethod
    def get_definition(cls) -> SourceTypeDefinition:
        """Get the source type definition for UI rendering."""
        pass


class FileConnectionBuilder(ConnectionBuilder):
    """Connection builder for file-based sources."""

    source_type = SourceType.FILE
    SUPPORTED_EXTENSIONS = {".csv", ".parquet", ".json", ".xlsx", ".xls"}

    def build(self, config: dict[str, Any]) -> str:
        """Build file path from config."""
        return config.get("path", "")

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Validate file configuration."""
        errors = []
        path = config.get("path")

        if not path:
            errors.append("path is required")
        else:
            p = Path(path)
            if p.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                errors.append(
                    f"Unsupported file type: {p.suffix}. "
                    f"Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}"
                )

        return errors

    @classmethod
    def get_definition(cls) -> SourceTypeDefinition:
        """Get the source type definition for UI rendering."""
        return SourceTypeDefinition(
            type=SourceType.FILE.value,
            name="File",
            description="Local file (CSV, Parquet, JSON, Excel)",
            icon="file",
            category="file",
            fields=[
                FieldDefinition(
                    name="path",
                    label="File Path",
                    type=FieldType.FILE_PATH,
                    required=True,
                    placeholder="/path/to/data.csv",
                    description="Path to the data file",
                ),
                FieldDefinition(
                    name="format",
                    label="Format",
                    type=FieldType.SELECT,
                    options=[
                        {"value": "auto", "label": "Auto-detect"},
                        {"value": "csv", "label": "CSV"},
                        {"value": "parquet", "label": "Parquet"},
                        {"value": "json", "label": "JSON"},
                        {"value": "excel", "label": "Excel"},
                    ],
                    default="auto",
                    description="File format (auto-detected from extension if not specified)",
                ),
                FieldDefinition(
                    name="delimiter",
                    label="Delimiter",
                    placeholder=",",
                    default=",",
                    description="CSV delimiter character",
                    depends_on="format",
                    depends_value="csv",
                ),
                FieldDefinition(
                    name="encoding",
                    label="Encoding",
                    type=FieldType.SELECT,
                    options=[
                        {"value": "utf-8", "label": "UTF-8"},
                        {"value": "utf-16", "label": "UTF-16"},
                        {"value": "iso-8859-1", "label": "ISO-8859-1 (Latin-1)"},
                        {"value": "cp1252", "label": "Windows-1252"},
                    ],
                    default="utf-8",
                    description="File encoding",
                ),
                FieldDefinition(
                    name="has_header",
                    label="Has Header Row",
                    type=FieldType.BOOLEAN,
                    default=True,
                    description="First row contains column names",
                ),
                FieldDefinition(
                    name="sheet",
                    label="Sheet Name",
                    placeholder="Sheet1",
                    description="Excel sheet name (for Excel files)",
                    depends_on="format",
                    depends_value="excel",
                ),
            ],
        )


class PostgreSQLConnectionBuilder(ConnectionBuilder):
    """Connection builder for PostgreSQL databases."""

    source_type = SourceType.POSTGRESQL

    def build(self, config: dict[str, Any]) -> str:
        """Build PostgreSQL connection string."""
        host = config.get("host", "localhost")
        port = config.get("port", 5432)
        database = config.get("database", "")
        username = config.get("username", "")
        password = quote_plus(config.get("password", ""))
        schema = config.get("schema")

        conn = f"postgresql://{username}:{password}@{host}:{port}/{database}"

        if schema:
            conn += f"?options=-csearch_path%3D{schema}"

        return conn

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Validate PostgreSQL configuration."""
        errors = []
        required = ["host", "database", "username"]

        for field in required:
            if not config.get(field):
                errors.append(f"{field} is required")

        return errors

    @classmethod
    def get_definition(cls) -> SourceTypeDefinition:
        """Get the source type definition for UI rendering."""
        return SourceTypeDefinition(
            type=SourceType.POSTGRESQL.value,
            name="PostgreSQL",
            description="PostgreSQL database",
            icon="database",
            category="database",
            docs_url="https://www.postgresql.org/docs/",
            fields=[
                FieldDefinition(
                    name="host",
                    label="Host",
                    required=True,
                    placeholder="localhost",
                    description="Database server hostname or IP",
                ),
                FieldDefinition(
                    name="port",
                    label="Port",
                    type=FieldType.NUMBER,
                    default=5432,
                    min_value=1,
                    max_value=65535,
                    description="Database server port",
                ),
                FieldDefinition(
                    name="database",
                    label="Database",
                    required=True,
                    placeholder="mydb",
                    description="Database name",
                ),
                FieldDefinition(
                    name="username",
                    label="Username",
                    required=True,
                    placeholder="postgres",
                    description="Database username",
                ),
                FieldDefinition(
                    name="password",
                    label="Password",
                    type=FieldType.PASSWORD,
                    description="Database password",
                ),
                FieldDefinition(
                    name="schema",
                    label="Schema",
                    placeholder="public",
                    default="public",
                    description="Database schema",
                ),
                FieldDefinition(
                    name="table",
                    label="Table",
                    placeholder="my_table",
                    description="Table name to validate",
                ),
                FieldDefinition(
                    name="ssl_mode",
                    label="SSL Mode",
                    type=FieldType.SELECT,
                    options=[
                        {"value": "disable", "label": "Disable"},
                        {"value": "require", "label": "Require"},
                        {"value": "verify-ca", "label": "Verify CA"},
                        {"value": "verify-full", "label": "Verify Full"},
                    ],
                    default="disable",
                    description="SSL connection mode",
                ),
            ],
        )


class MySQLConnectionBuilder(ConnectionBuilder):
    """Connection builder for MySQL databases."""

    source_type = SourceType.MYSQL

    def build(self, config: dict[str, Any]) -> str:
        """Build MySQL connection string."""
        host = config.get("host", "localhost")
        port = config.get("port", 3306)
        database = config.get("database", "")
        username = config.get("username", "")
        password = quote_plus(config.get("password", ""))

        return f"mysql://{username}:{password}@{host}:{port}/{database}"

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Validate MySQL configuration."""
        errors = []
        required = ["host", "database", "username"]

        for field in required:
            if not config.get(field):
                errors.append(f"{field} is required")

        return errors

    @classmethod
    def get_definition(cls) -> SourceTypeDefinition:
        """Get the source type definition for UI rendering."""
        return SourceTypeDefinition(
            type=SourceType.MYSQL.value,
            name="MySQL",
            description="MySQL database",
            icon="database",
            category="database",
            docs_url="https://dev.mysql.com/doc/",
            fields=[
                FieldDefinition(
                    name="host",
                    label="Host",
                    required=True,
                    placeholder="localhost",
                    description="Database server hostname or IP",
                ),
                FieldDefinition(
                    name="port",
                    label="Port",
                    type=FieldType.NUMBER,
                    default=3306,
                    min_value=1,
                    max_value=65535,
                    description="Database server port",
                ),
                FieldDefinition(
                    name="database",
                    label="Database",
                    required=True,
                    placeholder="mydb",
                    description="Database name",
                ),
                FieldDefinition(
                    name="username",
                    label="Username",
                    required=True,
                    placeholder="root",
                    description="Database username",
                ),
                FieldDefinition(
                    name="password",
                    label="Password",
                    type=FieldType.PASSWORD,
                    description="Database password",
                ),
                FieldDefinition(
                    name="table",
                    label="Table",
                    placeholder="my_table",
                    description="Table name to validate",
                ),
                FieldDefinition(
                    name="ssl",
                    label="Use SSL",
                    type=FieldType.BOOLEAN,
                    default=False,
                    description="Enable SSL connection",
                ),
            ],
        )


class SQLiteConnectionBuilder(ConnectionBuilder):
    """Connection builder for SQLite databases."""

    source_type = SourceType.SQLITE

    def build(self, config: dict[str, Any]) -> str:
        """Build SQLite connection string."""
        path = config.get("path", "")
        return f"sqlite:///{path}"

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Validate SQLite configuration."""
        errors = []
        if not config.get("path"):
            errors.append("path is required")
        return errors

    @classmethod
    def get_definition(cls) -> SourceTypeDefinition:
        """Get the source type definition for UI rendering."""
        return SourceTypeDefinition(
            type=SourceType.SQLITE.value,
            name="SQLite",
            description="SQLite database file",
            icon="database",
            category="database",
            docs_url="https://www.sqlite.org/docs.html",
            fields=[
                FieldDefinition(
                    name="path",
                    label="Database Path",
                    type=FieldType.FILE_PATH,
                    required=True,
                    placeholder="/path/to/database.db",
                    description="Path to the SQLite database file",
                ),
                FieldDefinition(
                    name="table",
                    label="Table",
                    placeholder="my_table",
                    description="Table name to validate",
                ),
            ],
        )


class SnowflakeConnectionBuilder(ConnectionBuilder):
    """Connection builder for Snowflake databases."""

    source_type = SourceType.SNOWFLAKE

    def build(self, config: dict[str, Any]) -> str:
        """Build Snowflake connection string."""
        account = config.get("account", "")
        username = config.get("username", "")
        password = quote_plus(config.get("password", ""))
        database = config.get("database", "")
        schema = config.get("schema", "PUBLIC")
        warehouse = config.get("warehouse", "")
        role = config.get("role")

        conn = (
            f"snowflake://{username}:{password}@{account}"
            f"/{database}/{schema}?warehouse={warehouse}"
        )

        if role:
            conn += f"&role={role}"

        return conn

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Validate Snowflake configuration."""
        errors = []
        required = ["account", "database", "warehouse", "username"]

        for field in required:
            if not config.get(field):
                errors.append(f"{field} is required")

        return errors

    @classmethod
    def get_definition(cls) -> SourceTypeDefinition:
        """Get the source type definition for UI rendering."""
        return SourceTypeDefinition(
            type=SourceType.SNOWFLAKE.value,
            name="Snowflake",
            description="Snowflake data warehouse",
            icon="snowflake",
            category="warehouse",
            docs_url="https://docs.snowflake.com/",
            fields=[
                FieldDefinition(
                    name="account",
                    label="Account",
                    required=True,
                    placeholder="xy12345.us-east-1",
                    description="Snowflake account identifier",
                ),
                FieldDefinition(
                    name="username",
                    label="Username",
                    required=True,
                    description="Snowflake username",
                ),
                FieldDefinition(
                    name="password",
                    label="Password",
                    type=FieldType.PASSWORD,
                    description="Snowflake password",
                ),
                FieldDefinition(
                    name="warehouse",
                    label="Warehouse",
                    required=True,
                    placeholder="COMPUTE_WH",
                    description="Snowflake warehouse name",
                ),
                FieldDefinition(
                    name="database",
                    label="Database",
                    required=True,
                    placeholder="MY_DB",
                    description="Database name",
                ),
                FieldDefinition(
                    name="schema",
                    label="Schema",
                    placeholder="PUBLIC",
                    default="PUBLIC",
                    description="Schema name",
                ),
                FieldDefinition(
                    name="role",
                    label="Role",
                    placeholder="ACCOUNTADMIN",
                    description="Snowflake role (optional)",
                ),
                FieldDefinition(
                    name="table",
                    label="Table",
                    placeholder="MY_TABLE",
                    description="Table name to validate",
                ),
            ],
        )


class BigQueryConnectionBuilder(ConnectionBuilder):
    """Connection builder for BigQuery."""

    source_type = SourceType.BIGQUERY

    def build(self, config: dict[str, Any]) -> str:
        """Build BigQuery connection string."""
        project = config.get("project", "")
        dataset = config.get("dataset", "")

        conn = f"bigquery://{project}"
        if dataset:
            conn += f"/{dataset}"

        return conn

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Validate BigQuery configuration."""
        errors = []

        if not config.get("project"):
            errors.append("project is required")

        return errors

    @classmethod
    def get_definition(cls) -> SourceTypeDefinition:
        """Get the source type definition for UI rendering."""
        return SourceTypeDefinition(
            type=SourceType.BIGQUERY.value,
            name="BigQuery",
            description="Google BigQuery",
            icon="cloud",
            category="warehouse",
            docs_url="https://cloud.google.com/bigquery/docs",
            fields=[
                FieldDefinition(
                    name="project",
                    label="Project ID",
                    required=True,
                    placeholder="my-gcp-project",
                    description="Google Cloud project ID",
                ),
                FieldDefinition(
                    name="dataset",
                    label="Dataset",
                    placeholder="my_dataset",
                    description="BigQuery dataset name",
                ),
                FieldDefinition(
                    name="table",
                    label="Table",
                    placeholder="my_table",
                    description="Table name to validate",
                ),
                FieldDefinition(
                    name="location",
                    label="Location",
                    type=FieldType.SELECT,
                    options=[
                        {"value": "US", "label": "US (multi-region)"},
                        {"value": "EU", "label": "EU (multi-region)"},
                        {"value": "us-central1", "label": "Iowa (us-central1)"},
                        {"value": "us-east1", "label": "S. Carolina (us-east1)"},
                        {"value": "us-west1", "label": "Oregon (us-west1)"},
                        {"value": "europe-west1", "label": "Belgium (europe-west1)"},
                        {"value": "asia-east1", "label": "Taiwan (asia-east1)"},
                        {"value": "asia-northeast1", "label": "Tokyo (asia-northeast1)"},
                    ],
                    default="US",
                    description="Dataset location",
                ),
                FieldDefinition(
                    name="credentials_path",
                    label="Credentials File",
                    type=FieldType.FILE_PATH,
                    placeholder="/path/to/service-account.json",
                    description="Path to service account JSON key file",
                ),
            ],
        )


class RedshiftConnectionBuilder(ConnectionBuilder):
    """Connection builder for Amazon Redshift."""

    source_type = SourceType.REDSHIFT

    def build(self, config: dict[str, Any]) -> str:
        """Build Redshift connection string."""
        host = config.get("host", "")
        port = config.get("port", 5439)
        database = config.get("database", "")
        username = config.get("username", "")
        password = quote_plus(config.get("password", ""))
        schema = config.get("schema", "public")

        conn = f"redshift+psycopg2://{username}:{password}@{host}:{port}/{database}"
        if schema:
            conn += f"?options=-csearch_path%3D{schema}"

        return conn

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Validate Redshift configuration."""
        errors = []
        required = ["host", "database", "username"]

        for field in required:
            if not config.get(field):
                errors.append(f"{field} is required")

        return errors

    @classmethod
    def get_definition(cls) -> SourceTypeDefinition:
        """Get the source type definition for UI rendering."""
        return SourceTypeDefinition(
            type=SourceType.REDSHIFT.value,
            name="Amazon Redshift",
            description="Amazon Redshift data warehouse",
            icon="cloud",
            category="warehouse",
            docs_url="https://docs.aws.amazon.com/redshift/",
            fields=[
                FieldDefinition(
                    name="host",
                    label="Host",
                    required=True,
                    placeholder="my-cluster.xxxxx.region.redshift.amazonaws.com",
                    description="Redshift cluster endpoint",
                ),
                FieldDefinition(
                    name="port",
                    label="Port",
                    type=FieldType.NUMBER,
                    default=5439,
                    min_value=1,
                    max_value=65535,
                    description="Redshift port (default: 5439)",
                ),
                FieldDefinition(
                    name="database",
                    label="Database",
                    required=True,
                    placeholder="dev",
                    description="Database name",
                ),
                FieldDefinition(
                    name="username",
                    label="Username",
                    required=True,
                    placeholder="admin",
                    description="Database username",
                ),
                FieldDefinition(
                    name="password",
                    label="Password",
                    type=FieldType.PASSWORD,
                    description="Database password",
                ),
                FieldDefinition(
                    name="schema",
                    label="Schema",
                    placeholder="public",
                    default="public",
                    description="Database schema",
                ),
                FieldDefinition(
                    name="table",
                    label="Table",
                    placeholder="my_table",
                    description="Table name to validate",
                ),
                FieldDefinition(
                    name="iam_role",
                    label="IAM Role ARN",
                    placeholder="arn:aws:iam::123456789:role/MyRole",
                    description="IAM role for S3 access (optional)",
                ),
            ],
        )


class DatabricksConnectionBuilder(ConnectionBuilder):
    """Connection builder for Databricks."""

    source_type = SourceType.DATABRICKS

    def build(self, config: dict[str, Any]) -> str:
        """Build Databricks connection string."""
        host = config.get("host", "")
        http_path = config.get("http_path", "")
        token = config.get("token", "")
        catalog = config.get("catalog", "")
        schema = config.get("schema", "default")

        # Databricks SQL uses token-based auth
        conn = f"databricks://token:{token}@{host}?http_path={http_path}"
        if catalog:
            conn += f"&catalog={catalog}"
        if schema:
            conn += f"&schema={schema}"

        return conn

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Validate Databricks configuration."""
        errors = []
        required = ["host", "http_path", "token"]

        for field in required:
            if not config.get(field):
                errors.append(f"{field} is required")

        return errors

    @classmethod
    def get_definition(cls) -> SourceTypeDefinition:
        """Get the source type definition for UI rendering."""
        return SourceTypeDefinition(
            type=SourceType.DATABRICKS.value,
            name="Databricks",
            description="Databricks (Unity Catalog / Delta Lake)",
            icon="layers",
            category="bigdata",
            docs_url="https://docs.databricks.com/",
            fields=[
                FieldDefinition(
                    name="host",
                    label="Host",
                    required=True,
                    placeholder="adb-xxxxx.azuredatabricks.net",
                    description="Databricks workspace URL",
                ),
                FieldDefinition(
                    name="http_path",
                    label="HTTP Path",
                    required=True,
                    placeholder="/sql/1.0/warehouses/xxxxx",
                    description="SQL warehouse HTTP path",
                ),
                FieldDefinition(
                    name="token",
                    label="Access Token",
                    type=FieldType.PASSWORD,
                    required=True,
                    description="Databricks personal access token",
                ),
                FieldDefinition(
                    name="catalog",
                    label="Catalog",
                    placeholder="main",
                    description="Unity Catalog name",
                ),
                FieldDefinition(
                    name="schema",
                    label="Schema",
                    placeholder="default",
                    default="default",
                    description="Schema name",
                ),
                FieldDefinition(
                    name="table",
                    label="Table",
                    placeholder="my_table",
                    description="Table name to validate",
                ),
            ],
        )


class OracleConnectionBuilder(ConnectionBuilder):
    """Connection builder for Oracle Database."""

    source_type = SourceType.ORACLE

    def build(self, config: dict[str, Any]) -> str:
        """Build Oracle connection string."""
        host = config.get("host", "localhost")
        port = config.get("port", 1521)
        service_name = config.get("service_name", "")
        sid = config.get("sid", "")
        username = config.get("username", "")
        password = quote_plus(config.get("password", ""))

        # Oracle supports both SID and Service Name
        if service_name:
            return f"oracle+cx_oracle://{username}:{password}@{host}:{port}/?service_name={service_name}"
        elif sid:
            return f"oracle+cx_oracle://{username}:{password}@{host}:{port}/{sid}"
        else:
            return f"oracle+cx_oracle://{username}:{password}@{host}:{port}"

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Validate Oracle configuration."""
        errors = []
        required = ["host", "username"]

        for field in required:
            if not config.get(field):
                errors.append(f"{field} is required")

        # Either service_name or sid should be provided
        if not config.get("service_name") and not config.get("sid"):
            errors.append("Either service_name or sid is required")

        return errors

    @classmethod
    def get_definition(cls) -> SourceTypeDefinition:
        """Get the source type definition for UI rendering."""
        return SourceTypeDefinition(
            type=SourceType.ORACLE.value,
            name="Oracle",
            description="Oracle Database",
            icon="database",
            category="database",
            docs_url="https://docs.oracle.com/en/database/",
            fields=[
                FieldDefinition(
                    name="host",
                    label="Host",
                    required=True,
                    placeholder="localhost",
                    description="Database server hostname or IP",
                ),
                FieldDefinition(
                    name="port",
                    label="Port",
                    type=FieldType.NUMBER,
                    default=1521,
                    min_value=1,
                    max_value=65535,
                    description="Oracle listener port",
                ),
                FieldDefinition(
                    name="service_name",
                    label="Service Name",
                    placeholder="ORCLPDB1",
                    description="Oracle service name (preferred over SID)",
                ),
                FieldDefinition(
                    name="sid",
                    label="SID",
                    placeholder="ORCL",
                    description="Oracle SID (legacy, use Service Name if possible)",
                ),
                FieldDefinition(
                    name="username",
                    label="Username",
                    required=True,
                    placeholder="SYSTEM",
                    description="Database username",
                ),
                FieldDefinition(
                    name="password",
                    label="Password",
                    type=FieldType.PASSWORD,
                    description="Database password",
                ),
                FieldDefinition(
                    name="table",
                    label="Table",
                    placeholder="MY_TABLE",
                    description="Table name to validate",
                ),
            ],
        )


class SQLServerConnectionBuilder(ConnectionBuilder):
    """Connection builder for Microsoft SQL Server."""

    source_type = SourceType.SQLSERVER

    def build(self, config: dict[str, Any]) -> str:
        """Build SQL Server connection string."""
        host = config.get("host", "localhost")
        port = config.get("port", 1433)
        database = config.get("database", "")
        username = config.get("username", "")
        password = quote_plus(config.get("password", ""))
        schema = config.get("schema", "dbo")
        driver = config.get("driver", "ODBC Driver 17 for SQL Server")

        # Build connection string with URL-encoded driver
        encoded_driver = quote_plus(driver)
        conn = f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver={encoded_driver}"

        return conn

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Validate SQL Server configuration."""
        errors = []
        required = ["host", "database", "username"]

        for field in required:
            if not config.get(field):
                errors.append(f"{field} is required")

        return errors

    @classmethod
    def get_definition(cls) -> SourceTypeDefinition:
        """Get the source type definition for UI rendering."""
        return SourceTypeDefinition(
            type=SourceType.SQLSERVER.value,
            name="SQL Server",
            description="Microsoft SQL Server",
            icon="database",
            category="database",
            docs_url="https://docs.microsoft.com/en-us/sql/",
            fields=[
                FieldDefinition(
                    name="host",
                    label="Host",
                    required=True,
                    placeholder="localhost",
                    description="SQL Server hostname or IP",
                ),
                FieldDefinition(
                    name="port",
                    label="Port",
                    type=FieldType.NUMBER,
                    default=1433,
                    min_value=1,
                    max_value=65535,
                    description="SQL Server port",
                ),
                FieldDefinition(
                    name="database",
                    label="Database",
                    required=True,
                    placeholder="mydb",
                    description="Database name",
                ),
                FieldDefinition(
                    name="username",
                    label="Username",
                    required=True,
                    placeholder="sa",
                    description="SQL Server login",
                ),
                FieldDefinition(
                    name="password",
                    label="Password",
                    type=FieldType.PASSWORD,
                    description="SQL Server password",
                ),
                FieldDefinition(
                    name="schema",
                    label="Schema",
                    placeholder="dbo",
                    default="dbo",
                    description="Database schema",
                ),
                FieldDefinition(
                    name="table",
                    label="Table",
                    placeholder="my_table",
                    description="Table name to validate",
                ),
                FieldDefinition(
                    name="driver",
                    label="ODBC Driver",
                    type=FieldType.SELECT,
                    options=[
                        {"value": "ODBC Driver 17 for SQL Server", "label": "ODBC Driver 17"},
                        {"value": "ODBC Driver 18 for SQL Server", "label": "ODBC Driver 18"},
                        {"value": "SQL Server Native Client 11.0", "label": "Native Client 11.0"},
                    ],
                    default="ODBC Driver 17 for SQL Server",
                    description="ODBC driver to use",
                ),
                FieldDefinition(
                    name="trust_server_certificate",
                    label="Trust Server Certificate",
                    type=FieldType.BOOLEAN,
                    default=False,
                    description="Trust the server certificate without validation",
                ),
            ],
        )


class SparkConnectionBuilder(ConnectionBuilder):
    """Connection builder for Apache Spark."""

    source_type = SourceType.SPARK

    def build(self, config: dict[str, Any]) -> str:
        """Build Spark connection string."""
        connection_type = config.get("connection_type", "hive")
        host = config.get("host", "localhost")
        port = config.get("port", 10000)
        database = config.get("database", "default")
        username = config.get("username", "")
        password = quote_plus(config.get("password", ""))

        if connection_type == "hive":
            # Hive JDBC connection
            if username:
                return f"hive://{username}:{password}@{host}:{port}/{database}"
            return f"hive://{host}:{port}/{database}"
        elif connection_type == "spark_thrift":
            # Spark Thrift Server
            return f"hive://{host}:{port}/{database}"
        else:
            # Generic Spark connection
            return f"spark://{host}:{port}/{database}"

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Validate Spark configuration."""
        errors = []
        if not config.get("host"):
            errors.append("host is required")
        return errors

    @classmethod
    def get_definition(cls) -> SourceTypeDefinition:
        """Get the source type definition for UI rendering."""
        return SourceTypeDefinition(
            type=SourceType.SPARK.value,
            name="Apache Spark",
            description="Apache Spark (via Hive/JDBC)",
            icon="zap",
            category="bigdata",
            docs_url="https://spark.apache.org/docs/latest/",
            fields=[
                FieldDefinition(
                    name="connection_type",
                    label="Connection Type",
                    type=FieldType.SELECT,
                    options=[
                        {"value": "hive", "label": "Hive Metastore"},
                        {"value": "spark_thrift", "label": "Spark Thrift Server"},
                    ],
                    default="hive",
                    description="How to connect to Spark",
                ),
                FieldDefinition(
                    name="host",
                    label="Host",
                    required=True,
                    placeholder="localhost",
                    description="Spark/Hive server hostname",
                ),
                FieldDefinition(
                    name="port",
                    label="Port",
                    type=FieldType.NUMBER,
                    default=10000,
                    min_value=1,
                    max_value=65535,
                    description="Hive/Thrift server port",
                ),
                FieldDefinition(
                    name="database",
                    label="Database",
                    placeholder="default",
                    default="default",
                    description="Hive database name",
                ),
                FieldDefinition(
                    name="username",
                    label="Username",
                    description="Username (if authentication enabled)",
                ),
                FieldDefinition(
                    name="password",
                    label="Password",
                    type=FieldType.PASSWORD,
                    description="Password (if authentication enabled)",
                ),
                FieldDefinition(
                    name="table",
                    label="Table",
                    placeholder="my_table",
                    description="Table name to validate",
                ),
            ],
        )


# Registry of connection builders
CONNECTION_BUILDERS: dict[str, type[ConnectionBuilder]] = {
    SourceType.FILE.value: FileConnectionBuilder,
    SourceType.POSTGRESQL.value: PostgreSQLConnectionBuilder,
    SourceType.MYSQL.value: MySQLConnectionBuilder,
    SourceType.SQLITE.value: SQLiteConnectionBuilder,
    SourceType.SNOWFLAKE.value: SnowflakeConnectionBuilder,
    SourceType.BIGQUERY.value: BigQueryConnectionBuilder,
    SourceType.REDSHIFT.value: RedshiftConnectionBuilder,
    SourceType.DATABRICKS.value: DatabricksConnectionBuilder,
    SourceType.ORACLE.value: OracleConnectionBuilder,
    SourceType.SQLSERVER.value: SQLServerConnectionBuilder,
    SourceType.SPARK.value: SparkConnectionBuilder,
}


def get_connection_builder(source_type: str) -> ConnectionBuilder:
    """Get connection builder for source type.

    Args:
        source_type: Type of data source.

    Returns:
        ConnectionBuilder instance.

    Raises:
        ValueError: If source type is not supported.
    """
    builder_class = CONNECTION_BUILDERS.get(source_type)
    if builder_class is None:
        supported = ", ".join(CONNECTION_BUILDERS.keys())
        raise ValueError(f"Unknown source type: {source_type}. Supported: {supported}")

    return builder_class()


def build_connection_string(source_type: str, config: dict[str, Any]) -> str:
    """Build connection string from source type and configuration.

    Args:
        source_type: Type of data source.
        config: Source-specific configuration.

    Returns:
        Connection string.

    Raises:
        ValueError: If source type unknown or config invalid.
    """
    builder = get_connection_builder(source_type)
    errors = builder.validate_config(config)

    if errors:
        raise ValueError(f"Invalid configuration: {'; '.join(errors)}")

    return builder.build(config)


async def test_connection(source_type: str, config: dict[str, Any]) -> dict[str, Any]:
    """Test database connection.

    Args:
        source_type: Type of data source.
        config: Source-specific configuration.

    Returns:
        Dictionary with success status and message or error.
    """
    try:
        # Validate config first
        builder = get_connection_builder(source_type)
        errors = builder.validate_config(config)

        if errors:
            return {
                "success": False,
                "error": f"Configuration errors: {'; '.join(errors)}",
            }

        connection_string = builder.build(config)

        if source_type == "file":
            # For files, just check if path exists
            path = Path(config["path"])
            if not path.exists():
                return {"success": False, "error": f"File not found: {path}"}
            return {
                "success": True,
                "message": f"File exists: {path.name} ({path.stat().st_size:,} bytes)",
            }

        # For databases, use truthound to test connection
        import truthound as th

        # Quick profile to test connection
        result = th.profile(connection_string)
        return {
            "success": True,
            "message": f"Connected! Found {result.column_count} columns, {result.row_count:,} rows",
        }

    except ImportError:
        return {"success": False, "error": "truthound package not available"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_supported_source_types() -> list[dict[str, Any]]:
    """Get list of supported source types with their required fields.

    Returns comprehensive information about each source type including
    field definitions for dynamic form rendering.

    Returns:
        List of source type definitions.
    """
    result = []
    for source_type in SourceType:
        builder_class = CONNECTION_BUILDERS.get(source_type.value)
        if builder_class:
            definition = builder_class.get_definition()
            result.append(definition.to_dict())
    return result


def get_source_type_categories() -> list[dict[str, str]]:
    """Get list of source type categories.

    Returns:
        List of category definitions with name and description.
    """
    return [
        {"value": "file", "label": "Files", "description": "Local file sources"},
        {"value": "database", "label": "Databases", "description": "Relational databases"},
        {"value": "warehouse", "label": "Data Warehouses", "description": "Cloud data warehouses"},
        {"value": "bigdata", "label": "Big Data", "description": "Big data platforms"},
    ]


def get_source_types_by_category() -> dict[str, list[dict[str, Any]]]:
    """Get source types grouped by category.

    Returns:
        Dictionary mapping category to list of source type definitions.
    """
    categories: dict[str, list[dict[str, Any]]] = {
        "file": [],
        "database": [],
        "warehouse": [],
        "bigdata": [],
    }

    for source_type in SourceType:
        builder_class = CONNECTION_BUILDERS.get(source_type.value)
        if builder_class:
            definition = builder_class.get_definition()
            category = definition.category
            if category in categories:
                categories[category].append(definition.to_dict())

    return categories
