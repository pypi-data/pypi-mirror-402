from dataspree.formconfig.data.base_configurable import AliasContainerType as AliasContainerType, BaseConfigurableData, ConfigValue
from dataspree.formconfig.data.config_list import ConfigList
from dataspree.formconfig.data.config_optional import ConfigOptional
from dataspree.formconfig.data.config_union import ConfigUnion
from typing import Any, TypeVar, overload
from typing_extensions import TypeForm

CT = TypeVar('CT', bound=ConfigValue)
K = TypeVar('K')
V = TypeVar('V')
CU = TypeVar('CU', bound=ConfigValue)
CO = TypeVar('CO', bound=ConfigValue)
L = TypeVar('L', bound=ConfigValue)

@overload
def from_defaults(alias: str, data: Any) -> BaseConfigurableData | Any: ...
@overload
def from_defaults(alias: type[BaseConfigurableData], data: Any) -> BaseConfigurableData: ...
@overload
def from_defaults(alias: TypeForm[ConfigUnion[CU]], data: Any) -> ConfigUnion[CU]: ...
@overload
def from_defaults(alias: TypeForm[ConfigOptional[CO]], data: Any) -> ConfigOptional[CO]: ...
@overload
def from_defaults(alias: TypeForm[ConfigList[L]], data: Any) -> ConfigList[L]: ...
@overload
def from_defaults(alias: TypeForm[list[CT]], data: Any) -> ConfigList[CT]: ...
@overload
def from_defaults(alias: TypeForm[tuple[CT, ...]], data: Any) -> tuple[Any, ...]: ...
@overload
def from_defaults(alias: TypeForm[tuple[Any, Any]], data: Any) -> tuple[Any, ...]: ...
@overload
def from_defaults(alias: TypeForm[dict[K, V]], data: Any) -> dict[Any, Any]: ...
@overload
def from_defaults(alias: Any, data: Any) -> Any: ...
