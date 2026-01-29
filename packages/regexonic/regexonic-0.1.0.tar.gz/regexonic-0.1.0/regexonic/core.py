from __future__ import annotations

import re
import sys
from copy import copy, deepcopy
from dataclasses import dataclass
from re import Match, Pattern
from types import GenericAlias
from typing import (
    Any,
    AnyStr,
    Callable,
    ClassVar,
    Generic,
    Iterator,
    Literal,
    Mapping,
    TypeAlias,
    overload,
)

MaybeNone: TypeAlias = Any


class BaseNotFoundError(ValueError, Generic[AnyStr]):
    template: str
    """
    String template must have have {pattern} for the regex pattern,
    {input} for input string that caused the error.
    """

    def __init__(
        self,
        compiled: Pattern[AnyStr],
        input: AnyStr,
        *args: object,
    ) -> None:
        self.input = input
        self.compiled = compiled
        self.pattern = compiled.pattern
        if isinstance(input, str):
            self._input_str = input
        elif isinstance(input, bytes | bytearray):
            self._input_str = input.decode()
        else:
            raise TypeError(input)
        if isinstance(self.pattern, str):
            self._pattern_str = self.pattern
        elif isinstance(self.pattern, bytes | bytearray):
            self._pattern_str = self.pattern.decode()
        else:
            raise TypeError(self.pattern)
        self.detail = self.template.format(
            pattern=self._pattern_str,
            input=self._input_str,
        )
        super().__init__(self.detail, *args)


class MatchNotFoundError(BaseNotFoundError):
    template: str = "The pattern '{pattern}' does not match the input value '{input}'."


class SearchNotFoundError(BaseNotFoundError):
    template: str = "Using the pattern '{pattern}' yields no results when searching the input value '{input}'."


@dataclass
class Expression(Generic[AnyStr]):
    """
    This is a replacement for the standard `re.Pattern` object
    with better types and additional helper methods.
    All attributes and methods from the original object are
    maintained for compatibility.
    """

    pattern: AnyStr
    flags: int = 0

    def __post_init__(self) -> None:
        self.compiled = re.compile(
            pattern=self.pattern,
            flags=self.flags,
        )

    @classmethod
    def transpile(
        cls, object: re.Pattern[AnyStr] | Expression[AnyStr]
    ) -> Expression[AnyStr]:
        result = Expression(object.pattern, object.flags)
        return result

    def __eq__(self, value: object, /) -> bool:
        if isinstance(value, re.Pattern):
            return self.compiled == value
        elif isinstance(value, Expression):
            return self.compiled == value.compiled
        return False

    def __hash__(self) -> int:
        return hash(self.compiled)

    def __copy__(self) -> Expression[AnyStr]:
        return Expression.transpile(copy(self.compiled))

    def __deepcopy__(self, memo: Any, /) -> Expression[AnyStr]:
        return Expression.transpile(deepcopy(self.compiled, memo))

    def __class_getitem__(cls, item: Any, /) -> GenericAlias:
        return GenericAlias(cls, item)

    @property
    def groupindex(self) -> Mapping[str, int]:
        return self.compiled.groupindex

    @property
    def groups(self) -> int:
        return self.compiled.groups

    @overload
    def search(
        self,
        string: AnyStr,
        pos: int = 0,
        endpos: int = sys.maxsize,
        *,
        required: Literal[True] = True,
    ) -> Match[AnyStr]: ...
    @overload
    def search(
        self,
        string: AnyStr,
        pos: int = 0,
        endpos: int = sys.maxsize,
        *,
        required: Literal[False] = False,
    ) -> Match[AnyStr] | None: ...

    def search(
        self,
        string: AnyStr,
        pos: int = 0,
        endpos: int = sys.maxsize,
        *,
        required: Literal[True] | Literal[False] = False,
    ) -> Match[AnyStr] | None:
        m = self.compiled.search(string, pos, endpos)
        if required and (m is None):
            raise SearchNotFoundError(self.compiled, string)
        return m

    @overload
    def match(
        self,
        string: AnyStr,
        pos: int = 0,
        endpos: int = sys.maxsize,
        *,
        full: bool = False,
        required: Literal[True] = True,
    ) -> Match[AnyStr]: ...

    @overload
    def match(
        self,
        string: AnyStr,
        pos: int = 0,
        endpos: int = sys.maxsize,
        *,
        full: bool = False,
        required: Literal[False] = False,
    ) -> Match[AnyStr] | None: ...

    def match(
        self,
        string: AnyStr,
        pos: int = 0,
        endpos: int = sys.maxsize,
        *,
        full: bool = False,
        required: Literal[True] | Literal[False] = False,
    ) -> Match[AnyStr] | None:
        if full:
            m = self.compiled.fullmatch(string, pos, endpos)
        else:
            m = self.compiled.match(string, pos, endpos)

        if required and (m is None):
            raise MatchNotFoundError(self.compiled, string)
        return m

    @overload
    def fullmatch(
        self,
        string: AnyStr,
        pos: int = 0,
        endpos: int = sys.maxsize,
        *,
        required: Literal[True] = True,
    ) -> Match[AnyStr]: ...

    @overload
    def fullmatch(
        self,
        string: AnyStr,
        pos: int = 0,
        endpos: int = sys.maxsize,
        *,
        required: Literal[False] = False,
    ) -> Match[AnyStr] | None: ...

    def fullmatch(
        self,
        string: AnyStr,
        pos: int = 0,
        endpos: int = sys.maxsize,
        *,
        required: Literal[True] | Literal[False] = False,
    ) -> Match[AnyStr] | None:
        m = self.compiled.fullmatch(string, pos, endpos)
        if required and (m is None):
            raise MatchNotFoundError(self.compiled, string)
        return m

    def split(
        self,
        string: AnyStr,
        maxsplit: int = 0,
    ) -> list[AnyStr | MaybeNone]:
        return self.compiled.split(string, maxsplit)

    def findall(
        self,
        string: AnyStr,
        pos: int = 0,
        endpos: int = sys.maxsize,
    ) -> list[AnyStr]:
        return self.compiled.findall(string, pos, endpos)

    def finditer(
        self, string: AnyStr, pos: int = 0, endpos: int = sys.maxsize
    ) -> Iterator[Match[AnyStr]]:
        return self.compiled.finditer(string, pos, endpos)

    def sub(
        self,
        repl: AnyStr | Callable[[Match[AnyStr]], AnyStr],
        string: AnyStr,
        count: int = 0,
    ) -> AnyStr:
        return self.compiled.sub(repl, string, count)

    def subn(
        self,
        repl: AnyStr | Callable[[Match[AnyStr]], AnyStr],
        string: AnyStr,
        count: int = 0,
    ) -> tuple[AnyStr, int]:
        return self.compiled.subn(repl, string, count)

    def check(self, string: AnyStr, /, full: bool = True) -> bool:
        m = self.compiled.fullmatch(string) if full else self.compiled.match(string)
        return m is not None

    def test(self, string: AnyStr, /, full: bool = True) -> bool:
        return self.check(string, full)

    def validate(self, string: AnyStr, /, full: bool = True) -> AnyStr:
        if not self.check(string, full):
            raise ValueError(
                f"`'{string}'` does not match the pattern `r'{self.compiled.pattern}'`"
            )
        return string


class Subber(Generic[AnyStr]):
    @overload
    def __init__(
        self,
        replace: AnyStr | Callable[[Match[AnyStr]], AnyStr],
        pattern: AnyStr,
        flags: int = 0,
    ) -> None: ...
    @overload
    def __init__(
        self,
        replace: AnyStr | Callable[[Match[AnyStr]], AnyStr],
        pattern: Pattern[AnyStr],
    ) -> None: ...
    def __init__(
        self,
        replace: AnyStr | Callable[[Match[AnyStr]], AnyStr],
        pattern: AnyStr | Pattern[AnyStr],
        flags: int = 0,
    ) -> None:
        self.replace = replace
        if isinstance(pattern, re.Pattern):
            if flags is not None:
                raise ValueError(
                    "If you create an expression using a compiled pattern, you cannot pass flags, as these would be ignored and information would be lost."
                )
            self.compiled: Pattern[AnyStr] = pattern
        elif isinstance(pattern, str | bytes):
            self.compiled = re.compile(pattern=pattern, flags=flags)
        else:
            raise TypeError(pattern)

    def __call__(self, string: AnyStr, count: int = 0) -> AnyStr:
        result = self.compiled.sub(self.replace, string, count)
        return result

    def n(self, string: AnyStr, count: int = 0) -> tuple[AnyStr, int]:
        result = self.compiled.subn(self.replace, string, count)
        return result


class Structure(Generic[AnyStr]):
    """
    This is similar to `Expression`, except is for when you want to create
    a subclass that can implement additional methods for that specific pattern.
    """

    compiled: ClassVar[re.Pattern]

    @property
    def flags(self) -> int:
        return self.compiled.flags

    @overload
    @classmethod
    def match(
        cls,
        string: AnyStr,
        *,
        required: Literal[True] = True,
    ) -> re.Match[AnyStr]: ...
    @overload
    @classmethod
    def match(
        cls,
        string: AnyStr,
        *,
        required: Literal[False] = False,
    ) -> re.Match[AnyStr] | None: ...
    @classmethod
    def match(
        cls,
        string: AnyStr,
        *,
        required: Literal[True] | Literal[False] = True,
    ) -> re.Match[AnyStr] | None:
        m = cls.compiled.match(string)
        if required and (m is None):
            raise MatchNotFoundError(cls.compiled, string)
        return m

    @overload
    @classmethod
    def fullmatch(
        cls,
        string: AnyStr,
        *,
        required: Literal[True] = True,
    ) -> re.Match[AnyStr]: ...
    @overload
    @classmethod
    def fullmatch(
        cls,
        string: AnyStr,
        *,
        required: Literal[False] = False,
    ) -> re.Match[AnyStr] | None: ...
    @classmethod
    def fullmatch(
        cls,
        string: AnyStr,
        *,
        required: Literal[True] | Literal[False] = True,
    ) -> re.Match[AnyStr] | None:
        m = cls.compiled.fullmatch(string)
        if required and (m is None):
            raise MatchNotFoundError(cls.compiled, string)
        return m

    @overload
    @classmethod
    def search(
        cls,
        string: AnyStr,
        *,
        required: Literal[True] = True,
    ) -> re.Match[AnyStr]: ...
    @overload
    @classmethod
    def search(
        cls,
        string: AnyStr,
        *,
        required: Literal[False] = False,
    ) -> re.Match[AnyStr] | None: ...
    @classmethod
    def search(
        cls,
        string: AnyStr,
        *,
        required: Literal[True] | Literal[False] = True,
    ) -> re.Match[AnyStr] | None:
        m = cls.compiled.search(string)
        if required and (m is None):
            raise SearchNotFoundError(cls.compiled, string)
        return m

    @classmethod
    def split(
        cls,
        string: AnyStr,
        maxsplit: int = 0,
    ) -> list[AnyStr | MaybeNone]:
        return cls.compiled.split(string, maxsplit)

    @classmethod
    def findall(
        cls,
        string: AnyStr,
        pos: int = 0,
        endpos: int = sys.maxsize,
    ) -> list[AnyStr]:
        return cls.compiled.findall(string, pos, endpos)

    @classmethod
    def finditer(
        cls,
        string: AnyStr,
        pos: int = 0,
        endpos: int = sys.maxsize,
    ) -> Iterator[Match[AnyStr]]:
        return cls.compiled.finditer(string, pos, endpos)

    @classmethod
    def sub(
        cls,
        repl: AnyStr | Callable[[Match[AnyStr]], AnyStr],
        string: AnyStr,
        count: int = 0,
    ) -> AnyStr:
        return cls.compiled.sub(repl, string, count)

    @classmethod
    def subn(
        cls,
        repl: AnyStr | Callable[[Match[AnyStr]], AnyStr],
        string: AnyStr,
        count: int = 0,
    ) -> tuple[AnyStr, int]:
        return cls.compiled.subn(repl, string, count)

    @classmethod
    def check(
        cls,
        string: AnyStr,
        *,
        full: bool = True,
    ) -> bool:
        m = cls.compiled.fullmatch(string) if full else cls.compiled.match(string)
        return m is not None

    @classmethod
    def test(
        cls,
        string: AnyStr,
        *,
        full: bool = True,
    ) -> bool:
        return cls.check(string, full=full)

    @classmethod
    def validate(
        cls,
        string: AnyStr,
        *,
        full: bool = True,
    ) -> AnyStr:
        if not cls.check(string, full=full):
            raise ValueError(
                f"`'{string}'` does not match the pattern `r'{cls.compiled.pattern}'`"
            )
        return string


@dataclass
class Matcher(Generic[AnyStr]):
    """
    A regex match class used for quickly checking if a string matches a given pattern.

    ??? link
        - https://stackoverflow.com/questions/58774029/differences-between-re-match-re-search-re-fullmatch
    """

    pattern: AnyStr
    flags: int = 0
    full: bool = True
    """Whether the input string must fully match the pattern, as opposed to just a substring."""

    def __post_init__(self) -> None:
        self.compiled = re.compile(
            pattern=self.pattern,
            flags=self.flags,
        )
        self.function = self.compiled.fullmatch if self.full else self.compiled.match

    def __hash__(self) -> int:
        return hash((self.pattern, self.flags, self.full))

    @overload
    def get(
        self,
        string: AnyStr,
        start: int = 0,
        end: int = sys.maxsize,
        *,
        required: Literal[True],
    ) -> re.Match[AnyStr]: ...
    @overload
    def get(
        self,
        string: AnyStr,
        start: int = 0,
        end: int = sys.maxsize,
        *,
        required: Literal[False],
    ) -> re.Match[AnyStr] | None: ...
    @overload
    def get(
        self,
        string: AnyStr,
        start: int = 0,
        end: int = sys.maxsize,
    ) -> re.Match[AnyStr] | None: ...
    def get(
        self,
        string: AnyStr,
        start: int = 0,
        end: int = sys.maxsize,
        *,
        required: bool = False,
    ) -> re.Match[AnyStr] | None:
        result = self.function(string, start, end)
        if required and result is None:
            raise MatchNotFoundError(self.compiled, string)
        return result

    def __call__(
        self,
        string: AnyStr,
        start: int = 0,
        end: int = sys.maxsize,
    ) -> bool:
        """
        Check if an input string matches the pattern

        Parameters:
            string (str): Input string.
            start (int): The start position.
            end (int): The start position.

        Returns:
            True if match found else False.
        """
        return self.get(string, start, end) is not None


def define(pattern: AnyStr, flags: int = 0) -> Expression[AnyStr]:
    return Expression(pattern=pattern, flags=flags)
