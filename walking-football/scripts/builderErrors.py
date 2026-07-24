"""Exceptions raised by the session builder."""


class SessionBuilderError(Exception):
    """Base class for expected session builder failures."""


class SessionDataError(SessionBuilderError):
    """Raised when a YAML session definition is invalid."""


class SessionTemplateError(SessionBuilderError):
    """Raised when an ODT template is invalid or cannot be rendered."""
