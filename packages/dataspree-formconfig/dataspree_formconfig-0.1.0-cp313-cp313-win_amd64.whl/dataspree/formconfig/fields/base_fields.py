"""Defines the UI field schema (BaseField and its subclasses).

Primitive fields (string, int, float, bool, etc.) and composite fields (group, list, union, optional) are all Pydantic
models with defaults, metadata, and recursive model_dump.

This is the structure that is serialized and sent to the frontend as configuration.
"""

# TODO: (!) Workflow inference vs insights
#
#       (!) Verteilung der aufgaben (erneut aufrufen)
#
#       (!) Backend definiert visualisierung im frontend
#           - Display name (!) im frontend konfigurieren
#           - description im frontend konfigurieren
#           - bei inference anfrangen
#           - erstmal drin lassen.


# TODO: Request for data     vs
#       (1) ImageField (subtype: PNG) -> reload default, default als quelle (producer)
#       (!) RoiField (auch das mit default queelle producer)

# TODO: weg: HTTP calls
#       - start so belassen (perform action)
#       / action / perform
#       globale action id

from __future__ import annotations

import re

from collections.abc import Callable
from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Any, cast

from dataspree.formconfig.data.base import BaseContent


class BaseField(BaseModel):
    """Base class for all UI field types with metadata and recursive behavior.

    Attributes:
        name: Internal name of the field, usually snake_case. Determines the output structure.
        description: Optional description text for UI display.
        display_name: Optional human-readable label; auto-generated from name if omitted.
        type: Type identifier for the frontend. Inferred from the class name if omitted.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True, ignored_types=cast(tuple[type, ...], (Callable,)), extra='forbid'
    )

    name: str
    description: str | None = None
    display_name: str | None = None
    type: str | None = None

    def model_post_init(self, __context: Any) -> None:
        """Default post init; fill in defaults for display name and type if not specified."""
        if self.display_name is None:
            self.display_name = self.capitalize(self.name)
        if self.type is None:
            self.type = self.default_type()

    @classmethod
    def default_type(cls) -> str:
        """Derive default type string from class name."""
        return re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Serialize this field, its content and all subfields."""
        return super().model_dump(
            *args, exclude_unset=False, exclude_defaults=False, exclude_none=False, by_alias=False, **kwargs
        )

    def get_children(self) -> list[BaseField]:
        """Return the list of active subfields."""
        return []

    @staticmethod
    def capitalize(content: str) -> str:
        """Capitalize and prettify snake_case string into Title Case."""
        return ' '.join(x.capitalize() for x in content.split('_'))


#
# Primitive fields (fields without subfields).
#

# name
# data type secret (ist immer string), string


class FieldString(BaseField):
    """Basic string field.

    Attributes:
        default: Default / assigned value.
    """

    default: str | None = ''


class FieldPassword(BaseField):
    """Basic password field.

    Attributes:
        default: Default / assigned value.
    """

    default: str | None = ''


class FieldTextArea(BaseField):
    """Basic text area field.

    Attributes:
        default: Default / assigned value.
    """

    default: str | None = ''


class FieldInteger(BaseField):
    """Basic integer field with optional bounds.

    Attributes:
        default: Default / assigned value.
        min: Optional minimum allowed value.
        max: Optional maximum allowed value.
    """

    default: int | None = 0
    min: int | None = None
    max: int | None = None


class FieldFloat(BaseField):
    """Basic float field with optional bounds.

    Attributes:
        default: Default / assigned value.
        min: Optional minimum allowed value.
        max: Optional maximum allowed value.
    """

    default: float | None = 0.0
    min: float | None = None
    max: float | None = None


class FieldBool(BaseField):
    """Basic bool field.

    Attributes:
        default: Default / assigned value.
    """

    default: bool | None = False


class FieldJsonText(BaseField):
    """Basic JSON field.

    Attributes:
        default: Default / assigned value.
    """

    default: dict[str, Any] = Field(default_factory=dict)


class FieldEnum(BaseField):
    """Basic enum field with selectable options.

    Attributes:
        options: List of available options, each with at least a 'value' key.
        default: Currently selected option value or None.
    """

    options: list[dict[str, str | int]] = Field(default_factory=list)
    default: str | int | None = None

    def model_post_init(self, __context: Any) -> None:
        """Fill in default if no valid value specified and call the base post init."""
        BaseField.model_post_init(self, __context)

        if not self.options:
            self.default = None
            return

        if self.default not in [o.get('value') for o in self.options]:
            self.default = None
            # self.default = values[0]


#
# Composite field types
#


class FieldNested(BaseField):
    """Base class for fields that contain one or more nested subfields.

    Attributes:
        fields: Nested child fields contained in this field.
    """

    fields: list[BaseField] = Field(default_factory=list)

    def get_children(self) -> list[BaseField]:
        """Return the list of active subfields."""
        return self.fields

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Recursively serialize this field, its content and all subfields."""
        base = super().model_dump(*args, **kwargs)
        base['fields'] = [child.model_dump(*args, **kwargs) for child in self.fields]
        return base


class FieldData(FieldNested):
    """Group field that contains a list of subfields."""


class FieldList(FieldNested):
    """List field containing repeated items.

    Attributes:
        default: Values currently contained in the list, for example
            [1, 2, 3] or [{'content_1': 1, 'content_2': 'b'}].
    """

    default: list[dict[Any, Any] | BaseContent | int | str | float | bool] = Field(default_factory=list)

    @model_validator(mode='after')
    def _validate_defaults(self) -> FieldList:
        if self.default is None:
            return self
        for i, item in enumerate(self.default):
            if not isinstance(item, (dict, BaseContent, int, str, float, bool)):
                raise ValueError(f'List item {i} must be a dict/content/primitives, got {type(item)}')
        return self


class FieldUnion(FieldNested):
    """Union field selecting exactly one child variant.

    Attributes:
        default: Name of the active child field, or None if none is selected.
    """

    default: str | None = None  # name of the selected type

    def get_children(self) -> list[BaseField]:
        """Return the list of active subfields."""
        if not self.default:
            return []
        return [selected] if (selected := next((f for f in self.fields if f.name == self.default), None)) else []

    @model_validator(mode='after')
    def _validate_default(self) -> FieldUnion:
        available_names: set[str] = {f.name for f in self.fields}
        if self.default is not None and self.default not in available_names:
            raise ValueError(f"FieldUnion.default '{self.default}' not in options {sorted(available_names)}")
        return self


class FieldOptional(FieldNested):
    """Optional field that can enable or disable its children.

    Attributes:
        default: True when the nested fields are enabled, False otherwise.
    """

    default: bool = False  # True = enabled, False = disabled

    def get_children(self) -> list[BaseField]:
        """Return the list of active subfields."""
        if not self.default:
            return []
        return self.fields


#
# Alias for UI config variant
#

FormField = (
    FieldString
    | FieldPassword
    | FieldTextArea
    | FieldInteger
    | FieldFloat
    | FieldBool
    | FieldJsonText
    | FieldEnum
    | FieldList
    | FieldData
    | FieldUnion
    | FieldOptional
)
