"""Templated union of multiple types."""

from __future__ import annotations

from dataclasses import dataclass
from types import UnionType
from typing import TypeVar, Generic, get_origin, Union, Any, get_args, Type

from dataspree.formconfig.data.base_configurable import (
    ConfigValue,
    BaseConfigurableData,
    WrapperAlias,
    require_valid_config_type,
    require_valid_config_value,
    build_defaults,
)
from dataspree.formconfig.data.parse import from_defaults
from dataspree.formconfig.data.serialize import instantiate_field, build_field
from dataspree.formconfig.core.exceptions import (
    FormConfigError,
    FormConfigTypeResolutionError,
    FormConfigValidationError,
    FormConfigMetadataError,
    FormConfigParseError,
)
from dataspree.formconfig.core.naming import display_class_name
from dataspree.formconfig.fields.base_fields import BaseField, FieldUnion
from dataspree.formconfig.typing.generic_with_args import GenericWithArgs
from dataspree.formconfig.typing.type_utils import resolve_generic_arg, resolve_generic_args, type_key_class

U = TypeVar('U', bound=ConfigValue)


@dataclass
class ConfigUnion(GenericWithArgs, Generic[U], BaseConfigurableData):
    """Templated union of multiple types selectable via UI.

    Allowed:
    - ConfigUnion[A | B | ...] where A, B, ... are of type BaseConfigurableData or PrimitiveTypes.
    - ConfigUnion[Union[A, ...]] where A, ... are of type BaseConfigurableData or PrimitiveTypes.

    Example allowed:
        - ConfigUnion[Union[A, int]]
        - ConfigUnion[Union[int]]
        - ConfigUnion[int | A]

    Example disallowed:
         - ConfigUnion[int | type(None)]
         - ConfigUnion[X | A] where X is neither of type BaseConfigurableData or PrimitiveTypes
         - ConfigUnion[Union[X, A]] where X is neither of type BaseConfigurableData or PrimitiveTypes
         - ConfigUnion (without parameters). This cannot be checked at annotation time, but at instantiation
         - ConfigUnion[A] where A is arbitrary (can be BaseConfigurableData or PrimitiveTypes).
    """

    content: ConfigValue | None = None  # instance of the selected member

    @classmethod
    def _contained_types(cls, alias: WrapperAlias) -> list[Type[Any]]:
        """Simple utility function that checks the member args and returns them.

        Given ConfigUnion[Union[A, ...]] or ConfigUnion[A | B | ...] this returns [A, B, ...] and checks that they
        adhere to the constraints formulated in the type annotations.
        """
        origin = get_origin(alias) or alias
        origin_cls = getattr(cls, '__origin__', None)
        if not isinstance(origin_cls, type):
            origin_cls = cls

        if not isinstance(origin, type) or not issubclass(origin, origin_cls):
            raise FormConfigTypeResolutionError(f'Alias must be a {display_class_name(cls)}.')

        child_arg = resolve_generic_arg(alias, of=origin_cls, index=0, default=None)
        if child_arg is not None and get_origin(child_arg) in (Union, UnionType):
            if not (params := resolve_generic_args(child_arg)):
                raise FormConfigTypeResolutionError(
                    f'{display_class_name(cls)} must be of Union | UnionType with at least one argument.'
                )

            try:
                for t in params:
                    require_valid_config_type(t)
            except FormConfigError as e:
                raise FormConfigTypeResolutionError(
                    f'{display_class_name(cls)} parameter must be PrimitiveType or BaseConfigurableData: {e}'
                )

            members: list[Type[Any]] = []
            for t in params:
                t_cls = get_origin(t) or t
                if not isinstance(t_cls, type):
                    raise FormConfigTypeResolutionError(
                        f'{display_class_name(cls)} members must be runtime types, got {t!r}.'
                    )
                members.append(t_cls)

            return members
        else:
            raise FormConfigTypeResolutionError(
                f'{display_class_name(cls)} parameter must be Union of PrimitiveTypes or BaseConfigurableData.'
            )

    @property
    def selected(self) -> str | None:
        """Return the identifier of the current selection."""
        if self.content is None:
            return None

        try:
            require_valid_config_value(self.content)
        except FormConfigError as e:
            raise FormConfigValidationError(f'Invalid ConfigUnion content: {type(self.content)!r}: {e}.')

        return type_key_class(type(self.content))

    @classmethod
    def build_field_for_type(
        cls: Type[ConfigUnion[U]],
        value: ConfigUnion[U] | None = None,
        type_specification: WrapperAlias | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FieldUnion | BaseField:
        """Transform an instance of this class or None into the representation of this class."""
        metadata = dict(metadata or {})
        if 'default' in metadata:
            raise FormConfigMetadataError('Ambiguous default value.')

        if type_specification is None:
            type_specification = cls.typing_alias()

        name = name or type_key_class(cls)

        # Determine selection and content.
        selected_key: str | None
        content: ConfigValue | None
        if value is None:
            selected_key = None
            content = None
        else:
            selected_key = value.selected
            content = value.content

        # Build all child fields.
        children: list[BaseField] = []
        member_classes: list[Type[Any]] = cls._contained_types(type_specification)

        for cld_cls in member_classes:
            cld_name: str = type_key_class(cld_cls)

            # Only fill in the value if hte current member is selected
            cld_val: ConfigValue | None = content if selected_key == cld_name and isinstance(content, cld_cls) else None

            if (raw_child_meta := metadata.pop(cld_name, {})) is None:
                raw_child_meta = {}

            if not isinstance(raw_child_meta, dict):
                raise FormConfigMetadataError(
                    f'Field metadata for {display_class_name(cls)}.{cld_name} must be a dict, got '
                    f'{type(raw_child_meta)!r}.'
                )

            if 'default' in raw_child_meta:
                raise FormConfigMetadataError(
                    f'Ambiguous default value for union member {display_class_name(cls)}.{cld_name}.'
                )

            (child_meta := dict(raw_child_meta))['default'] = cld_val
            children.append(build_field(value_type=cld_cls, name=cld_name, metadata=child_meta))

        # Allow building a field even if no default is specified (although a ConfigUnion can only contain an actual
        # selection)
        if selected_key is None:
            selected_key = None
            # raise FormConfigValidationError(f'{display_class_name(cls)} needs an active selection!')

        # Build outer level
        metadata['fields'] = children
        metadata['default'] = selected_key
        return instantiate_field(FieldUnion, name, metadata)

    def build_defaults(self) -> dict[str, Any]:
        """Create a nested default dictionary for representation in UI."""
        if (key := self.selected) is None:
            raise FormConfigValidationError(f'{display_class_name(type(self))} needs an active selection.')

        if self.content is None:
            raise FormConfigValidationError(f'{display_class_name(type(self))} selection {key!r} has no content.')

        # include selection for list-row defaults
        return {'selection': key, key: build_defaults(self.content)}

    @classmethod
    def from_defaults(cls, data: dict[str, Any] | Any, alias: WrapperAlias | None = None) -> ConfigUnion[U]:
        """Create an instance from UI defaults data.

        Raises:
            FormConfigError: If the input cannot be parsed for this type.
        """
        # Extract member types from ConfigUnion[Union[A,B,...]] or ConfigUnion[A] and guard.
        members: list[Type[Any]] = cls._contained_types(alias or cls)

        # Check input
        if not isinstance(data, dict):
            raise FormConfigParseError(f'Expected dict data for {display_class_name(cls)}, got {type(data)!r}.')

        # Check selection
        if not (sel := data.get('selection')):
            raise FormConfigValidationError(f'{display_class_name(cls)} requires an active selection.')

        if not isinstance(sel, str):
            raise FormConfigParseError(f'{display_class_name(cls)} selection must be str, got {type(sel)!r}.')

        if (target := next((m for m in members if type_key_class(m) == sel), None)) is None:
            raise FormConfigValidationError(f'{display_class_name(cls)} selection {sel!r} is not a valid member.')

        if sel not in data:
            raise FormConfigValidationError(
                f'{display_class_name(cls)} selection {sel!r} is missing its content payload.'
            )

        content = from_defaults(data=data.get(sel), alias=target)
        if not isinstance(content, target):
            raise FormConfigValidationError(
                f'{display_class_name(cls)} selection {sel!r} produced incompatible content.'
            )

        try:
            return cls(content)
        except FormConfigError:
            raise
        except Exception as e:
            raise FormConfigParseError(
                f'Could not instantiate {display_class_name(cls)} with selection {sel!r} and content '
                f'of type {display_class_name(type(content))}.'
            ) from e

    def __class_getitem__(cls, item: Any) -> Any:
        """Validate generic argument at alias creation time.

        This explicitly disallows Annotated for now.
        """
        if get_origin(item) not in (Union, UnionType):
            raise FormConfigTypeResolutionError(
                f'{display_class_name(cls)} parameter must be Union[A, B, ...] or A | B | ..., got {item!r}.'
            )

        if not len(a := get_args(item)):
            raise FormConfigTypeResolutionError(f'{display_class_name(cls)} must have Union/UnionType arguments .')

        try:
            for m in a:
                require_valid_config_type(m)
        except FormConfigError as e:
            raise FormConfigTypeResolutionError(
                f'{display_class_name(cls)} parameter must be PrimitiveType or BaseConfigurableData: {e}'
            )

        return super().__class_getitem__(item)
