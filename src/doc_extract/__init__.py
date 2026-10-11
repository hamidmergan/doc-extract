from .core import Result, extract, extract_many
from .errors import (
    ConfigError,
    ExtractError,
    LimitError,
    ModelError,
    UnsupportedFileError,
)

__version__ = "0.1.0"

__all__ = [
    "extract",
    "extract_many",
    "Result",
    "ExtractError",
    "ConfigError",
    "LimitError",
    "ModelError",
    "UnsupportedFileError",
    "__version__",
]
