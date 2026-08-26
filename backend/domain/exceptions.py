"""
VAT Enterprise Domain Typed Exceptions
"""


class VATDomainException(Exception):
    """Base exception for all VAT domain failures."""
    def __init__(self, message: str, details: dict = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class TelemetryParsingError(VATDomainException):
    """Raised when raw telemetry cannot be tokenized or normalized."""
    pass


class KnowledgeRetrievalError(VATDomainException):
    """Raised when hybrid vector search fails and no fallback is available."""
    pass


class RunbookSynthesisError(VATDomainException):
    """Raised when 4-stage remediation runbook cannot be synthesized."""
    pass


class RepositoryConnectionError(VATDomainException):
    """Raised when persistence layer is unreachable."""
    pass
