from __future__ import annotations

import re

import pytest

from regexonic import (
    Expression,
    Matcher,
    MatchNotFoundError,
    SearchNotFoundError,
    Structure,
    Subber,
    define,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def email_pattern() -> Expression[str]:
    return Expression(r"[\w.-]+@[\w.-]+\.\w+")


@pytest.fixture
def digit_pattern() -> Expression[str]:
    return Expression(r"\d+")


@pytest.fixture
def named_groups_pattern() -> Expression[str]:
    return Expression(r"(?P<area>\d{3})-(?P<exchange>\d{3})-(?P<number>\d{4})")


# =============================================================================
# Test: MatchNotFoundError
# =============================================================================


class TestMatchNotFoundError:
    def test_raises_with_correct_attributes(self) -> None:
        compiled = re.compile(r"\d+")
        error = MatchNotFoundError(compiled, "no digits here")

        assert error.compiled is compiled
        assert error.pattern == r"\d+"
        assert error.input == "no digits here"
        assert "no digits here" in error.detail
        assert r"\d+" in str(error)

    def test_with_bytes_pattern(self) -> None:
        compiled = re.compile(rb"\d+")
        error = MatchNotFoundError(compiled, b"no digits here")

        assert error.pattern == rb"\d+"
        assert error.input == b"no digits here"
        assert "no digits here" in error.detail

    def test_is_value_error_subclass(self) -> None:
        compiled = re.compile(r"\d+")
        error = MatchNotFoundError(compiled, "test")

        assert isinstance(error, ValueError)


# =============================================================================
# Test: SearchNotFoundError
# =============================================================================


class TestSearchNotFoundError:
    def test_raises_with_correct_attributes(self) -> None:
        compiled = re.compile(r"\d+")
        error = SearchNotFoundError(compiled, "no digits here")

        assert error.compiled is compiled
        assert error.pattern == r"\d+"
        assert error.input == "no digits here"
        assert "no digits here" in error.detail

    def test_has_different_template_than_match_error(self) -> None:
        compiled = re.compile(r"\d+")
        match_error = MatchNotFoundError(compiled, "test")
        search_error = SearchNotFoundError(compiled, "test")

        assert match_error.template != search_error.template
        assert "match" in match_error.template.lower()
        assert "search" in search_error.template.lower()


# =============================================================================
# Test: Expression - Creation and Properties
# =============================================================================


class TestExpressionCreation:
    def test_create_with_pattern_string(self) -> None:
        expr = Expression(r"\d+")
        assert expr.pattern == r"\d+"
        assert expr.flags == 0

    def test_create_with_flags(self) -> None:
        expr = Expression(r"[a-z]+", flags=re.IGNORECASE)
        assert expr.flags == re.IGNORECASE

    def test_create_with_bytes_pattern(self) -> None:
        expr = Expression(rb"\d+")
        assert expr.pattern == rb"\d+"

    def test_compiled_property(self) -> None:
        expr = Expression(r"\d+")
        assert isinstance(expr.compiled, re.Pattern)
        assert expr.compiled.pattern == r"\d+"

    def test_groups_property(self, named_groups_pattern: Expression[str]) -> None:
        assert named_groups_pattern.groups == 3

    def test_groupindex_property(self, named_groups_pattern: Expression[str]) -> None:
        index = named_groups_pattern.groupindex
        assert index["area"] == 1
        assert index["exchange"] == 2
        assert index["number"] == 3


class TestExpressionEquality:
    def test_equal_to_same_pattern(self) -> None:
        expr1 = Expression(r"\d+")
        expr2 = Expression(r"\d+")
        assert expr1 == expr2

    def test_equal_to_compiled_pattern(self) -> None:
        expr = Expression(r"\d+")
        compiled = re.compile(r"\d+")
        assert expr == compiled

    def test_not_equal_to_different_pattern(self) -> None:
        expr1 = Expression(r"\d+")
        expr2 = Expression(r"\w+")
        assert expr1 != expr2

    def test_not_equal_to_non_pattern(self) -> None:
        expr = Expression(r"\d+")
        assert expr != "\\d+"
        assert expr != 123

    def test_hash_consistency(self) -> None:
        expr1 = Expression(r"\d+")
        expr2 = Expression(r"\d+")
        assert hash(expr1) == hash(expr2)

        # Can be used in sets/dicts
        s = {expr1}
        assert expr2 in s


class TestExpressionCopy:
    def test_copy(self) -> None:
        from copy import copy

        expr = Expression(r"\d+", flags=re.IGNORECASE)
        copied = copy(expr)

        assert copied == expr
        assert copied is not expr

    def test_deepcopy(self) -> None:
        from copy import deepcopy

        expr = Expression(r"\d+", flags=re.IGNORECASE)
        copied = deepcopy(expr)

        assert copied == expr
        assert copied is not expr


class TestExpressionTranspile:
    def test_transpile_from_compiled_pattern(self) -> None:
        compiled = re.compile(r"\d+", flags=re.IGNORECASE)
        expr = Expression.transpile(compiled)

        assert expr.pattern == r"\d+"
        assert expr.flags & re.IGNORECASE

    def test_transpile_from_expression(self) -> None:
        original = Expression(r"\d+", flags=re.IGNORECASE)
        expr = Expression.transpile(original)

        assert expr == original
        assert expr is not original


# =============================================================================
# Test: Expression - Search
# =============================================================================


class TestExpressionSearch:
    def test_search_finds_match(self, digit_pattern: Expression[str]) -> None:
        match = digit_pattern.search("abc 123 def")
        assert match is not None
        assert match.group() == "123"

    def test_search_returns_none_when_not_found(
        self, digit_pattern: Expression[str]
    ) -> None:
        match = digit_pattern.search("no digits here")
        assert match is None

    def test_search_with_required_true_returns_match(
        self, digit_pattern: Expression[str]
    ) -> None:
        match = digit_pattern.search("abc 123 def", required=True)
        assert match.group() == "123"

    def test_search_with_required_true_raises_on_no_match(
        self, digit_pattern: Expression[str]
    ) -> None:
        with pytest.raises(SearchNotFoundError) as exc_info:
            digit_pattern.search("no digits here", required=True)

        assert exc_info.value.input == "no digits here"

    def test_search_with_pos_and_endpos(self, digit_pattern: Expression[str]) -> None:
        match = digit_pattern.search("123 456 789", pos=4, endpos=7)
        assert match is not None
        assert match.group() == "456"


# =============================================================================
# Test: Expression - Match
# =============================================================================


class TestExpressionMatch:
    def test_match_at_beginning(self, digit_pattern: Expression[str]) -> None:
        match = digit_pattern.match("123 abc")
        assert match is not None
        assert match.group() == "123"

    def test_match_fails_if_not_at_beginning(
        self, digit_pattern: Expression[str]
    ) -> None:
        match = digit_pattern.match("abc 123")
        assert match is None

    def test_match_with_required_true_returns_match(
        self, digit_pattern: Expression[str]
    ) -> None:
        match = digit_pattern.match("123 abc", required=True)
        assert match.group() == "123"

    def test_match_with_required_true_raises_on_no_match(
        self, digit_pattern: Expression[str]
    ) -> None:
        with pytest.raises(MatchNotFoundError):
            digit_pattern.match("abc 123", required=True)

    def test_match_with_full_true(self, digit_pattern: Expression[str]) -> None:
        match = digit_pattern.match("123", full=True)
        assert match is not None

        match = digit_pattern.match("123 abc", full=True)
        assert match is None

    def test_match_with_pos_and_endpos(self, digit_pattern: Expression[str]) -> None:
        match = digit_pattern.match("abc123def", pos=3, endpos=6)
        assert match is not None
        assert match.group() == "123"


# =============================================================================
# Test: Expression - Fullmatch
# =============================================================================


class TestExpressionFullmatch:
    def test_fullmatch_succeeds_on_exact_match(
        self, digit_pattern: Expression[str]
    ) -> None:
        match = digit_pattern.fullmatch("12345")
        assert match is not None
        assert match.group() == "12345"

    def test_fullmatch_fails_on_partial_match(
        self, digit_pattern: Expression[str]
    ) -> None:
        match = digit_pattern.fullmatch("123 abc")
        assert match is None

    def test_fullmatch_with_required_true_returns_match(
        self, digit_pattern: Expression[str]
    ) -> None:
        match = digit_pattern.fullmatch("12345", required=True)
        assert match.group() == "12345"

    def test_fullmatch_with_required_true_raises_on_no_match(
        self, digit_pattern: Expression[str]
    ) -> None:
        with pytest.raises(MatchNotFoundError):
            digit_pattern.fullmatch("123 abc", required=True)


# =============================================================================
# Test: Expression - Find Operations
# =============================================================================


class TestExpressionFindall:
    def test_findall_returns_all_matches(self, digit_pattern: Expression[str]) -> None:
        result = digit_pattern.findall("a1b22c333d4444")
        assert result == ["1", "22", "333", "4444"]

    def test_findall_returns_empty_list_on_no_match(
        self, digit_pattern: Expression[str]
    ) -> None:
        result = digit_pattern.findall("no digits")
        assert result == []

    def test_findall_with_pos_and_endpos(self, digit_pattern: Expression[str]) -> None:
        result = digit_pattern.findall("111 222 333", pos=4, endpos=7)
        assert result == ["222"]

    def test_findall_with_groups(self) -> None:
        expr = Expression(r"(\d+)-(\d+)")
        result = expr.findall("1-2 and 3-4")
        assert result == [("1", "2"), ("3", "4")]


class TestExpressionFinditer:
    def test_finditer_returns_iterator_of_matches(
        self, digit_pattern: Expression[str]
    ) -> None:
        matches = list(digit_pattern.finditer("a1b22c333"))
        assert len(matches) == 3
        assert [m.group() for m in matches] == ["1", "22", "333"]

    def test_finditer_with_pos_and_endpos(self, digit_pattern: Expression[str]) -> None:
        matches = list(digit_pattern.finditer("111 222 333", pos=4, endpos=7))
        assert len(matches) == 1
        assert matches[0].group() == "222"


# =============================================================================
# Test: Expression - Split
# =============================================================================


class TestExpressionSplit:
    def test_split_basic(self) -> None:
        expr = Expression(r"\s+")
        result = expr.split("one two  three")
        assert result == ["one", "two", "three"]

    def test_split_with_maxsplit(self) -> None:
        expr = Expression(r"\s+")
        result = expr.split("one two three four", maxsplit=2)
        assert result == ["one", "two", "three four"]

    def test_split_with_groups(self) -> None:
        expr = Expression(r"(\s+)")
        result = expr.split("one two")
        assert result == ["one", " ", "two"]


# =============================================================================
# Test: Expression - Substitution
# =============================================================================


class TestExpressionSub:
    def test_sub_replaces_all_matches(self, digit_pattern: Expression[str]) -> None:
        result = digit_pattern.sub("X", "a1b22c333")
        assert result == "aXbXcX"

    def test_sub_with_count(self, digit_pattern: Expression[str]) -> None:
        result = digit_pattern.sub("X", "a1b22c333", count=2)
        assert result == "aXbXc333"

    def test_sub_with_callable(self, digit_pattern: Expression[str]) -> None:
        result = digit_pattern.sub(lambda m: f"[{m.group()}]", "a1b22c333")
        assert result == "a[1]b[22]c[333]"

    def test_sub_with_backreference(self) -> None:
        expr = Expression(r"(\w+) (\w+)")
        result = expr.sub(r"\2 \1", "hello world")
        assert result == "world hello"


class TestExpressionSubn:
    def test_subn_returns_tuple_with_count(
        self, digit_pattern: Expression[str]
    ) -> None:
        result, count = digit_pattern.subn("X", "a1b22c333")
        assert result == "aXbXcX"
        assert count == 3

    def test_subn_with_count_limit(self, digit_pattern: Expression[str]) -> None:
        result, count = digit_pattern.subn("X", "a1b22c333", count=2)
        assert result == "aXbXc333"
        assert count == 2


# =============================================================================
# Test: Expression - Check/Test/Validate
# =============================================================================


class TestExpressionCheck:
    def test_check_returns_true_on_full_match(
        self, email_pattern: Expression[str]
    ) -> None:
        assert email_pattern.check("user@example.com") is True

    def test_check_returns_false_on_no_match(
        self, email_pattern: Expression[str]
    ) -> None:
        assert email_pattern.check("not-an-email") is False

    def test_check_full_false_allows_partial_match(
        self, digit_pattern: Expression[str]
    ) -> None:
        assert digit_pattern.check("123abc", full=False) is True
        assert digit_pattern.check("123abc", full=True) is False

    def test_test_is_alias_for_check(self, email_pattern: Expression[str]) -> None:
        assert email_pattern.test("user@example.com") is True
        assert email_pattern.test("not-an-email") is False


class TestExpressionValidate:
    def test_validate_returns_string_on_match(
        self, email_pattern: Expression[str]
    ) -> None:
        result = email_pattern.validate("user@example.com")
        assert result == "user@example.com"

    def test_validate_raises_on_no_match(self, email_pattern: Expression[str]) -> None:
        with pytest.raises(ValueError) as exc_info:
            email_pattern.validate("not-an-email")

        assert "not-an-email" in str(exc_info.value)

    def test_validate_full_false_allows_partial_match(
        self, digit_pattern: Expression[str]
    ) -> None:
        result = digit_pattern.validate("123abc", full=False)
        assert result == "123abc"


# =============================================================================
# Test: Expression - Bytes Support
# =============================================================================


class TestExpressionBytes:
    def test_search_with_bytes(self) -> None:
        expr = Expression(rb"\d+")
        match = expr.search(b"abc 123 def")
        assert match is not None
        assert match.group() == b"123"

    def test_match_with_bytes(self) -> None:
        expr = Expression(rb"\d+")
        match = expr.match(b"123 abc")
        assert match is not None
        assert match.group() == b"123"

    def test_findall_with_bytes(self) -> None:
        expr = Expression(rb"\d+")
        result = expr.findall(b"a1b22c333")
        assert result == [b"1", b"22", b"333"]

    def test_sub_with_bytes(self) -> None:
        expr = Expression(rb"\d+")
        result = expr.sub(b"X", b"a1b22c333")
        assert result == b"aXbXcX"

    def test_check_with_bytes(self) -> None:
        expr = Expression(rb"\d+")
        assert expr.check(b"123") is True
        assert expr.check(b"abc") is False


# =============================================================================
# Test: define() helper function
# =============================================================================


class TestDefine:
    def test_define_creates_expression(self) -> None:
        expr = define(r"\d+")
        assert isinstance(expr, Expression)
        assert expr.pattern == r"\d+"

    def test_define_with_flags(self) -> None:
        expr = define(r"[a-z]+", flags=re.IGNORECASE)
        assert expr.flags == re.IGNORECASE

    def test_define_with_bytes(self) -> None:
        expr = define(rb"\d+")
        assert expr.pattern == rb"\d+"


# =============================================================================
# Test: Subber
# =============================================================================


class TestSubber:
    def test_create_with_pattern_string(self) -> None:
        subber = Subber("X", r"\d+")
        assert subber.replace == "X"

    def test_call_replaces_matches(self) -> None:
        subber = Subber("X", r"\d+")
        result = subber("a1b22c333")
        assert result == "aXbXcX"

    def test_call_with_count(self) -> None:
        subber = Subber("X", r"\d+")
        result = subber("a1b22c333", count=2)
        assert result == "aXbXc333"

    def test_n_method_returns_count(self) -> None:
        subber = Subber("X", r"\d+")
        result, count = subber.n("a1b22c333")
        assert result == "aXbXcX"
        assert count == 3

    def test_with_callable_replacement(self) -> None:
        subber = Subber(lambda m: f"[{m.group()}]", r"\d+")
        result = subber("a1b22")
        assert result == "a[1]b[22]"

    def test_with_flags(self) -> None:
        subber = Subber("X", r"[a-z]+", flags=re.IGNORECASE)
        result = subber("ABC def GHI")
        assert result == "X X X"

    def test_create_with_compiled_pattern_no_flags(self) -> None:
        compiled = re.compile(r"\d+")
        with pytest.raises(ValueError):
            Subber("X", compiled, flags=re.IGNORECASE)  # type: ignore

    def test_with_bytes(self) -> None:
        subber = Subber(b"X", rb"\d+")
        result = subber(b"a1b22c333")
        assert result == b"aXbXcX"


# =============================================================================
# Test: Structure
# =============================================================================


class PhoneStructure(Structure[str]):
    compiled = re.compile(r"(?P<area>\d{3})-(?P<exchange>\d{3})-(?P<number>\d{4})")

    @classmethod
    def parse(cls, string: str) -> dict[str, str]:
        match = cls.fullmatch(string, required=True)
        return match.groupdict()


class TestStructure:
    def test_flags_property(self) -> None:
        class FlaggedStructure(Structure[str]):
            compiled = re.compile(r"\d+", flags=re.IGNORECASE)

        instance = FlaggedStructure()
        assert instance.flags & re.IGNORECASE

    def test_match_returns_match(self) -> None:
        match = PhoneStructure.match("555-123-4567 extra")
        assert match is not None
        assert match.group("area") == "555"

    def test_match_required_true_raises(self) -> None:
        with pytest.raises(MatchNotFoundError):
            PhoneStructure.match("invalid", required=True)

    def test_match_required_false_returns_none(self) -> None:
        match = PhoneStructure.match("invalid", required=False)
        assert match is None

    def test_fullmatch_returns_match(self) -> None:
        match = PhoneStructure.fullmatch("555-123-4567")
        assert match is not None

    def test_fullmatch_fails_on_partial(self) -> None:
        match = PhoneStructure.fullmatch("555-123-4567 extra", required=False)
        assert match is None

    def test_fullmatch_required_true_raises(self) -> None:
        with pytest.raises(MatchNotFoundError):
            PhoneStructure.fullmatch("invalid", required=True)

    def test_search_returns_match(self) -> None:
        match = PhoneStructure.search("Call 555-123-4567 today")
        assert match is not None
        assert match.group() == "555-123-4567"

    def test_search_required_true_raises(self) -> None:
        with pytest.raises(SearchNotFoundError):
            PhoneStructure.search("no phone here", required=True)

    def test_search_required_false_returns_none(self) -> None:
        match = PhoneStructure.search("no phone here", required=False)
        assert match is None

    def test_findall(self) -> None:
        result = PhoneStructure.findall("555-123-4567 and 555-987-6543")
        assert len(result) == 2

    def test_finditer(self) -> None:
        matches = list(PhoneStructure.finditer("555-123-4567 and 555-987-6543"))
        assert len(matches) == 2

    def test_split(self) -> None:
        class Splitter(Structure[str]):
            compiled = re.compile(r"\s+")

        result = Splitter.split("one two three")
        assert result == ["one", "two", "three"]

    def test_sub(self) -> None:
        result = PhoneStructure.sub("XXX-XXX-XXXX", "Call 555-123-4567")
        assert result == "Call XXX-XXX-XXXX"

    def test_subn(self) -> None:
        result, count = PhoneStructure.subn("XXX", "555-123-4567 and 555-987-6543")
        assert count == 2

    def test_check_returns_true(self) -> None:
        assert PhoneStructure.check("555-123-4567") is True

    def test_check_returns_false(self) -> None:
        assert PhoneStructure.check("invalid") is False

    def test_check_full_false(self) -> None:
        assert PhoneStructure.check("555-123-4567 extra", full=False) is True
        assert PhoneStructure.check("555-123-4567 extra", full=True) is False

    def test_test_is_alias_for_check(self) -> None:
        assert PhoneStructure.test("555-123-4567") is True
        assert PhoneStructure.test("invalid") is False

    def test_validate_returns_string(self) -> None:
        result = PhoneStructure.validate("555-123-4567")
        assert result == "555-123-4567"

    def test_validate_raises_on_invalid(self) -> None:
        with pytest.raises(ValueError):
            PhoneStructure.validate("invalid")

    def test_custom_method(self) -> None:
        result = PhoneStructure.parse("555-123-4567")
        assert result == {"area": "555", "exchange": "123", "number": "4567"}


# =============================================================================
# Test: Matcher
# =============================================================================


class TestMatcher:
    def test_create_matcher(self) -> None:
        matcher = Matcher(r"\d+")
        assert matcher.pattern == r"\d+"
        assert matcher.flags == 0
        assert matcher.full is True

    def test_call_returns_true_on_match(self) -> None:
        matcher = Matcher(r"\d+")
        assert matcher("123") is True

    def test_call_returns_false_on_no_match(self) -> None:
        matcher = Matcher(r"\d+")
        assert matcher("abc") is False

    def test_full_true_requires_full_match(self) -> None:
        matcher = Matcher(r"\d+", full=True)
        assert matcher("123") is True
        assert matcher("123abc") is False

    def test_full_false_allows_partial_match(self) -> None:
        matcher = Matcher(r"\d+", full=False)
        assert matcher("123") is True
        assert matcher("123abc") is True
        assert matcher("abc123") is False  # match requires start of string

    def test_call_with_start_and_end(self) -> None:
        matcher = Matcher(r"\d+")
        assert matcher("abc123def", start=3, end=6) is True

    def test_get_returns_match_object(self) -> None:
        matcher = Matcher(r"\d+")
        match = matcher.get("123")
        assert match is not None
        assert match.group() == "123"

    def test_get_returns_none_on_no_match(self) -> None:
        matcher = Matcher(r"\d+")
        match = matcher.get("abc")
        assert match is None

    def test_get_required_true_returns_match(self) -> None:
        matcher = Matcher(r"\d+")
        match = matcher.get("123", 0, 3, required=True)
        assert match.group() == "123"

    def test_get_required_true_raises_on_no_match(self) -> None:
        matcher = Matcher(r"\d+")
        with pytest.raises(MatchNotFoundError):
            matcher.get("abc", 0, 3, required=True)

    def test_with_flags(self) -> None:
        matcher = Matcher(r"[a-z]+", flags=re.IGNORECASE)
        assert matcher("ABC") is True

    def test_hash(self) -> None:
        matcher1 = Matcher(r"\d+", flags=0, full=True)
        matcher2 = Matcher(r"\d+", flags=0, full=True)
        matcher3 = Matcher(r"\d+", flags=0, full=False)

        assert hash(matcher1) == hash(matcher2)
        assert hash(matcher1) != hash(matcher3)

        # Can be used in sets
        s = {matcher1}
        assert matcher2 in s

    def test_with_bytes(self) -> None:
        matcher = Matcher(rb"\d+")
        assert matcher(b"123") is True
        assert matcher(b"abc") is False


# =============================================================================
# Test: Generic Type Support
# =============================================================================


class TestGenericTypeSupport:
    def test_expression_class_getitem(self) -> None:
        # Should not raise
        expr_type = Expression[str]
        assert expr_type is not None

        expr_type = Expression[bytes]
        assert expr_type is not None

    def test_matcher_generic(self) -> None:
        str_matcher: Matcher[str] = Matcher(r"\d+")
        bytes_matcher: Matcher[bytes] = Matcher(rb"\d+")

        assert str_matcher("123") is True
        assert bytes_matcher(b"123") is True


# =============================================================================
# Test: Edge Cases
# =============================================================================


class TestEdgeCases:
    def test_empty_pattern(self) -> None:
        expr = Expression(r"")
        assert expr.check("") is True
        assert expr.check("anything", full=False) is True

    def test_empty_string_input(self) -> None:
        expr = Expression(r"\d*")
        assert expr.check("") is True

        expr2 = Expression(r"\d+")
        assert expr2.check("") is False

    def test_special_regex_characters(self) -> None:
        expr = Expression(r"\.\*\+\?\[\]\(\)\{\}\|\^\\\$")
        assert expr.check(".*+?[](){}|^\\$") is True

    def test_unicode_patterns(self) -> None:
        expr = Expression(r"[\u0400-\u04FF]+")  # Cyrillic
        assert expr.check("Привет") is True
        assert expr.check("Hello") is False

    def test_multiline_flag(self) -> None:
        expr = Expression(r"^\d+", flags=re.MULTILINE)
        result = expr.findall("123\n456\n789")
        assert result == ["123", "456", "789"]

    def test_dotall_flag(self) -> None:
        expr = Expression(r"a.b", flags=re.DOTALL)
        assert expr.check("a\nb") is True

        expr_no_flag = Expression(r"a.b")
        assert expr_no_flag.check("a\nb") is False

    def test_verbose_flag(self) -> None:
        pattern = r"""
            \d{3}  # area code
            -
            \d{4}  # number
        """
        expr = Expression(pattern, flags=re.VERBOSE)
        assert expr.check("555-1234") is True

    def test_very_long_string(self) -> None:
        expr = Expression(r"\d+")
        long_string = "a" * 100000 + "123" + "b" * 100000
        match = expr.search(long_string)
        assert match is not None
        assert match.group() == "123"

    def test_complex_pattern_with_lookahead(self) -> None:
        # Password: at least 8 chars, must contain digit and letter
        expr = Expression(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")
        assert expr.check("password1") is True
        assert expr.check("12345678") is False  # no letter
        assert expr.check("password") is False  # no digit
        assert expr.check("pass1") is False  # too short

    def test_complex_pattern_with_lookbehind(self) -> None:
        # Match digits only if preceded by $
        expr = Expression(r"(?<=\$)\d+")
        result = expr.findall("$100 and 200 and $300")
        assert result == ["100", "300"]

    def test_negative_lookahead(self) -> None:
        # Match 'foo' not followed by 'bar'
        expr = Expression(r"foo(?!bar)")
        assert expr.search("foobaz") is not None
        assert expr.search("foobar") is None

    def test_named_groups_access(self) -> None:
        expr = Expression(r"(?P<first>\w+)\s+(?P<last>\w+)")
        match = expr.match("John Doe", required=True)
        assert match.group("first") == "John"
        assert match.group("last") == "Doe"

    def test_non_capturing_groups(self) -> None:
        expr = Expression(r"(?:ab)+")
        match = expr.fullmatch("ababab")
        assert match is not None
        assert expr.groups == 0  # No capturing groups

    def test_backreference(self) -> None:
        # Match repeated words
        expr = Expression(r"(\w+)\s+\1")
        assert expr.search("the the") is not None
        assert expr.search("the a") is None

    def test_conditional_pattern(self) -> None:
        # Match optional area code with required format
        expr = Expression(r"(\d{3}-)?\d{3}-\d{4}")
        assert expr.check("555-123-4567") is True
        assert expr.check("123-4567") is True
        assert expr.check("5551234567") is False


# =============================================================================
# Test: Integration / Real-world Patterns
# =============================================================================


class TestRealWorldPatterns:
    def test_email_validation(self) -> None:
        # Simplified email pattern
        expr = Expression(r"^[\w.-]+@[\w.-]+\.\w{2,}$")

        assert expr.check("user@example.com") is True
        assert expr.check("user.name@example.co.uk") is True
        assert expr.check("user+tag@example.com") is False  # + not in \w
        assert expr.check("@example.com") is False
        assert expr.check("user@") is False

    def test_url_extraction(self) -> None:
        expr = Expression(r"https?://[\w.-]+(?:/[\w./-]*)?")

        text = "Visit https://example.com/path and http://test.org for more"
        urls = expr.findall(text)
        assert urls == ["https://example.com/path", "http://test.org"]

    def test_ip_address_validation(self) -> None:
        # IPv4 pattern (simplified, allows 999.999.999.999)
        expr = Expression(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")

        assert expr.check("192.168.1.1") is True
        assert expr.check("10.0.0.1") is True
        assert expr.check("192.168.1") is False
        assert expr.check("192.168.1.1.1") is False

    def test_date_parsing(self) -> None:
        expr = Expression(r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})")

        match = expr.match("2024-01-15", required=True)
        assert match.group("year") == "2024"
        assert match.group("month") == "01"
        assert match.group("day") == "15"

    def test_log_line_parsing(self) -> None:
        expr = Expression(
            r"\[(?P<level>\w+)\]\s+(?P<timestamp>[\d-]+\s[\d:]+)\s+-\s+(?P<message>.+)"
        )

        log_line = "[ERROR] 2024-01-15 10:30:45 - Connection failed"
        match = expr.match(log_line, required=True)

        assert match.group("level") == "ERROR"
        assert match.group("timestamp") == "2024-01-15 10:30:45"
        assert match.group("message") == "Connection failed"

    def test_html_tag_extraction(self) -> None:
        expr = Expression(r"<(\w+)[^>]*>.*?</\1>", flags=re.DOTALL)

        html = "<div class='test'>content</div>"
        assert expr.search(html) is not None

    def test_csv_field_splitting(self) -> None:
        # Split on comma, but not inside quotes
        expr = Expression(r',(?=(?:[^"]*"[^"]*")*[^"]*$)')

        line = 'a,b,"c,d",e'
        result = expr.split(line)
        assert result == ["a", "b", '"c,d"', "e"]

    def test_password_strength_validation(self) -> None:
        # At least 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special
        expr = Expression(
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        )

        assert expr.check("Passw0rd!") is True
        assert expr.check("password1!") is False  # no uppercase
        assert expr.check("PASSWORD1!") is False  # no lowercase
        assert expr.check("Password!!") is False  # no digit
        assert expr.check("Passw0rd") is False  # no special char
        assert expr.check("Pass0!") is False  # too short
