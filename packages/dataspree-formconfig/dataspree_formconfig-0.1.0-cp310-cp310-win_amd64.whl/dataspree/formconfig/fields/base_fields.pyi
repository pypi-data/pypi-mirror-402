from _typeshed import Incomplete
from dataspree.formconfig.data.base import BaseContent
from pydantic import BaseModel
from typing import Any

class BaseField(BaseModel):
    """Base class for all UI field types with metadata and recursive behavior.

    Attributes:
        name: Internal name of the field, usually snake_case. Determines the output structure.
        description: Optional description text for UI display.
        display_name: Optional human-readable label; auto-generated from name if omitted.
        type: Type identifier for the frontend. Inferred from the class name if omitted.
    """
    model_config: Incomplete
    name: str
    description: str | None
    display_name: str | None
    type: str | None
    def model_post_init(self, /, __context: Any) -> None:
        """Default post init; fill in defaults for display name and type if not specified."""
    @classmethod
    def default_type(cls) -> str:
        """Derive default type string from class name."""
    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Serialize this field, its content and all subfields."""
    def get_children(self) -> list[BaseField]:
        """Return the list of active subfields."""
    @staticmethod
    def capitalize(content: str) -> str:
        """Capitalize and prettify snake_case string into Title Case."""

class FieldString(BaseField):
    """Basic string field.

    Attributes:
        default: Default / assigned value.
    """
    default: str | None

class FieldPassword(BaseField):
    """Basic password field.

    Attributes:
        default: Default / assigned value.
    """
    default: str | None

class FieldTextArea(BaseField):
    """Basic text area field.

    Attributes:
        default: Default / assigned value.
    """
    default: str | None

class FieldInteger(BaseField):
    """Basic integer field with optional bounds.

    Attributes:
        default: Default / assigned value.
        min: Optional minimum allowed value.
        max: Optional maximum allowed value.
    """
    default: int | None
    min: int | None
    max: int | None

class FieldFloat(BaseField):
    """Basic float field with optional bounds.

    Attributes:
        default: Default / assigned value.
        min: Optional minimum allowed value.
        max: Optional maximum allowed value.
    """
    default: float | None
    min: float | None
    max: float | None

class FieldBool(BaseField):
    """Basic bool field.

    Attributes:
        default: Default / assigned value.
    """
    default: bool | None

class FieldJsonText(BaseField):
    """Basic JSON field.

    Attributes:
        default: Default / assigned value.
    """
    default: dict[str, Any]

class FieldEnum(BaseField):
    """Basic enum field with selectable options.

    Attributes:
        options: List of available options, each with at least a 'value' key.
        default: Currently selected option value or None.
    """
    options: list[dict[str, str | int]]
    default: str | int | None
    def model_post_init(self, /, __context: Any) -> None:
        """Fill in default if no valid value specified and call the base post init."""

class FieldNested(BaseField):
    """Base class for fields that contain one or more nested subfields.

    Attributes:
        fields: Nested child fields contained in this field.
    """
    fields: list[BaseField]
    def get_children(self) -> list[BaseField]:
        """Return the list of active subfields."""
    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Recursively serialize this field, its content and all subfields."""

class FieldData(FieldNested):
    """Group field that contains a list of subfields."""

class FieldList(FieldNested):
    """List field containing repeated items.

    Attributes:
        default: Values currently contained in the list, for example
            [1, 2, 3] or [{'content_1': 1, 'content_2': 'b'}].
    """
    default: list[dict[Any, Any] | BaseContent | int | str | float | bool]

class FieldUnion(FieldNested):
    """Union field selecting exactly one child variant.

    Attributes:
        default: Name of the active child field, or None if none is selected.
    """
    default: str | None
    def get_children(self) -> list[BaseField]:
        """Return the list of active subfields."""

class FieldOptional(FieldNested):
    """Optional field that can enable or disable its children.

    Attributes:
        default: True when the nested fields are enabled, False otherwise.
    """
    default: bool
    def get_children(self) -> list[BaseField]:
        """Return the list of active subfields."""
FormField = FieldString | FieldPassword | FieldTextArea | FieldInteger | FieldFloat | FieldBool | FieldJsonText | FieldEnum | FieldList | FieldData | FieldUnion | FieldOptional
