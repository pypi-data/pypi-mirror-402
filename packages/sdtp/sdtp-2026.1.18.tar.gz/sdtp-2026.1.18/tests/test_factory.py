import pytest
from sdtp.sdtp_filter import make_filter

def test_make_filter_atomic():
    spec = {
        "operator": "IN_LIST",
        "column": "foo",
        "values": [1, 2, 3]
    }
    filt = make_filter(spec)
    assert filt.operator == "IN_LIST"
    assert filt.column == "foo"
    assert filt.values == [1, 2, 3]

def test_make_filter_compound():
    spec = {
        "operator": "ALL",
        "arguments": [
            {"operator": "IN_LIST", "column": "foo", "values": [1,2,3]},
            {"operator": "GE", "column": "bar", "value": 10}
        ]
    }
    filt = make_filter(spec)
    assert filt.operator == "ALL"
    assert len(filt.arguments) == 2
    assert filt.arguments[0].operator == "IN_LIST"
    assert filt.arguments[1].operator == "GE"

def test_make_filter_unknown_operator():
    bad_spec = {
        "operator": "MADE_UP",
        "column": "foo",
        "values": [1]
    }
    with pytest.raises(ValueError):
        make_filter(bad_spec)
def test_inlistfilter_private_attr_parsing():
    spec = {
        "operator": "IN_LIST",
        "column": "foo",
        "values": ["2024-01-01", "2024-01-02"]
    }
    filt = make_filter(spec)
    # parse_iso should parse these to date objects (assuming your parse_iso does)
    import datetime
    assert filt._compare_values[0] == datetime.date(2024, 1, 1)
    assert filt._compare_values[1] == datetime.date(2024, 1, 2)

def test_gefilter_private_attr_parsing():
    spec = {
        "operator": "GE",
        "column": "foo",
        "value": "2024-01-01"
    }
    filt = make_filter(spec)
    import datetime
    assert filt._compare_value == datetime.date(2024, 1, 1)

def test_regexfilter_private_attr_parsing():
    spec = {
        "operator": "REGEX_MATCH",
        "column": "foo",
        "expression": r"^a\d{3}z$"
    }
    filt = make_filter(spec)
    import re
    assert isinstance(filt._regex, re.Pattern)
    assert filt._regex.pattern == r"^a\d{3}z$"
