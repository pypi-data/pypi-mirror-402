class TSpecError(Exception):
    """Base error."""

class SpecVersionError(TSpecError):
    """Spec version negotiation or support-window error."""

class ParseError(TSpecError):
    """Parsing errors."""

class ValidationError(TSpecError):
    """Schema/structure validation errors."""

class ExecutionError(TSpecError):
    """Runtime execution errors."""

class SkipCaseError(ExecutionError):
    """Abort current case as skipped (used by on_error=skip_case)."""

class StepTimeoutError(ExecutionError):
    """Step exceeded hard timeout (runner-side)."""

