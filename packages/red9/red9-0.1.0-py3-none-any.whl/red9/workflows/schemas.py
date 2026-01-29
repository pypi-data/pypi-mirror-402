"""Output validation schemas for RED9 workflow stages.

Leverages Stabilize's OutputVerifier capability to validate task outputs
against JSON schemas before downstream consumption.

This ensures:
1. Required fields are present
2. Data types are correct
3. Minimum constraints are met (e.g., spec content has actual content)
"""

from __future__ import annotations

from typing import Any

# =============================================================================
# SPEC AGENT OUTPUT SCHEMA
# =============================================================================

SPEC_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["spec_content", "acceptance_criteria"],
    "properties": {
        "spec_content": {
            "type": "string",
            "minLength": 100,
            "description": "EARS-format specification content",
        },
        "acceptance_criteria": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string"},
            "description": "List of acceptance criteria",
        },
        "test_scenarios": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of test scenarios (optional)",
        },
        "files_to_modify": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Files that will be modified",
        },
        "files_to_create": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Files that will be created",
        },
    },
}


# =============================================================================
# DDD AGENT OUTPUT SCHEMA
# =============================================================================

DDD_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["success"],
    "properties": {
        "success": {
            "type": "boolean",
            "description": "Whether implementation succeeded",
        },
        "files_modified": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of modified file paths",
        },
        "files_created": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of created file paths",
        },
        "error": {
            "type": ["string", "null"],
            "description": "Error message if failed",
        },
        "summary": {
            "type": "string",
            "description": "Summary of changes made",
        },
    },
}


# =============================================================================
# EXPLORATION OUTPUT SCHEMA
# =============================================================================

EXPLORATION_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["essential_files"],
    "properties": {
        "essential_files": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["path", "reason"],
                "properties": {
                    "path": {"type": "string"},
                    "reason": {"type": "string"},
                },
            },
            "description": "List of essential files with reasons",
        },
        "architecture_summary": {
            "type": "string",
            "description": "Summary of codebase architecture",
        },
        "patterns_found": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Design patterns found in codebase",
        },
        "similar_implementations": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Similar features/implementations found",
        },
    },
}


# =============================================================================
# ARCHITECTURE OUTPUT SCHEMA
# =============================================================================

ARCHITECTURE_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["approach", "rationale"],
    "properties": {
        "approach": {
            "type": "string",
            "enum": ["minimal", "clean", "pragmatic"],
            "description": "Recommended approach",
        },
        "rationale": {
            "type": "string",
            "minLength": 50,
            "description": "Explanation of why this approach",
        },
        "files_to_modify": {
            "type": "array",
            "items": {"type": "string"},
        },
        "files_to_create": {
            "type": "array",
            "items": {"type": "string"},
        },
        "estimated_changes": {
            "type": "string",
            "enum": ["few", "moderate", "extensive"],
        },
        "risks": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Potential risks with this approach",
        },
    },
}


# =============================================================================
# REVIEW OUTPUT SCHEMA
# =============================================================================

REVIEW_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["issues"],
    "properties": {
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["description", "location", "confidence", "severity"],
                "properties": {
                    "description": {"type": "string"},
                    "location": {"type": "string"},
                    "confidence": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Confidence score 0-100",
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                    },
                    "suggestion": {"type": "string"},
                },
            },
        },
        "summary": {
            "type": "string",
            "description": "Overall review summary",
        },
        "approved": {
            "type": "boolean",
            "description": "Whether code is approved",
        },
    },
}


# =============================================================================
# CONTEXT AGENT OUTPUT SCHEMA
# =============================================================================

CONTEXT_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["project_type"],
    "properties": {
        "project_type": {
            "type": "string",
            "description": "Type of project (python, node, rust, etc.)",
        },
        "frameworks": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Frameworks detected in the project",
        },
        "entry_points": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Main entry points of the application",
        },
        "test_framework": {
            "type": "string",
            "description": "Testing framework used",
        },
        "build_system": {
            "type": "string",
            "description": "Build system (pip, npm, cargo, etc.)",
        },
        "key_directories": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Important directories in the project",
        },
    },
}


# =============================================================================
# VALIDATION HELPERS
# =============================================================================


def validate_output(output: dict[str, Any], schema: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate output against a JSON schema.

    This is a simple validation that doesn't require external dependencies.
    For full JSON Schema validation, use jsonschema library.

    Args:
        output: Output dictionary to validate.
        schema: JSON schema to validate against.

    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors: list[str] = []

    # Check required fields
    required = schema.get("required", [])
    for field in required:
        if field not in output:
            errors.append(f"Missing required field: {field}")

    # Check property types and constraints
    properties = schema.get("properties", {})
    for field, field_schema in properties.items():
        if field not in output:
            continue

        value = output[field]
        field_type = field_schema.get("type")

        # Type validation
        if field_type == "string" and not isinstance(value, str):
            errors.append(f"Field '{field}' must be a string")
        elif field_type == "boolean" and not isinstance(value, bool):
            errors.append(f"Field '{field}' must be a boolean")
        elif field_type == "integer" and not isinstance(value, int):
            errors.append(f"Field '{field}' must be an integer")
        elif field_type == "array" and not isinstance(value, list):
            errors.append(f"Field '{field}' must be an array")
        elif field_type == "object" and not isinstance(value, dict):
            errors.append(f"Field '{field}' must be an object")

        # String constraints
        if field_type == "string" and isinstance(value, str):
            min_length = field_schema.get("minLength", 0)
            if len(value) < min_length:
                errors.append(f"Field '{field}' must be at least {min_length} characters")

        # Array constraints
        if field_type == "array" and isinstance(value, list):
            min_items = field_schema.get("minItems", 0)
            if len(value) < min_items:
                errors.append(f"Field '{field}' must have at least {min_items} items")

        # Integer constraints
        if field_type == "integer" and isinstance(value, int):
            minimum = field_schema.get("minimum")
            maximum = field_schema.get("maximum")
            if minimum is not None and value < minimum:
                errors.append(f"Field '{field}' must be >= {minimum}")
            if maximum is not None and value > maximum:
                errors.append(f"Field '{field}' must be <= {maximum}")

        # Enum constraints
        enum_values = field_schema.get("enum")
        if enum_values and value not in enum_values:
            errors.append(f"Field '{field}' must be one of: {enum_values}")

    return len(errors) == 0, errors


def filter_high_confidence_issues(
    issues: list[dict[str, Any]],
    min_confidence: int = 80,
) -> list[dict[str, Any]]:
    """Filter review issues to only include high-confidence ones.

    This implements the confidence-based filtering from Claude Code's
    review system - only surface issues with confidence >= threshold.

    Args:
        issues: List of issue dictionaries with confidence scores.
        min_confidence: Minimum confidence threshold (default 80).

    Returns:
        Filtered list of issues.
    """
    return [issue for issue in issues if issue.get("confidence", 0) >= min_confidence]
