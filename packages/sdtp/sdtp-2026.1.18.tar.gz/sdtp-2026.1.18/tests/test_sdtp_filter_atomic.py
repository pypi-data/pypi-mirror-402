import pytest
from datetime import date, datetime, time
import sys

# Import your filter classes here:
from sdtp.sdtp_filter import InListFilter, GEFilter, GTFilter, LEFilter, LTFilter, RegexFilter, ColumnFilter

# Dummy parse_iso to mimic your real one for test (update if needed)
def parse_iso(val):
    if isinstance(val, str):
        for dt_type in (date, datetime, time):
            try:
                return dt_type.fromisoformat(val)
            except Exception:
                continue
    return val

# === InListFilter ===
def test_in_list_filter_match_and_nonmatch():
    filt = InListFilter(operator="IN_LIST", column="foo", values=[1, 2, 3])
    columns = ["foo", "bar"]
    assert filt.matches([2, "hello"], columns)  # match
    assert not filt.matches([5, "hello"], columns)  # non-match

def test_in_list_filter_empty_list():
    filt = InListFilter(operator="IN_LIST", column="foo", values=[])
    columns = ["foo", "bar"]
    assert not filt.matches([1, "hello"], columns)  # always non-match

def test_in_list_filter_bad_type():
    filt = InListFilter(operator="IN_LIST", column="foo", values=[1, 2, 3])
    columns = ["foo", "bar"]
    assert not filt.matches(["a string", "hello"], columns)  # bad type

def test_in_list_filter_none_value():
    filt = InListFilter(operator="IN_LIST", column="foo", values=[1, 2, 3])
    columns = ["foo", "bar"]
    assert not filt.matches([None, "hello"], columns)  # None in value

# === Comparison Filters ===
@pytest.mark.parametrize("FilterClass, op, val, match_val, no_match_val", [
    (GEFilter, "GE", 5, 5, 4),
    (GTFilter, "GT", 5, 6, 5),
    (LEFilter, "LE", 5, 5, 6),
    (LTFilter, "LT", 5, 4, 5)
])
def test_compare_filter_match_and_nonmatch(FilterClass, op, val, match_val, no_match_val):
    filt = FilterClass(operator=op, column="foo", value=val)
    columns = ["foo", "bar"]
    assert filt.matches([match_val, "zzz"], columns)
    assert not filt.matches([no_match_val, "zzz"], columns)

@pytest.mark.parametrize("FilterClass, op", [
    (GEFilter, "GE"), (GTFilter, "GT"),
    (LEFilter, "LE"), (LTFilter, "LT")
])
def test_compare_filter_bad_type(FilterClass, op):
    filt = FilterClass(operator=op, column="foo", value=5)
    columns = ["foo", "bar"]
    assert not filt.matches(["not-an-int", "zzz"], columns)

@pytest.mark.parametrize("FilterClass, op", [
    (GEFilter, "GE"), (GTFilter, "GT"),
    (LEFilter, "LE"), (LTFilter, "LT")
])
def test_compare_filter_none_value(FilterClass, op):
    filt = FilterClass(operator=op, column="foo", value=5)
    columns = ["foo", "bar"]
    assert not filt.matches([None, "zzz"], columns)

@pytest.mark.parametrize("FilterClass, op, typ, v, match_val, no_match_val", [
    (GEFilter, "GE", date, date(2024, 1, 1).isoformat(), date(2024, 1, 2), date(2023, 12, 31)),
    (GTFilter, "GT", date, date(2024, 1, 1).isoformat(), date(2024, 1, 2), date(2024, 1, 1)),
    (LEFilter, "LE", date, date(2024, 1, 1).isoformat(), date(2024, 1, 1), date(2024, 1, 2)),
    (LTFilter, "LT", date, date(2024, 1, 1).isoformat(), date(2023, 12, 31), date(2024, 1, 1)),
    (GEFilter, "GE", datetime, datetime(2024, 1, 1, 12, 0).isoformat(), datetime(2024, 1, 1, 13, 0), datetime(2023, 12, 31, 23, 59)),
    (LEFilter, "LE", time, time(12, 0).isoformat(), time(12, 0), time(13, 0))
])
def test_compare_filter_date_time(FilterClass, op, typ, v, match_val, no_match_val):
    filt = FilterClass(operator=op, column="foo", value=v)
    columns = ["foo", "bar"]
    assert filt.matches([match_val, "zzz"], columns)
    assert not filt.matches([no_match_val, "zzz"], columns)

# === RegexFilter ===
def test_regex_filter_match_and_nonmatch():
    filt = RegexFilter(operator="REGEX_MATCH", column="foo", expression=r"^a\d{3}z$")
    columns = ["foo", "bar"]
    assert filt.matches(["a123z", "zzz"], columns)
    assert not filt.matches(["b123z", "zzz"], columns)

def test_regex_filter_bad_type():
    filt = RegexFilter(operator="REGEX_MATCH", column="foo", expression=r"\d+")
    columns = ["foo", "bar"]
    assert not filt.matches([1234, "zzz"], columns)  # int not str

def test_regex_filter_none_value():
    filt = RegexFilter(operator="REGEX_MATCH", column="foo", expression=r"\d+")
    columns = ["foo", "bar"]
    assert not filt.matches([None, "zzz"], columns)

def test_regex_filter_empty_pattern():
    filt = RegexFilter(operator="REGEX_MATCH", column="foo", expression=r"")
    columns = ["foo", "bar"]
    assert filt.matches(["", "zzz"], columns)
    assert not filt.matches(["nonempty", "zzz"], columns)

def test_regex_filter_invalid_pattern():
    # Should raise error on bad pattern
    with pytest.raises(Exception):
        RegexFilter(operator="REGEX_MATCH", column="foo", expression=r"(")

# === ColumnFilter base: Missing column ===
def test_column_filter_missing_column():
    class DummyFilter(ColumnFilter):
        def matches_value(self, value):
            return True  # doesn't matter

    filt = DummyFilter(operator="DUMMY", column="not_there")
    columns = ["foo", "bar"]
    row = [1, 2]
    assert not filt.matches(row, columns)

