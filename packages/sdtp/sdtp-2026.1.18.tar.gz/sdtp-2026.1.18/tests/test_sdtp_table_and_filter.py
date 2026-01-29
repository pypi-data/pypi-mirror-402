import pytest
from pydantic import ValidationError
from sdtp.sdtp_filter import InListFilter, AllFilter, AnyFilter, NoneFilter, make_filter
from sdtp.sdtp_table import RowTable


@pytest.fixture
def row_table():
    schema = [{"name": "a", "type": "number"}, {"name": "b", "type": "string"}]
    rows = [
        [1, "foo"],
        [2, "bar"],
        [3, "baz"],
        [2, "qux"],
    ]
    return RowTable(schema, rows)



def test_no_filter_returns_all_rows(row_table):
    result = row_table.get_filtered_rows()
    assert result == [
        [1, "foo"],
        [2, "bar"],
        [3, "baz"],
        [2, "qux"],
    ]

def test_inlist_filter(row_table):
    filt = {"operator": "IN_LIST", "column": "a", "values": [2]}
    result = row_table.get_filtered_rows(filt)
    assert result == [
        [2, "bar"],
        [2, "qux"],
    ]

def test_inlist_filter_format_list(row_table):
    filt = {"operator": "IN_LIST", "column": "a", "values": [2]}
    result = row_table.get_filtered_rows(filt, format='list')
    assert result == [
        [2, "bar"],
        [2, "qux"],
    ]

def test_inlist_filter_select_b(row_table):
    filt = {"operator": "IN_LIST", "column": "a", "values": [2]}
    result = row_table.get_filtered_rows(filt, columns=['b'])
    assert result == [
        ["bar"],
        ["qux"],
    ]

def test_any_filter(row_table):
    filt = {
        "operator": "ANY",
        "arguments": [
            {"operator": "IN_LIST", "column": "a", "values": [1]},
            {"operator": "IN_LIST", "column": "b", "values": ["baz"]},
        ],
    }
    result = row_table.get_filtered_rows(filt)
    assert result == [
        [1, "foo"],
        [3, "baz"],
    ]

def test_all_filter(row_table):
    filt = {
        "operator": "ALL",
        "arguments": [
            {"operator": "IN_LIST", "column": "a", "values": [2, 3]},
            {"operator": "IN_LIST", "column": "b", "values": ["qux", "baz"]},
        ],
    }
    result = row_table.get_filtered_rows(filt)
    assert result == [
        [3, "baz"],
        [2, "qux"],
    ]

def test_none_filter(row_table):
    filt = {
        "operator": "NONE",
        "arguments": [
            {"operator": "IN_LIST", "column": "a", "values": [2]},
        ],
    }
    result = row_table.get_filtered_rows(filt)
    assert result == [
        [1, "foo"],
        [3, "baz"],
    ]

def test_no_match_returns_empty(row_table):
    filt = {"operator": "IN_LIST", "column": "a", "values": [42]}
    result = row_table.get_filtered_rows(filt)
    assert result == []

def test_empty_table_returns_empty():
    schema = [{"name": "x", "type": "number"}]
    rows = []
    t = RowTable(schema, rows)
    filt = {"operator": "IN_LIST", "column": "x", "values": [1]}
    assert t.get_filtered_rows(filt) == []

def test_columns_arg_returns_selected_columns(row_table):
    filt = {"operator": "IN_LIST", "column": "a", "values": [2, 3]}
    result = row_table.get_filtered_rows(filt, columns=["b"])
    assert result == [["bar"], ["baz"], ["qux"]]

def test_dict_format(row_table):
    filt = {"operator": "IN_LIST", "column": "a", "values": [2]}
    result = row_table.get_filtered_rows(filt, format="dict")
    assert result == [
        {"a": 2, "b": "bar"},
        {"a": 2, "b": "qux"},
    ]

def test_dict_format_select_b(row_table):
    filt = {"operator": "IN_LIST", "column": "a", "values": [2]}
    result = row_table.get_filtered_rows(filt, format="dict", columns=["b"])
    assert result == [
        {"b": "bar"},
        {"b": "qux"},
    ]


def test_sdml_format(row_table):
    filt = {"operator": "IN_LIST", "column": "a", "values": [2]}
    result = row_table.get_filtered_rows(filt, format="sdml")
    # Should return a RowTable with the same schema, only matching rows
    assert hasattr(result, "rows")
    assert result.rows == [
        [2, "bar"],
        [2, "qux"],
    ]
    assert result.schema == row_table.schema

def test_sdml_format_select_b(row_table):
    filt = {"operator": "IN_LIST", "column": "a", "values": [2]}
    result = row_table.get_filtered_rows(filt, format="sdml", columns=["b"])
    assert hasattr(result, "rows")
    assert result.rows == [
        ["bar"],
        ["qux"],
    ]
    assert result.schema == [row_table.schema[1]]

def test_empty_any_filter(row_table):
    filt = {"operator": "ANY", "arguments": []}
    # Should match no rows
    result = row_table.get_filtered_rows(filt)
    assert result == []

def test_empty_all_filter(row_table):
    filt = {"operator": "ALL", "arguments": []}
    # Should match all rows (vacuous truth)
    result = row_table.get_filtered_rows(filt)
    assert result == row_table.rows

def test_empty_none_filter(row_table):
    filt = {"operator": "NONE", "arguments": []}
    # Should match all rows (since none of zero match is true)
    result = row_table.get_filtered_rows(filt)
    assert result == row_table.rows


def test_filter_missing_column(row_table):
    # Filtering on a column that doesn't exist: should return empty (or, if you want, raise)
    filt = {"operator": "IN_LIST", "column": "z", "values": [1]}
    result = row_table.get_filtered_rows(filt)
    assert result == []

def test_bad_operator(row_table):
    filt = {"operator": "NOT_A_REAL_OP", "column": "a", "values": [1]}
    with pytest.raises(ValueError):
        row_table.get_filtered_rows(filt)

def test_bad_filter_spec(row_table):
    # Missing 'values' for IN_LIST
    filt = {"operator": "IN_LIST", "column": "a"}
    with pytest.raises(Exception):  # Could be ValueError, ValidationError, etc.
        row_table.get_filtered_rows(filt)

def test_inlist_bad_value_type(row_table):
    # values includes a dict, which can't be compared
    filt = {"operator": "IN_LIST", "column": "a", "values": [1, {"bad": "type"}]}
    # Should not raise, just not match
    with pytest.raises(ValidationError):
        result = row_table.get_filtered_rows(filt)
        assert result == [[1, "foo"]]
from datetime import date, datetime

def test_filter_with_date_strings_and_objects():
    schema = [{"name": "d", "type": "date"}, {"name": "val", "type": "number"}]
    rows = [
        [date(2023, 1, 1), 1],
        [date(2024, 1, 1), 2],
        [date(2025, 1, 1), 3],
    ]
    t = RowTable(schema, rows)
    # Filter with string, should be parsed to date
    filt = {"operator": "IN_LIST", "column": "d", "values": ["2024-01-01"]}
    result = t.get_filtered_rows(filt)
    assert result == [[date(2024, 1, 1), 2]]
    # Filter with date object, should match too
    filt2 = {"operator": "IN_LIST", "column": "d", "values": [date(2025, 1, 1).isoformat()]}
    result2 = t.get_filtered_rows(filt2)
    assert result2 == [[date(2025, 1, 1), 3]]

def test_filter_type_coercion_int_vs_str(row_table):
    # All table values for 'a' are ints, but filter with stringified ints
    filt = {"operator": "IN_LIST", "column": "a", "values": ["2"]}
    # Should not match unless your parse_iso can coerce int<->str (which it shouldn’t for numbers!)
    result = row_table.get_filtered_rows(filt)
    assert result == []

def test_filter_type_coercion_float_vs_int(row_table):
    # Filtering for float that matches int in row
    filt = {"operator": "IN_LIST", "column": "a", "values": [2.0]}
    result = row_table.get_filtered_rows(filt)
    # Python compares 2 == 2.0 as True
    assert result == [[2, "bar"], [2, "qux"]]

def test_filter_type_coercion_datetime_vs_string():
    schema = [{"name": "dt", "type": "datetime"}, {"name": "val", "type": "number"}]
    dt1 = datetime(2023, 1, 1, 12)
    dt2 = datetime(2023, 1, 1, 13)
    rows = [
        [dt1, 1],
        [dt2, 2],
    ]
    t = RowTable(schema, rows)
    # Filter with ISO string
    filt = {"operator": "IN_LIST", "column": "dt", "values": ["2023-01-01T13:00:00"]}
    result = t.get_filtered_rows(filt)
    assert result == [[dt2, 2]]



def test_get_filtered_rows_respects_column_order():
    schema = [
        {'name': 'A', 'type': 'number'},
        {'name': 'B', 'type': 'string'},
        {'name': 'C', 'type': 'number'},
        {'name': 'D', 'type': 'boolean'},
    ]
    rows = [
        [1, 'foo', 1.1, True],
        [2, 'bar', 2.2, False],
    ]
    table = RowTable(schema, rows)

    # Case 1: Partial, out-of-schema order ['D', 'B']
    requested_columns = ['D', 'B']
    result_rows_partial = [
        [True, 'foo'],
        [False, 'bar'],
    ]
    schema_partial = [
        {'name': 'D', 'type': 'boolean'},
        {'name': 'B', 'type': 'string'},
    ]
    dict_partial = [
        {'D': True, 'B': 'foo'},
        {'D': False, 'B': 'bar'},
    ]

    result = table.get_filtered_rows(columns=requested_columns)
    assert result == result_rows_partial

    result = table.get_filtered_rows(columns=requested_columns, format='sdml')
    assert result.rows == result_rows_partial
    assert result.schema == schema_partial

    result = table.get_filtered_rows(columns=requested_columns, format='dict')
    assert result == dict_partial

    # Case 2: All columns, out-of-schema order ['C', 'A', 'D', 'B']
    requested_columns = ['C', 'A', 'D', 'B']
    result_rows_full = [
        [1.1, 1, True, 'foo'],
        [2.2, 2, False, 'bar'],
    ]
    schema_full = [
        {'name': 'C', 'type': 'number'},
        {'name': 'A', 'type': 'number'},
        {'name': 'D', 'type': 'boolean'},
        {'name': 'B', 'type': 'string'},
    ]
    dict_full = [
        {'C': 1.1,  'A': 1, 'D': True, 'B': 'foo'},
        {'C': 2.2,  'A': 2, 'D': False, 'B': 'bar'},
    ]

    result = table.get_filtered_rows(columns=requested_columns)
    assert result == result_rows_full

    result = table.get_filtered_rows(columns=requested_columns, format='sdml')
    assert result.rows == result_rows_full
    assert result.schema == schema_full

    result = table.get_filtered_rows(columns=requested_columns, format='dict')
    assert result == dict_full