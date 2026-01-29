# BSD 3-Clause License

# Copyright (c) 2024-2025, The Regents of the University of California (Regents)
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import pytest
from sdtp  import (
    validate_column_spec,
    validate_table_schema,
)
from sdtp.sdtp_schema import _make_table_schema

# --- Valid Test Data ---

def test_valid_column_spec():
    col = {"name": "age", "type": "number"}
    validate_column_spec(col)  # Should not raise

def test_invalid_column_spec_missing_type():
    col = {"name": "age"}
    with pytest.raises(ValueError):
        validate_column_spec(col)

def test_invalid_column_spec_bad_type():
    col = {"name": "age", "type": "invalid_type"}
    with pytest.raises(ValueError):
        validate_column_spec(col)

def test_valid_table_schema():
    schema = {
        "type": "RowTable",
        "schema": [{"name": "name", "type": "string"}],
        "rows": [{"name": "Rick"}]  # Required field for row-type tables
    }
    validate_table_schema(schema) 

def test_valid_table_schema_with_schema():
    schema = {
        "type": "RowTable",
        "schema": [{"name": "name", "type": "string"}],
        "rows": [{"name": "Rick"}]  # Required field for row-type tables
    }
    validate_table_schema(schema) 

def test_invalid_table_schema_missing_columns():
    schema = {"not_columns": []}
    with pytest.raises(ValueError):
        validate_table_schema(schema)

def test_invalid_table_schema_bad_column():
    schema = {"columns": [{"name": "name", "type": "not_a_type"}]}
    with pytest.raises(ValueError):
        validate_table_schema(schema)

def test_make_table_schema_row():
    spec = {
        "type": "RowTable",
        "schema": [{"name": "foo", "type": "string"}],
        "rows": [["bar"]]
    }
    schema = _make_table_schema(spec)
    assert schema["type"] == "RowTable"
    assert schema["rows"] == [["bar"]]

def test_make_table_schema_remote():
    spec = {
        "type": "RemoteSDMLTable",
        "schema": [{"name": "foo", "type": "string"}],
        "url": "http://example.com",
        "table_name": "remote_table"
    }
    schema = _make_table_schema(spec)
    assert schema["type"] == "RemoteSDMLTable"
    assert schema["table_name"] == "remote_table"

def test_make_table_schema_invalid_type():
    spec = {
        "type": "magic",
        "schema": [{"name": "foo", "type": "string"}]
    }
    with pytest.raises(ValueError):
        _make_table_schema(spec)

from sdtp.sdtp_schema import make_table_schema

def test_make_table_schema_correct():
    cols = [("foo", "string"), ("bar", "number")]
    schema = make_table_schema(cols)
    assert schema == [{"name": "foo", "type": "string"}, {"name": "bar", "type": "number"}]

def test_make_table_schema_bad_type():
    cols = [("foo", "string"), ("bar", "bogus")]
    with pytest.raises(ValueError) as e:
        make_table_schema(cols)
    assert "bogus" in str(e.value)

def test_make_table_schema_empty():
    assert make_table_schema([]) == []

def test_make_table_schema_all_types():
    types = ["string", "number", "boolean", "date", "datetime", "timeofday"]
    cols = [(f"c{i}", t) for i, t in enumerate(types)]
    schema = make_table_schema(cols)
    assert all(col["type"] in types for col in schema)

def test_make_table_schema_duplicate_names():
    cols = [("foo", "string"), ("foo", "number")]
    # Current function allows duplicates; if you want to disallow, add a test for ValueError here
    schema = make_table_schema(cols)
    assert schema[0]["name"] == schema[1]["name"] == "foo"

def test_make_table_schema_case_sensitivity():
    cols = [("foo", "String")]
    with pytest.raises(ValueError):
        make_table_schema(cols)