from dataspree.formconfig.data.base import PrimitiveClass as PrimitiveClass
from dataspree.formconfig.data.base_configurable import AliasContainerType as AliasContainerType, BaseConfigurableData
from dataspree.formconfig.fields.base_fields import BaseField
from types import UnionType
from typing import Any, TypeVar

C = TypeVar('C', bound='BaseConfigurableData')

def build_field(name: str, value_type: type[BaseConfigurableData] | PrimitiveClass | AliasContainerType | UnionType | None = None, metadata: dict[str, Any] | None = None) -> BaseField:
    """Fallback: build a field for a particular value.

    Args:
        value_type: Optional wrapper type for configurable data.
        name: Name of the field.
        metadata: Field metadata, including display name and description.

    Returns:
        BaseField: The suitable UI representation.
    """
B = TypeVar('B', bound=BaseField)

def instantiate_field(default_input: type[B] | None, name: str, metadata: dict[str, Any]) -> B | BaseField:
    """Used to instantiate UI fields."""
