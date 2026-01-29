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
'''
Run tests on the table server, the middleware that sits between the data plane structures
and the data plane server
'''
import pytest
import sys

sys.path.append('src')
sys.path.append('tests')

from sdtp import TableServer, TableNotFoundException, ColumnNotFoundException
from sdtp import RowTable
from sdtp import InvalidDataException, SDML_STRING
import os
from json import load

TEST_URL_DIR = 'https://raw.githubusercontent.com/engageLively/sdtp/main/tests/tables/'

from sdtp.table_server import _check_dict_and_keys, _check_type
def test_check_type():
    _check_type(3, int, 'Int type check test')
    _check_type('foo', str, 'String type check test')
    _check_type({'foo': 2}, dict, 'Dict  type check test')
    test_table = RowTable([{"name": "a", "type": SDML_STRING}], [['foo']])
    _check_type(test_table, RowTable, 'RowTable type check test')
    with pytest.raises(AssertionError):
        _check_type(None, str, 'foo')
    with pytest.raises(AssertionError):
        _check_type(3, str, 'foo')
    with pytest.raises(AssertionError):
        _check_type('foo', int, 'foo')
    with pytest.raises(AssertionError):
        _check_type(3, RowTable, 'foo')
    with pytest.raises(AssertionError):
        _check_type(test_table, str, 'foo')

def test_check_dict_and_keys():
    test_dict = {'a': '1', 'b': '2'}
    _check_dict_and_keys(test_dict, {'a', 'b'}, ' dictionary test 1', 'test_dict')
    _check_dict_and_keys(test_dict, {'a'}, ' dictionary test 2', 'test_dict')
    _check_dict_and_keys(test_dict, {}, ' dictionary test 3', 'test_dict')
    _check_dict_and_keys(test_dict, None, ' dictionary test 4', 'test_dict')
    with pytest.raises(AssertionError):
        _check_dict_and_keys(None, {'a', 'b'}, ' dictionary test 5', 'test_dict')
    with pytest.raises(AssertionError):
        _check_dict_and_keys('foo', {'a', 'b'}, ' dictionary test 6', 'test_dict')
    with pytest.raises(AssertionError):
        _check_dict_and_keys(test_dict, {'a', 'c'}, ' dictionary test 7', 'test_dict')
    


def _check_table_key_present(server, key, table):
    assert(key in server.servers.keys())
    assert(server.servers[key] == table)
    
        

def test_add_table():
    test_table = RowTable([{"name": "a", "type": SDML_STRING}], [['foo']])
    server = TableServer()
    
    # add a table and make sure it's in the list
    server.add_sdtp_table('foo', test_table)
    _check_table_key_present(server, 'foo', test_table)
    test_table_1 = RowTable([{"name": "b", "type": SDML_STRING}], [['foo']])
    # check to make sure add_table replaces an existing table if the key is the same
    server.add_sdtp_table('foo', test_table_1)
    _check_table_key_present(server, 'foo', test_table_1)


def test_add_sdtp_table_from_dictionary():
    schema = [{"name": "a", "type": SDML_STRING}]
    rows = [['Alice']]
    test_table_spec_row = {'type': 'RowTable', 'schema': schema, 'rows': rows}
    test_table_spec_test = {'type': 'ServerTestTable', 'schema': schema, 'rows': rows}
    server = TableServer()
    
    # test for a non-existent factory.  Haven't added SDMLTestTableFactory yet
    with pytest.raises(InvalidDataException):
        server.add_sdtp_table_from_dictionary('test_table', test_table_spec_test)
    # test for a valid factory (make sure it's added)
    server.add_sdtp_table_from_dictionary('row_table',  test_table_spec_row)
    assert('row_table' in server.servers.keys())
    
# test_add_sdtp_table_from_dictionary()

def test_get_all_tables():
    # check an empty server
    server = TableServer()
    assert(len(server.get_all_tables()) == 0)
    schema = [{"name": "a", "type": SDML_STRING}]
    rows = [['Alice']]
    rows2 = [['Bob']]
    table = RowTable(schema, rows)
    table1 = RowTable(schema, rows2)
    # check getting a table works
    server.add_sdtp_table('table1',  table)
    assert(list(server.get_all_tables()) == [table])
    # check making sure adding a table with the same name overwrites, doesn't add
    server.add_sdtp_table('table1', table1)
    assert(list(server.get_all_tables()) == [table1])
    # check adding a table
    server.add_sdtp_table('table', table)
    table_list = server.get_all_tables()
    assert(len(table_list) == 2)
    assert(table in table_list)
    assert(table1 in table_list)

# server_test_tables is in the same directory as the tests

from server_test_tables import test_tables

def test_get_table():
    table_server = TableServer()
    # Test getting tables, including all corner cases
    # Table -- None and bad key
    with pytest.raises(TableNotFoundException) as err:
        table_server.get_table(None)
    with pytest.raises(TableNotFoundException) as err:
        table_server.get_table('foo')
    # For the tables, first, before we add we should get an error,
    # and after we add should get the table back
    for entry in test_tables:
        with pytest.raises(TableNotFoundException) as err:
            table_server.get_table(entry['name'])
        table_server.add_sdtp_table(entry['name'], entry['table'])
        found = table_server.get_table(entry['name'])
        assert(found == entry['table'])
    
table_server = TableServer()

def test_table_and_column_not_found_errors():
    # check that it appropriately handles missing tables, and checks for these in the get_all_values
    # route.  The same error-checking code is used in range_spec and get_column, so checking once 
    # is plenty.  As a side effect adds the test_tables to the server for subsequent tests
    with pytest.raises(TableNotFoundException) as err:
        table_server.get_all_values(None, 'foo')
    with pytest.raises(TableNotFoundException) as err:
        table_server.get_all_values('foo', 'foo')
    for entry in test_tables:
        with pytest.raises(TableNotFoundException) as err:
            table_server.get_all_values(entry['name'], 'foo')
        table_server.add_sdtp_table(entry['name'], entry['table'])
        # test bad column
        with pytest.raises(AssertionError) as err:
            table_server.get_all_values(entry['name'], None)
            # 'foo' is a name that we never use as a column name
        with pytest.raises(ColumnNotFoundException) as err:
            table_server.get_all_values(entry['name'], 'foo')
        # for each good table, good column pair get_all_values should match table.all_values

       

def test_get_all_values():
    # Error cases were checked above, so just make sure it handles the case where the column an dtable are valid
    for entry in test_tables:
        
        table = entry['table']
        for column in table.schema:
            assert(table_server.get_all_values(entry['name'], column['name']) == table.all_values(column['name']))
            
        

def test_get_range_spec():
    # Error cases were checked above, so just make sure it handles the case where the column an dtable are valid
    for entry in test_tables:
        table = entry['table']
        for column in table.schema:
            assert(table_server.get_range_spec(entry['name'], column['name']) == table.range_spec(column['name']))
            

def test_get_column():
    # Error cases were checked above, so just make sure it handles the case where the column an dtable are valid
    for entry in test_tables:
        table = entry['table']
        for column in table.schema:
            assert(table_server.get_column(entry['name'], column['name']) == table.get_column(column['name']))

import tempfile
import json


def test_table_server_load_file():
    # Prepare a simple SDML table dict
    table_spec = {
        "type": "RowTable",
        "schema": [{"name": "a", "type": "string"}],
        "rows": [["Alice"], ["Bob"]],
    }
    config = [{
        "name": "disk_table",
        "load_spec": {
            "location_type": "file",
            "path": None  # To be filled
        }
    }]
    # Write the table spec to a temp file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as tf:
        json.dump(table_spec, tf)
        tf.flush()
        config[0]["load_spec"]["path"] = tf.name
        # Write config file to temp file
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as cf:
            json.dump(config, cf)
            cf.flush()
            # Now initialize server
            server = TableServer()
            server.init_from_config(cf.name)
            t = server.get_table("disk_table")
            assert t.schema == table_spec["schema"]
            assert t.rows == table_spec["rows"] # type: ignore


def test_table_server_load_http(monkeypatch):
    # The "remote" table data you want to serve
    fake_table = {
        "type": "RowTable",
        "schema": [{"name": "a", "type": "string"}],
        "rows": [["Alice"], ["Bob"]],
    }

    class FakeResponse:
        def __init__(self, json_data):
            self._json = json_data
        def raise_for_status(self): pass
        def json(self): return self._json

    def fake_get(url, headers=None):
        return FakeResponse(fake_table)

    # Patch requests.get only in this test
    monkeypatch.setattr("requests.get", fake_get)

    config = [{
        "name": "remote_table",
        "load_spec": {
            "location_type": "uri",
            "url": "http://doesntmatter/test_table.json"
        }
    }]
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as cf:
        json.dump(config, cf)
        cf.flush()
        server = TableServer()
        server.init_from_config(cf.name)
        t = server.get_table("remote_table")
        # print(fake_table)
        assert t.schema == fake_table["schema"]
        assert t.rows == fake_table["rows"] # type: ignore
