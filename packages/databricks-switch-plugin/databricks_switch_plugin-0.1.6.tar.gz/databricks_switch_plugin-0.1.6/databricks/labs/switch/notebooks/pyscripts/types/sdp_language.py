"""SDP (Spark Declarative Pipeline) language type definitions for Switch conversion."""

from enum import Enum

from ._base import CaseInsensitiveEnumMixin


class SDPLanguage(CaseInsensitiveEnumMixin, str, Enum):
    """SDP language types for Switch conversion

    This enum defines the supported languages for Spark Declarative Pipeline output.
    Used in conjunction with TargetType.SDP to specify the output language.
    """

    PYTHON = "python"
    SQL = "sql"
