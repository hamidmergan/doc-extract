class ExtractError(Exception):
    """Base class of all errors in this package."""


class ConfigError(ExtractError):
    """A setting is missing or a value is invalid."""


class LimitError(ExtractError):
    """A limit was exceeded."""


class UnsupportedFileError(ExtractError):
    """The file type is not supported or the file cannot be read."""


class ModelError(ExtractError):
    """The model server did not answer, or the answer was unusable."""
