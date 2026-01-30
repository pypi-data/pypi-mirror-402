"""Built-in prompt type definitions for Switch."""

from enum import Enum
from pathlib import Path

from .sdp_language import SDPLanguage
from .target_type import TargetType


class PromptCategory(str, Enum):
    """Prompt categories matching directory structure"""

    SQL_TO_DATABRICKS_PYTHON_NOTEBOOK = "sql_to_databricks_python_notebook"
    DATABRICKS_NOTEBOOK_TO_DATABRICKS_NOTEBOOK = "databricks_notebook_to_databricks_notebook"
    CODE_TO_DATABRICKS_PYTHON_NOTEBOOK = "code_to_databricks_python_notebook"
    WORKFLOW_TO_DATABRICKS_JOBS = "workflow_to_databricks_jobs"
    ETL_TO_LAKEFLOW_SDP = "etl_to_lakeflow_sdp"


class BuiltinPrompt(str, Enum):
    """Built-in prompts with automatic categorization"""

    # SQL dialects
    MSSQL = "mssql"
    MYSQL = "mysql"
    NETEZZA = "netezza"
    ORACLE = "oracle"
    POSTGRESQL = "postgresql"
    REDSHIFT = "redshift"
    SNOWFLAKE = "snowflake"
    SYNAPSE = "synapse"
    TERADATA = "teradata"

    # Databricks notebook conversions
    PYTHON_TO_SQL = "python_to_sql"

    # Generic conversions
    PYTHON = "python"
    SCALA = "scala"
    AIRFLOW = "airflow"

    # SDP Conversions
    PYSPARK = "pyspark"
    UNKNOWN_ETL = "unknown_etl"

    @property
    def category(self) -> PromptCategory:
        """Auto-classify template category"""
        sql_dialects = {
            self.MSSQL,
            self.MYSQL,
            self.NETEZZA,
            self.ORACLE,
            self.POSTGRESQL,
            self.REDSHIFT,
            self.SNOWFLAKE,
            self.SYNAPSE,
            self.TERADATA,
        }
        etl_dialects = {
            self.PYSPARK,
            self.UNKNOWN_ETL,
        }
        if self in sql_dialects:
            return PromptCategory.SQL_TO_DATABRICKS_PYTHON_NOTEBOOK
        if self == self.PYTHON_TO_SQL:
            return PromptCategory.DATABRICKS_NOTEBOOK_TO_DATABRICKS_NOTEBOOK
        if self in {self.PYTHON, self.SCALA}:
            return PromptCategory.CODE_TO_DATABRICKS_PYTHON_NOTEBOOK
        if self == self.AIRFLOW:
            return PromptCategory.WORKFLOW_TO_DATABRICKS_JOBS
        if self in etl_dialects:
            return PromptCategory.ETL_TO_LAKEFLOW_SDP
        raise ValueError(f"Unknown prompt category: {self.value}")

    # Properties
    @property
    def path(self) -> Path:
        """Complete absolute path to built-in prompt file"""
        return self._base_dir() / "resources" / "builtin_prompts" / self._relative_path

    @property
    def _relative_path(self) -> Path:
        """Relative path from builtin_prompts/"""
        # Map synapse to mssql.yml to share the same prompt file
        if self.value == "synapse":
            return Path(self.category.value) / "mssql.yml"
        return Path(self.category.value) / f"{self.value}.yml"

    # Instance methods
    def exists(self) -> bool:
        """Check if built-in prompt file exists"""
        return self.path.exists()

    # Class methods
    @classmethod
    def from_name(cls, name: str) -> 'BuiltinPrompt':
        """Type-safe built-in prompt creation with clear errors"""
        try:
            return cls(name)
        except ValueError as e:
            supported = ', '.join(cls.get_supported_prompts())
            raise ValueError(f"Unsupported built-in prompt '{name}'. Supported: {supported}") from e

    @classmethod
    def get_supported_prompts(cls) -> list[str]:
        """All supported built-in prompts"""
        return [prompt.value for prompt in cls]

    @classmethod
    def get_common_instruction_path(cls, target_type: TargetType = None, sdp_language: SDPLanguage = None) -> Path:
        """Get path to common instruction YAML

        Args:
            target_type: Target output type (NOTEBOOK, FILE, SDP)
            sdp_language: Language for SDP output (PYTHON, SQL). Required when target_type is SDP.

        Returns:
            Path to the appropriate common instruction YAML file.
        """
        yaml_file_name = "sql_to_databricks_notebook_common_python.yml"
        if target_type is not None and target_type == TargetType.SDP:
            yaml_file_name = cls._get_sdp_instruction_yaml_name(sdp_language)

        return cls._base_dir() / "resources" / "builtin_prompts" / "common" / yaml_file_name

    # Static methods
    @staticmethod
    def _base_dir() -> Path:
        """Base directory"""
        return Path(__file__).parent.parent.parent.parent

    @classmethod
    def _get_sdp_instruction_yaml_name(cls, sdp_language: SDPLanguage) -> str:
        """Get file name of the common instruction YAML for Spark Declarative Pipeline

        Args:
            sdp_language: Language for SDP output (PYTHON, SQL)

        Returns:
            Name to the appropriate SDP instruction YAML file.

        Raises:
            ValueError: If sdp_language is None or invalid.
        """
        if sdp_language is None:
            raise ValueError("sdp_language is required when target_type is SDP")

        if sdp_language == SDPLanguage.PYTHON:
            yaml_file_name = "convert_to_spark_declarative_pipeline_python.yml"
        else:
            yaml_file_name = "convert_to_spark_declarative_pipeline_sql.yml"

        return yaml_file_name
