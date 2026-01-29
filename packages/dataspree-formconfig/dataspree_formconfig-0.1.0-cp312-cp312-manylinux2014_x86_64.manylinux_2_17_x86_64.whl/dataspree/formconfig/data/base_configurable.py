"""Form generator configuration schema representation.

This module defines configurable content classes used to represent structured UI input
schemas. Each class provides logic to map values into UI field configurations and defaults.
It is based on a flexible BaseContent interface, extended by BaseConfigurableData.
"""

from __future__ import annotations

from abc import abstractmethod, ABCMeta
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass, Field
import inspect
from types import GenericAlias
from typing import Any, TypeVar, TYPE_CHECKING, TypeAlias, get_origin, cast, Type
from typing_extensions import TypeForm


from dataspree.formconfig.data.base import BaseContent, PrimitiveTypes, PrimitiveClass, PrimitiveArgs
from dataspree.formconfig.core.exceptions import FormConfigError, FormConfigImplementationError
from dataspree.formconfig.core.naming import display_class_name, display_value
from dataspree.formconfig.fields.base_fields import BaseField
from dataspree.formconfig.typing.type_utils import type_key_class


# @dev: For A|B, list[A], dict[...], typing.List[...], typing.Union[...] etc
if TYPE_CHECKING:
    AliasContainerType: TypeAlias = TypeForm[Any] | GenericAlias
else:
    AliasContainerType = object  # runtime marker only; must be guarded via get_origin / isinstance checks


C = TypeVar('C', bound='BaseConfigurableData')

WrapperAlias = Type['BaseConfigurableData'] | AliasContainerType

_T = TypeVar('_T')


def build_defaults(val: Any) -> Any:
    """Convert a value into its default representation."""
    return val.build_defaults() if isinstance(val, BaseConfigurableData) else val


@dataclass
class BaseConfigurableData(BaseContent):
    """Concrete content that works with dataclass-style fields to generate UI.

    Metadata keys commonly supported by fields:
        - display_name: str
        - description: str
        - default: Any
        - input: type[BaseField]
    """

    #
    # Retrieve subfields
    #

    @classmethod
    def get_subfield_descriptors(cls: Type[BaseConfigurableData]) -> Iterable[Field[Any]]:
        """Return dataclass field definitions with metadata for schema building.

        Allow to define get_subfield_descriptors in the BaseConfigurableData and use it if available.
        """
        return fields(cls) if is_dataclass(cls) else []

    #
    # Generate UI Representation
    #

    @classmethod
    @abstractmethod
    def build_field_for_type(
        cls: Type[C],
        value: C | None = None,
        type_specification: WrapperAlias | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> BaseField:
        """Create a UI field representation for any sort of value, including the defaults.

        Args:
            value: The input value if available.

            type_specification: Optional wrapper type for configurable data.

            name: Name of the field.

            metadata: Field metadata, including display name and description.

        Returns:
            BaseField: The suitable UI representation.
        """

    def build_field(self, name: str | None = None, metadata: dict[str, Any] | None = None) -> BaseField:
        """Utility function to  create a UI field representation for any sort of value, including the defaults.

        Args:
            name: Name of the field.

            metadata: Field metadata, including display name and description.

        Returns:
            BaseField: The suitable UI representation.
        """
        return self.build_field_for_type(self, name=name, metadata=metadata)

    #
    # Serialize to simple structure
    #

    # UI Defaults representation

    def build_defaults(self) -> dict[str, Any] | Any:
        """Create a nested default dictionary for representation in UI."""
        field_descriptors = self.get_subfield_descriptors()
        try:
            return {f.name: build_defaults(getattr(self, f.name)) for f in field_descriptors}
        except AttributeError as e:
            raise FormConfigError(
                f'Missing attribute on {display_class_name(type(self))} instance {display_value(self)}.'
                f'Required field names: {", ".join(d.name for d in field_descriptors)}'
            ) from e

    def build_root_defaults(self) -> dict[str, Any]:
        """Create a nested default dictionary for disk representation."""
        return {type_key_class(type(self)): self.build_defaults()}

    # Serialized representation, not necessarily linked to UI.

    def serialize_to_disk_representation(self) -> dict[str, Any] | Any:
        """Serialize this into a representation that can be stored. Defaults to the "default" representation from UI.

        Has to be reversible by parse_from_disk_representation.
        """
        return self.build_defaults()

    #
    # Instantiate from serialized structure
    #

    @classmethod
    @abstractmethod
    def from_defaults(cls, data: dict[str, Any] | Any, alias: WrapperAlias | None = None) -> BaseConfigurableData:
        """Create an instance from UI defaults data.

        Raises:
            FormConfigError: If the input cannot be parsed for this type.
        """

    @classmethod
    def parse_from_disk_representation(cls, value: Any) -> BaseConfigurableData:
        """Load from serialized representation.

        Defaults to the "from_defaults" that loads from UI default representation.
        Has to be reversible by serialize_to_disk_representation.
        """
        return cls.from_defaults(value)

    @classmethod
    def load_root_defaults(cls, data: dict[str, Any], alias: WrapperAlias | None = None) -> BaseConfigurableData:
        """Load as root."""
        key = type_key_class(cls)
        inner = data.get(key, data)
        return cls.from_defaults(inner, alias)

    @classmethod
    def register(cls, subclass: Type[_T]) -> None:
        """Register base class and copy all functions! Raise if abstract method not implemented."""
        ABCMeta.register(cls, subclass)
        inject_and_validate(cls, subclass)


ConfigValue: TypeAlias = BaseConfigurableData | PrimitiveTypes

# AliasContainerTYpe is too broad for what I wanna express, but required. Otherwise, ConfigList[int] (i.e., a
# BaseConfigurableData with instantiated attributes) or sth similar would not be captured.
ConfigType: TypeAlias = Type[BaseConfigurableData] | PrimitiveClass | AliasContainerType


def require_valid_config_value(value: Any, *, ctx: str = 'value') -> ConfigValue:
    """Validate that a runtime value is BaseConfigurableData or a primitive, else raise."""
    if isinstance(value, BaseConfigurableData):
        return value
    if isinstance(value, PrimitiveArgs):
        return value
    raise FormConfigError(f'{ctx} must be BaseConfigurableData or PrimitiveTypes, got {type(value)!r}.')


def require_valid_config_type(tp: Any, *, ctx: str = 'type') -> ConfigType:
    """Validate that a type is a BaseConfigurableData subclass or a primitive class, else raise.

    Performs only surface-level validation.
    """
    origin = get_origin(tp)

    if isinstance(origin, type):
        if issubclass(origin, BaseConfigurableData) or origin in PrimitiveArgs:
            return cast(ConfigType, tp)

    elif isinstance(tp, type) and (issubclass(tp, BaseConfigurableData) or tp in PrimitiveArgs):
        return tp

    raise FormConfigError(f'{ctx} must be BaseConfigurableData subclass or PrimitiveType, got {tp!r}.')


def inject_and_validate(provider: Type[Any], target: Type[Any]) -> None:
    """Inject non-abstract public attributes from provider (including bases) and enforce abstracts.

    Injection walks the provider MRO (provider first, then bases) and copies attributes that:
    - do not start with '_'
    - are not already present on the target
    - are not abstract (based on __isabstractmethod__)
    """
    for base in inspect.getmro(provider):
        if base is object:
            break

        for name, obj in vars(base).items():
            if name.startswith('_'):
                continue
            if hasattr(target, name):
                continue
            if getattr(obj, '__isabstractmethod__', False):
                continue
            setattr(target, name, obj)

    missing: list[str] = []
    for name in getattr(provider, '__abstractmethods__', ()):
        if not hasattr(target, name):
            missing.append(name)
            continue

        attr = getattr(target, name)
        if getattr(attr, '__isabstractmethod__', False):
            missing.append(name)

    if missing:
        raise FormConfigImplementationError(
            f'{target.__qualname__} missing required implementations: {", ".join(sorted(missing))}'
        )
