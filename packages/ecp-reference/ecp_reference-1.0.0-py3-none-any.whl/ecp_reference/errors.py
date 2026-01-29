from __future__ import annotations

class ECPError(Exception):
    """Base error type for ECP PoC."""

class SkillFormatError(ECPError):
    """Raised when SKILL.md or directory layout is invalid."""

class ManifestValidationError(ECPError):
    """Raised when EXPERT.yaml fails schema validation."""

class PolicyValidationError(ECPError):
    """Raised when policy.json fails schema validation."""

class EvalValidationError(ECPError):
    """Raised when an eval suite fails schema validation."""

class BuildError(ECPError):
    """Raised when building or updating context artifacts fails."""

class QueryError(ECPError):
    """Raised when an expert query cannot be executed."""

class RefreshError(ECPError):
    """Raised when refresh cannot be executed."""
