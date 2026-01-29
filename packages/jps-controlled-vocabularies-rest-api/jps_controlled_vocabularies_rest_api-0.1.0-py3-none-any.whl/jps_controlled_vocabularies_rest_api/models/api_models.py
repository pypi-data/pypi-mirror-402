"""API request and response models.

This module defines Pydantic models for API requests and responses.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VocabularySummary(BaseModel):
    """Summary information about a vocabulary.

    Used in list endpoints to provide basic vocabulary metadata.
    """

    vocabulary_id: str = Field(..., description="Unique identifier for the vocabulary")
    schema_version: str = Field(..., description="Schema version")
    title: str = Field(..., description="Human-readable title")
    description: Optional[str] = Field(None, description="Description of the vocabulary")
    term_count: int = Field(..., description="Number of terms in this vocabulary")


class Term(BaseModel):
    """Representation of a single term.

    Contains all metadata for a vocabulary term.
    """

    key: str = Field(..., description="Unique identifier for the term within the vocabulary")
    name: str = Field(..., description="Display name of the term")
    description: Optional[str] = Field(None, description="Description of the term")
    vocabulary_id: Optional[str] = Field(
        None, description="ID of the vocabulary this term belongs to"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )


class VocabularyDetail(BaseModel):
    """Detailed vocabulary information including terms.

    Contains complete vocabulary metadata and optionally the full list of terms.
    """

    vocabulary_id: str = Field(..., description="Unique identifier for the vocabulary")
    schema_version: str = Field(..., description="Schema version")
    title: str = Field(..., description="Human-readable title")
    description: Optional[str] = Field(None, description="Description of the vocabulary")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )
    term_count: int = Field(..., description="Number of terms in this vocabulary")
    terms: Optional[List[Term]] = Field(
        None, description="List of terms (optional, may be paginated separately)"
    )


class ValueValidationRequest(BaseModel):
    """Request to validate a value against a vocabulary term.

    Used in the value validation endpoint.
    """

    vocabulary_id: str = Field(..., description="Vocabulary identifier")
    term_key: str = Field(..., description="Term key within the vocabulary")
    value: Any = Field(..., description="Value to validate")


class ValueValidationResult(BaseModel):
    """Result of value validation.

    Contains validation status, normalized value, and explanations.
    """

    is_valid: bool = Field(..., description="Whether the value is valid")
    normalized_value: Optional[Any] = Field(
        None, description="Normalized form of the value"
    )
    reasons: List[str] = Field(
        default_factory=list, description="Reasons for validation failure or notes"
    )
    allowed_values: Optional[List[Any]] = Field(
        None, description="List of allowed values if applicable"
    )
    pattern: Optional[str] = Field(None, description="Pattern if applicable")


class ValidationIssue(BaseModel):
    """A single validation issue.

    Describes a specific problem found during registry validation.
    """

    severity: str = Field(..., description="Severity level: error, warning, info")
    vocabulary_id: Optional[str] = Field(None, description="Related vocabulary ID")
    term_key: Optional[str] = Field(None, description="Related term key")
    message: str = Field(..., description="Description of the issue")
    details: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional details"
    )


class ValidationReport(BaseModel):
    """Registry validation report.

    Contains overall status and list of validation issues.
    """

    is_valid: bool = Field(..., description="Whether the registry is valid")
    total_vocabularies: int = Field(..., description="Total number of vocabularies")
    total_terms: int = Field(..., description="Total number of terms")
    issues: List[ValidationIssue] = Field(
        default_factory=list, description="List of validation issues"
    )
    summary: Optional[str] = Field(None, description="Summary message")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Health status")


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    status: str = Field(..., description="Readiness status")
    backend: str = Field(..., description="Backend type")
    registry_loaded: bool = Field(..., description="Whether registry is loaded")
    vocabulary_count: int = Field(..., description="Number of loaded vocabularies")
    warnings: Optional[List[str]] = Field(
        default_factory=list, description="Any warnings or issues"
    )


class ErrorResponse(BaseModel):
    """Standardized error response."""

    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional error details"
    )
    request_id: Optional[str] = Field(None, description="Request identifier for tracing")
