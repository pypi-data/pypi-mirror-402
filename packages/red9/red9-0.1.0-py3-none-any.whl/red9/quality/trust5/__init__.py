"""TRUST 5 Quality Framework.

Implements the moai-adk TRUST 5 quality framework:
- T (Tested): Coverage >= 75%, test quality
- R (Readable): File/function size, complexity
- U (Unified): Linting, type hints, consistency
- S (Secured): Security scanning via AST-grep
- T (Trackable): Commit quality, changelog

Usage:
    from red9.quality.trust5 import TRUST5Validator

    validator = TRUST5Validator(project_root)
    result = validator.validate(files_modified)

    if result.passed:
        print("Quality gates passed!")
    else:
        print(f"Failed dimensions: {result.failed_dimensions}")
"""

from red9.quality.trust5.validator import (
    DimensionResult,
    TRUST5Config,
    TRUST5Result,
    TRUST5Validator,
)

__all__ = [
    "TRUST5Validator",
    "TRUST5Result",
    "TRUST5Config",
    "DimensionResult",
]
