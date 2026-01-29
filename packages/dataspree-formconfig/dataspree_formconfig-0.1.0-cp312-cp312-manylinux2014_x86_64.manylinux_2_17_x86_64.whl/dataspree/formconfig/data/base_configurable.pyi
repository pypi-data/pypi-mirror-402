import abc
from _typeshed import Incomplete
from abc import abstractmethod
from collections.abc import Iterable
from dataclasses import Field, dataclass
from dataspree.formconfig.data.base import BaseContent, PrimitiveClass, PrimitiveTypes
from dataspree.formconfig.fields.base_fields import BaseField as BaseField
from types import GenericAlias
from typing import Any, TypeAlias, TypeVar
from typing_extensions import TypeForm

AliasContainerType: TypeAlias = TypeForm[Any] | GenericAlias
C = TypeVar('C', bound='BaseConfigurableData')
WrapperAlias: Incomplete

def build_defaults(val: Any) -> Any:
    """Convert a value into its default representation."""

@dataclass
class BaseConfigurableData(BaseContent, metaclass=abc.ABCMeta):
    """Concrete content that works with dataclass-style fields to generate UI.

    Metadata keys commonly supported by fields:
        - display_name: str
        - description: str
        - default: Any
        - input: type[BaseField]
    """
    @classmethod
    def get_subfield_descriptors(cls) -> Iterable[Field[Any]]:
        """Return dataclass field definitions with metadata for schema building.

        Allow to define get_subfield_descriptors in the BaseConfigurableData and use it if available.
        """
    @classmethod
    @abstractmethod
    def build_field_for_type(cls, value: C | None = None, type_specification: WrapperAlias | None = None, name: str | None = None, metadata: dict[str, Any] | None = None) -> BaseField:
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
    def build_defaults(self) -> dict[str, Any] | Any:
        """Create a nested default dictionary for representation in UI."""
    def build_root_defaults(self) -> dict[str, Any]:
        """Create a nested default dictionary for disk representation."""
    def serialize_to_disk_representation(self) -> dict[str, Any] | Any:
        '''Serialize this into a representation that can be stored. Defaults to the "default" representation from UI.

        Has to be reversible by parse_from_disk_representation.
        '''
    @classmethod
    @abstractmethod
    def from_defaults(cls, data: dict[str, Any] | Any, alias: WrapperAlias | None = None) -> BaseConfigurableData:
        """Create an instance from UI defaults data.

        Raises:
            FormConfigError: If the input cannot be parsed for this type.
        """
    @classmethod
    def parse_from_disk_representation(cls, value: Any) -> BaseConfigurableData:
        '''Load from serialized representation.

        Defaults to the "from_defaults" that loads from UI default representation.
        Has to be reversible by serialize_to_disk_representation.
        '''
    @classmethod
    def load_root_defaults(cls, data: dict[str, Any], alias: WrapperAlias | None = None) -> BaseConfigurableData:
        """Load as root."""
    @classmethod
    def register(cls, subclass: type[_T]) -> None:
        """Register base class and copy all functions! Raise if abstract method not implemented."""
ConfigValue: TypeAlias = BaseConfigurableData | PrimitiveTypes
ConfigType: TypeAlias = type[BaseConfigurableData] | PrimitiveClass | AliasContainerType

def require_valid_config_value(value: Any, *, ctx: str = 'value') -> ConfigValue:
    """Validate that a runtime value is BaseConfigurableData or a primitive, else raise."""
def require_valid_config_type(tp: Any, *, ctx: str = 'type') -> ConfigType:
    """Validate that a type is a BaseConfigurableData subclass or a primitive class, else raise.

    Performs only surface-level validation.
    """
def inject_and_validate(provider: type[Any], target: type[Any]) -> None:
    """Inject non-abstract public attributes from provider (including bases) and enforce abstracts.

    Injection walks the provider MRO (provider first, then bases) and copies attributes that:
    - do not start with '_'
    - are not already present on the target
    - are not abstract (based on __isabstractmethod__)
    """
