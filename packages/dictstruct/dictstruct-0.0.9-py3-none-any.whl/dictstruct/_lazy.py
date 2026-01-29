from collections.abc import Iterator
from typing import Any, ClassVar, Final

from msgspec import UNSET

from dictstruct._main import DictStruct

_getattribute: Final = object.__getattribute__


class LazyDictStruct(DictStruct, frozen=True):  # type: ignore [misc]
    """
    A subclass of :class:`DictStruct` that supports Just-In-Time (JIT) decoding of field values.

    `LazyDictStruct` is designed for developers who need to efficiently handle large or complex data structures, particularly when working with serialized data formats like JSON. By storing field values in a raw, undecoded format, this class allows for deferred decoding, meaning that data is only decoded when accessed. This approach can lead to significant performance improvements and reduced memory usage, especially in scenarios where not all fields are always needed.

    Key Features:
    - **JIT Decoding**: Decode data only when accessed, saving processing time and memory.
    - **Immutable Structure**: As a frozen dataclass, instances are immutable, ensuring data integrity after creation.
    - **Compatibility**: Inherits from :class:`DictStruct`, making it compatible with the standard dictionary API, allowing for easy integration with existing codebases that rely on dictionary-like data structures.

    Use Cases:
    - Handling large JSON responses from APIs where only a subset of the data is needed at any given time.
    - Optimizing applications that process data lazily, improving startup times and reducing resource consumption.

    Example:
        >>> import msgspec
        >>> from functools import cached_property
        >>> class MyStruct(LazyDictStruct):
        ...     _myField: msgspec.Raw = msgspec.field(name='myField')
        ...     @cached_property
        ...     def myField(self) -> YourGiantJsonObject:
        ...         '''Decode the raw JSON data into a python object when accessed.'''
        ...         return msgspec.json.decode(self._myField, type=YourGiantJsonObject)
        ...
        >>> # Encode data into a raw JSON format
        >>> raw_data = msgspec.json.encode({"myField": "some value"})
        >>> # Create an instance of MyStruct with the raw data
        >>> my_struct = MyStruct(_myField=raw_data)
        >>> # Access the decoded field value
        >>> print(my_struct.myField)
        "some value"

    See Also:
        :class:`DictStruct` for the base class implementation.
    """

    __lazy_field_pairs__: ClassVar[tuple[tuple[str, str], ...]]
    __lazy_public_to_raw__: ClassVar[dict[str, str]]

    def __init_subclass__(cls, *args: Any, **kwargs: Any) -> None:
        """
        Initialize a subclass of :class:`LazyDictStruct`.

        This method resolves any lazy field names (prefixed with an underscore) and overwrites
        `cls.__struct_fields__` so it contains the names of the materialized properties
        defined on your subclass.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        See Also:
            :class:`DictStruct` for the base class implementation.
        """
        super().__init_subclass__(*args, **kwargs)

        if cls.__name__ == "StructMeta":
            return

        try:
            cls.__struct_fields__
        except AttributeError:
            return

    # "A classmethod + class attrs is the lightest way to do that without storing extra data on every instance."
    @classmethod
    def __lazy_field_maps__(cls) -> tuple[tuple[tuple[str, str], ...], dict[str, str]]:
        try:
            return cls.__lazy_field_pairs__, cls.__lazy_public_to_raw__
        except AttributeError:
            struct_fields = cls.__struct_fields__
            field_pairs = tuple(
                (raw_name, raw_name[1:] if raw_name[0] == "_" else raw_name)
                for raw_name in struct_fields
            )
            public_to_raw = {public_name: raw_name for raw_name, public_name in field_pairs}
            cls.__lazy_field_pairs__ = field_pairs
            cls.__lazy_public_to_raw__ = public_to_raw
            return field_pairs, public_to_raw

    def __contains__(self, key: str) -> bool:
        """
        Check if a key is in the struct.

        Args:
            key: The key to check.

        Returns:
            True if the key is present and not :obj:`~msgspec.UNSET`, False otherwise.

        Example:
            >>> class MyStruct(LazyDictStruct):
            ...     field1: str
            >>> s = MyStruct(field1="value")
            >>> 'field1' in s
            True
            >>> 'field2' in s
            False
        """
        # "type(self) vs self: self would go through DictStruct.__getattribute__ (custom) on every call. type(self) does a direct class lookup and still respects subclass overrides of the helper. It's a small but real hot-path win and avoids any instance-level surprises."
        _, public_to_raw = type(self).__lazy_field_maps__()
        raw_name = public_to_raw.get(key)
        if raw_name is None:
            return False
        return _getattribute(self, raw_name) is not UNSET

    def __iter__(self) -> Iterator[str]:
        """
        Iterate through the keys of the Struct.

        Yields:
            Struct key.

        Example:
            >>> class MyStruct(LazyDictStruct):
            ...     field1: str
            ...     field2: int
            >>> s = MyStruct(field1="value", field2=42)
            >>> list(iter(s))
            ['field1', 'field2']
        """
        field_pairs, _ = type(self).__lazy_field_maps__()
        for raw_name, public_name in field_pairs:
            if _getattribute(self, raw_name) is not UNSET:
                yield public_name

    def items(self) -> Iterator[tuple[str, Any]]:
        """
        Returns an iterator over the struct's field name and value pairs.

        Example:
            >>> class MyStruct(DictStruct):
            ...     field1: str
            ...     field2: int
            >>> s = MyStruct(field1="value", field2=42)
            >>> list(s.items())
            [('field1', 'value'), ('field2', 42)]
        """
        field_pairs, _ = type(self).__lazy_field_maps__()
        for _, public_name in field_pairs:
            value = getattr(self, public_name, UNSET)
            if value is not UNSET:
                yield public_name, value

    def values(self) -> Iterator[Any]:
        """
        Returns an iterator over the struct's field values.

        Example:
            >>> class MyStruct(DictStruct):
            ...     field1: str
            ...     field2: int
            >>> s = MyStruct(field1="value", field2=42)
            >>> list(s.values())
            ['value', 42]
        """
        field_pairs, _ = type(self).__lazy_field_maps__()
        for _, public_name in field_pairs:
            value = getattr(self, public_name, UNSET)
            if value is not UNSET:
                yield value
