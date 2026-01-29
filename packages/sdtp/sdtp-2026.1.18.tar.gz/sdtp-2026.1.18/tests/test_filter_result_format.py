import pytest
import json
from sdtp.sdtp_table import RowTable, RemoteSDMLTable
from sdtp.sdtp_utils import json_serialize

from datetime import date

# Sample schema and data
schema = [
    {"name": "id", "type": "number"},
    {"name": "name", "type": "string"},
    {"name": "birthday", "type": "date"}
]
rows = [
    [1, "Alice", date(1980, 1, 1)],
    [2, "Bob", date(1990, 6, 15)]
]
rowtable = RowTable(schema, rows)

def _convert_row_to_dict(row, names):
    result = {}
    for i in range(len(names)): result[names[i]] = row[i]
    return result

row_tests = [
    {
        "columns": [],
        "list_expected": rows,
        "dicts_expected": [_convert_row_to_dict(row, rowtable.column_names()) for row in rows],
        "table_expected": rowtable
    },
    {
        "columns": ["id", "name"],
        "list_expected": [row[:2] for row in rows],
        "dicts_expected": [_convert_row_to_dict(row[:2], ["id", "name"]) for row in rows],
        "table_expected": RowTable(schema[:2], [row[:2] for row in rows])
    },
]

def test_rowtable_formats():
    for test in row_tests:
      columns = test["columns"]
      # (a) LIST FORMAT
      result_list = rowtable.get_filtered_rows(columns=columns, format='list')
      assert result_list == test["list_expected"]

      # (b) DICT FORMAT
      result_dicts = rowtable.get_filtered_rows(columns=columns, format='dict')
      assert result_dicts == test["dicts_expected"]

      # (c) SDML FORMAT
      result_table = rowtable.get_filtered_rows(columns=columns, format='sdml')
      expected_table = test["table_expected"]
      assert result_table.schema == expected_table.schema
      assert result_table.rows == expected_table.rows



test_row_table = RowTable(
    [
        
        {"name": "id", "type": "number"},
        {"name": "name", "type": "string"},
    ],
    [
        [1, "Alice"],
        [2, "Bob"]
    ]
)

from unittest.mock import patch

def fake_remote(self, filter_spec = None, columns = [], format="list"):
    return test_row_table


def test_remote_rowtable_reordering():
    # Simulate remote returning out-of-order schema
    remote_schema = [
        {"name": "name", "type": "string"},
        {"name": "id", "type": "number"},
        {"name": "birthday", "type": "date"}
    ]
    

    
    with patch.object(RemoteSDMLTable, "_get_filtered_rows_from_remote", fake_remote):
        # Now query for ["id", "name"] columns, expect result in that order
        remote_table = RemoteSDMLTable("remote_test", remote_schema, "http://fake")
        result = remote_table.get_filtered_rows(columns=["name", "id"], format="list")
        assert result == [["Alice", 1], ["Bob", 2]]
        columns = ["name", "id"]
        # For dict format
        result_dict = remote_table.get_filtered_rows(columns=columns, format="dict")
        assert result_dict == [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        # For sdml, make sure schema is ordered as requested
        result_table = remote_table.get_filtered_rows(columns=columns, format="sdml")
        # assert [col["name"] for col in result_sdml["schema"]] == ["id", "name"]
        assert result_table.column_names() == ['id', 'name']
        assert result_table.rows == [[1, "Alice"], [2, "Bob"]]

