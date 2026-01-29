"""Nested dataclass content for grouped input fields."""

from __future__ import annotations

from dataclasses import dataclass, MISSING
from typing import Any, get_type_hints, Type

from dataspree.formconfig.data.base_configurable import BaseConfigurableData, WrapperAlias
from dataspree.formconfig.data.parse import from_defaults
from dataspree.formconfig.data.serialize import build_field, instantiate_field
from dataspree.formconfig.core.exceptions import FormConfigError, FormConfigMetadataError, FormConfigValidationError
from dataspree.formconfig.core.naming import display_class_name, display_value
from dataspree.formconfig.fields.base_fields import BaseField, FieldData
from dataspree.formconfig.typing.type_utils import type_key_class


@dataclass
class ConfigData(BaseConfigurableData):
    """Nested dataclass content for grouped input fields."""

    @classmethod
    def build_field_for_type(
        cls: Type[ConfigData],
        value: ConfigData | None = None,
        type_specification: WrapperAlias | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FieldData | BaseField:
        """Create a UI field representation for any sort of value, including the defaults.

        Args:
            value: The input value if available.

            type_specification: Optional wrapper type for configurable data.

            name: Name of the field.

            metadata: Field metadata, including display name and description.

        Returns:
            BaseField: The suitable UI representation.
        """
        metadata = dict(metadata or {})
        if 'default' in metadata:
            raise FormConfigMetadataError('Ambiguous default value.')

        name = name or type_key_class(cls)
        if 'fields' in metadata:
            raise FormConfigMetadataError('Ambiguous fields provided in metadata.')
        metadata['fields'] = md_fields = []

        # Build children
        hints: dict[str, Any]
        try:
            hints = get_type_hints(cls, include_extras=False)
        except (NameError, TypeError, AttributeError, ImportError):
            hints = {}

        names = metadata.pop('names', None)
        if names is not None:
            if not isinstance(names, (set, list, tuple)) or not all(isinstance(x, str) for x in names):
                raise FormConfigError(
                    f'{display_class_name(cls)}.build_field metadata["names"] must be a list/set/tuple of str.'
                )

        for f in cls.get_subfield_descriptors():
            sub_meta = metadata.pop(f.name, None) or {}
            if names is not None and f.name not in names:
                continue

            if not isinstance(sub_meta, dict):
                raise FormConfigMetadataError(
                    f'Field metadata for {display_class_name(cls)}.{f.name} must be a dict, got {type(sub_meta)!r}.'
                )
            field_meta = dict(f.metadata) | sub_meta

            if (default_from_value := getattr(value, f.name, MISSING)) is not MISSING:
                # Note that we must not build_defaults here, because that's the children's responsibility
                field_meta['default'] = default_from_value

            else:
                if 'default' in field_meta:
                    pass
                elif 'default_factory' in field_meta:
                    field_meta['default'] = field_meta['default_factory']()
                else:
                    if (dc_default := getattr(f, 'default', MISSING)) is not MISSING:
                        field_meta['default'] = dc_default

                    elif (dc_factory := getattr(f, 'default_factory', MISSING)) is not MISSING:
                        field_meta['default'] = dc_factory()

            field_type = hints.get(f.name, f.type)

            md_fields.append(build_field(name=f.name, value_type=field_type, metadata=field_meta))

        metadata.pop('content', None)
        return instantiate_field(FieldData, name, metadata)

    @classmethod
    def from_defaults(cls, data: dict[str, Any] | None | Any, alias: WrapperAlias | None = None) -> ConfigData:
        """Create an instance from UI defaults data.

        Raises:
            FormConfigError: If the input cannot be parsed for this type.
        """
        if data is None:
            raise FormConfigError(f'Expected dict data for {display_class_name(cls)}, got None.')

        if not isinstance(data, dict):
            raise FormConfigError(f'Expected dict data for {display_class_name(cls)}, got {type(data)!r}.')

        try:
            hints = get_type_hints(cls, include_extras=False)
        except (NameError, TypeError, AttributeError, ImportError):
            hints = {}

        inst = cls.__new__(cls)  # bypass __init__

        descriptors = cls.get_subfield_descriptors()

        # Give a "nice" warning about extra keys to make it easy to discover typos.
        if extra_args := set(data.keys()) - {f.name for f in descriptors if f.init}:
            raise FormConfigValidationError(f'Unexpected fields for {display_class_name(cls)}: {sorted(extra_args)!r}')

        for f in descriptors:
            field_alias = hints.get(f.name, f.type)

            if f.init and (val := data.get(f.name, MISSING)) is not MISSING:  # only init fields should be set by user.
                try:
                    val = from_defaults(data=val, alias=field_alias)
                except Exception as e:
                    raise FormConfigError(
                        f'Failed to parse field {display_class_name(cls)}.{f.name} from {type(data[f.name])!r} '
                        f'instance {display_value(val)!r}.'
                    ) from e
                object.__setattr__(inst, f.name, val)

            elif f.default is not MISSING:
                object.__setattr__(inst, f.name, f.default)

            elif f.default_factory is not MISSING:
                object.__setattr__(inst, f.name, f.default_factory())

            elif f.init:
                raise FormConfigError(
                    f'Attribute {f.name} '
                    f'does not have a default / default factory and is not provided but '
                    f'required for initialization!'
                )

        post = getattr(inst, '__post_init__', None)
        if callable(post):
            post()

        return inst
