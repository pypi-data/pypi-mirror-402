"""Validation endpoints.

This module provides endpoints for validating values and registry integrity.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_store
from ..models.api_models import (
    ValidationIssue,
    ValidationReport,
    ValueValidationRequest,
    ValueValidationResult,
)
from ..stores.base import VocabularyStore

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/validate/value",
    response_model=ValueValidationResult,
    summary="Validate a value",
    description=(
        "Validates whether a given value is acceptable for a specific term "
        "in a vocabulary. Returns structured validation results with reasons."
    ),
)
def validate_value(
    request: ValueValidationRequest,
    store: VocabularyStore = Depends(get_store),
) -> ValueValidationResult:
    """Validate a value against a vocabulary term.

    Args:
        request: Validation request containing vocabulary_id, term_key, and value.
        store: The vocabulary store dependency.

    Returns:
        ValueValidationResult: Structured validation result.
    """
    try:
        # Get the term
        term = store.get_term(request.vocabulary_id, request.term_key)

        # Basic validation logic
        # In a real implementation, this would use the validator from
        # jps-controlled-vocabularies-utils
        is_valid = False
        normalized_value = request.value
        reasons: List[str] = []
        allowed_values = None
        pattern = None

        # Extract validation rules from term metadata
        metadata = term.metadata or {}
        allowed_values_from_meta = metadata.get("allowed_values")
        pattern_from_meta = metadata.get("pattern")

        if allowed_values_from_meta:
            allowed_values = allowed_values_from_meta
            if request.value in allowed_values:
                is_valid = True
                reasons.append("Value is in the list of allowed values")
            else:
                reasons.append(
                    f"Value '{request.value}' is not in the list of allowed values"
                )

        elif pattern_from_meta:
            import re

            pattern = pattern_from_meta
            if re.match(pattern, str(request.value)):
                is_valid = True
                reasons.append("Value matches the required pattern")
            else:
                reasons.append(
                    f"Value '{request.value}' does not match the required pattern"
                )

        else:
            # No validation rules specified, accept any value
            is_valid = True
            reasons.append("No validation constraints defined for this term")

        return ValueValidationResult(
            is_valid=is_valid,
            normalized_value=normalized_value,
            reasons=reasons,
            allowed_values=allowed_values,
            pattern=pattern,
        )

    except KeyError as e:
        logger.warning(
            f"Validation failed: term not found - {request.vocabulary_id}/{request.term_key}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "TERM_NOT_FOUND",
                "message": str(e),
                "details": {
                    "vocabulary_id": request.vocabulary_id,
                    "term_key": request.term_key,
                },
            },
        )

    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "Value validation failed",
                "details": {"error": str(e)},
            },
        )


@router.post(
    "/validate/registry",
    response_model=ValidationReport,
    summary="Validate registry",
    description=(
        "Validates the integrity and consistency of the loaded vocabulary registry. "
        "Checks for structural issues, missing required fields, and other problems."
    ),
)
def validate_registry(
    store: VocabularyStore = Depends(get_store),
) -> ValidationReport:
    """Validate the currently loaded vocabulary registry.

    Args:
        store: The vocabulary store dependency.

    Returns:
        ValidationReport: Comprehensive validation report.
    """
    try:
        registry = store.get_registry()
        issues: List[ValidationIssue] = []
        total_vocabularies = len(registry)
        total_terms = 0

        # Validate each vocabulary
        for vocab_id, vocab_data in registry.items():
            # Check required fields
            if not vocab_data.get("title"):
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        vocabulary_id=vocab_id,
                        message=f"Vocabulary '{vocab_id}' is missing a title",
                        details={},
                    )
                )

            if not vocab_data.get("schema_version"):
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        vocabulary_id=vocab_id,
                        message=f"Vocabulary '{vocab_id}' is missing schema_version",
                        details={},
                    )
                )

            # Validate terms
            terms = vocab_data.get("terms", [])
            total_terms += len(terms)

            term_keys_seen = set()
            for idx, term in enumerate(terms):
                # Check required term fields
                if not term.get("key") and not term.get("name"):
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            vocabulary_id=vocab_id,
                            message=f"Term at index {idx} is missing both 'key' and 'name'",
                            details={"term_index": idx},
                        )
                    )

                # Check for duplicate keys
                term_key = term.get("key", term.get("name"))
                if term_key in term_keys_seen:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            vocabulary_id=vocab_id,
                            term_key=term_key,
                            message=f"Duplicate term key: '{term_key}'",
                            details={},
                        )
                    )
                term_keys_seen.add(term_key)

        # Determine overall validity
        has_errors = any(issue.severity == "error" for issue in issues)
        is_valid = not has_errors

        summary = (
            f"Registry is valid with {len(issues)} issue(s)"
            if is_valid
            else f"Registry has {len([i for i in issues if i.severity == 'error'])} error(s)"
        )

        return ValidationReport(
            is_valid=is_valid,
            total_vocabularies=total_vocabularies,
            total_terms=total_terms,
            issues=issues,
            summary=summary,
        )

    except Exception as e:
        logger.error(f"Registry validation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "Registry validation failed",
                "details": {"error": str(e)},
            },
        )
