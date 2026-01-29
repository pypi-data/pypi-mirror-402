"""This module contains parsers for various lists kinds."""

import typing as t

from ._base import Parser
from ._swagger_utils import OpenAPISchema
from ._utils import Final
from ._utils import T as _T
from ._utils import Y as _Y
from .exceptions import MultipleParseErrors, ParseError, SimpleParseError

__all__ = ('List', 'TwoTuple')


class List(t.Generic[_T], Parser[t.Sequence[_T]]):
    """A parser for a list homogeneous values."""

    __slots__ = ('__el_type',)

    def __init__(self, el_type: Parser[_T]):
        super().__init__()
        self.__el_type: Final = el_type

    def describe(self) -> str:
        return f'List[{self.__el_type.describe()}]'

    def _to_open_api(self, schema: OpenAPISchema) -> t.Mapping[str, t.Any]:
        return {
            'type': 'array',
            'items': self.__el_type.to_open_api(schema),
        }

    def try_parse(self, value: object) -> t.List[_T]:
        if not isinstance(value, list):
            raise SimpleParseError(self, value)

        el_type = self.__el_type
        res = []
        errors = []

        for idx, item in enumerate(value):
            try:
                res.append(el_type.try_parse(item))
            except ParseError as e:
                errors.append(e.add_location(idx))

        if errors:
            raise MultipleParseErrors(self, value, errors)
        else:
            return res


class ListSizeRestrictions(t.Generic[_T], Parser[t.Sequence[_T]]):
    """A parser for a list with size restrictions."""

    __slots__ = ('_parser', '_max_size', '_min_size')

    def __init__(
        self,
        parser: List[_T],
        *,
        max_size: int | None = None,
        min_size: int = 0,
    ) -> None:
        """
        :param parser: The list parser to add restrictions to.
        :param max_size: The maximum size it may have, inclusive.
        :param min_size: The minimum size it may have, inclusive.
        """
        super().__init__()
        self._parser = parser
        self._max_size = max_size
        self._min_size = min_size
        assert self._min_size >= 0

        if self._max_size is not None:
            assert self._max_size >= 1
            assert self._max_size > self._min_size

    def describe(self) -> str:
        base = self._parser.describe()
        if self._min_size > 0:
            base += f' of at least {self._min_size} items'
            if self._max_size is not None:
                base += ', and'
        if self._max_size is not None:
            base += f' of at most {self._max_size} items'
        return base

    def try_parse(self, value: object) -> t.Sequence[_T]:
        base = self._parser.try_parse(value)
        if self._max_size is not None and self._max_size < len(base):
            raise SimpleParseError(self, value)
        if len(base) < self._min_size:
            raise SimpleParseError(self, value)

        return base

    def _to_open_api(self, schema: OpenAPISchema) -> t.Mapping[str, t.Any]:
        base = {
            **self._parser.to_open_api(schema),
        }
        if self._max_size is not None:
            base['maxItems'] = self._max_size
        if self._min_size > 0:
            base['minItems'] = self._min_size
        return base


class TwoTuple(t.Generic[_T, _Y], Parser[t.Tuple[_T, _Y]]):
    """A parser for a tuple that consists exactly of two arguments."""

    __slots__ = ('__left', '__right')

    def __init__(self, left: Parser[_T], right: Parser[_Y]) -> None:
        super().__init__()
        self.__left = left
        self.__right = right

    def describe(self) -> str:
        return 'Tuple[{}, {}]'.format(
            self.__left.describe(), self.__right.describe()
        )

    def _to_open_api(self, schema: OpenAPISchema) -> t.Mapping[str, t.Any]:
        return {
            'type': 'array',
            'items': (self.__left | self.__right).to_open_api(schema),
            'minItems': 2,
            'maxItems': 2,
        }

    def try_parse(self, value: object) -> t.Tuple[_T, _Y]:
        if not isinstance(value, (tuple, list)):
            raise SimpleParseError(self, value)
        if len(value) != 2:
            raise SimpleParseError(self, value)

        return (
            self.__left.try_parse(value[0]),
            self.__right.try_parse(value[1]),
        )
