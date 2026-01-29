class FormConfigError(Exception):
    """Base error for all form config failures."""
class FormConfigImplementationError(FormConfigError):
    """Raised for internal bugs or broken invariants in the implementation."""
class FormConfigUserError(FormConfigError):
    """Raised for invalid user-supplied inputs."""
class FormConfigMetadataError(FormConfigUserError):
    """Raised for invalid or ambiguous metadata passed into schema generation."""
class FormConfigSchemaError(FormConfigImplementationError):
    """Raised when a schema cannot be built due to unsupported or inconsistent definitions."""
class FormConfigTypeResolutionError(FormConfigSchemaError):
    """Raised when an alias/type cannot be resolved or is unsupported."""
class FormConfigParseError(FormConfigUserError):
    """Raised when input data cannot be parsed into the requested type."""
class FormConfigValidationError(FormConfigUserError):
    """Raised when parsed data violates semantic constraints (missing keys, extra keys, invariants)."""
class FormWorkflowError(FormConfigError):
    """Raised when there is an unspecified error with the workflow."""
class FormWorkflowImplementationError(FormConfigError):
    """Raised when there is an unspecified implementation error in the workflow."""
class FormWorkflowFactAlreadyWritten(FormConfigError):
    """Raised when there is an unspecified implementation error in the workflow."""
class FactError(FormWorkflowError):
    """Raised when there is a problem with a fact."""
class MissingFactError(FactError):
    """Raised when a required fact is missing."""
class InvalidFactError(FactError):
    """Raised when a required fact is missing."""
class StepExpiredError(FormWorkflowError):
    """Raised when operating on an expired session."""
class InvalidWorkflowError(FormWorkflowError):
    """Raised when the workflow configuration or state is inconsistent."""
