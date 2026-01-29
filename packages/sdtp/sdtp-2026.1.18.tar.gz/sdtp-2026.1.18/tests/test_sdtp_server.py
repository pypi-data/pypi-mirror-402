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
Run tests on the table server
'''

import pytest
import json
import sys
from flask import Flask
import os
# Get the absolute path to the directory containing THIS file
file_dir = os.path.dirname(os.path.abspath(__file__))

# Add that directory to sys.path if not already present
if file_dir not in sys.path:
    sys.path.insert(0, file_dir)


sys.path.append('./src')
sys.path.append('../src')


from sdtp import sdtp_server_blueprint, jsonifiable_column, RowTable
from sdtp.sdtp_utils import json_serialize
app = Flask(__name__)
app.register_blueprint(sdtp_server_blueprint)

sdtp_server_blueprint.init_logging(__name__)

from server_test_tables import test_tables
# from server_test_tables import test_tables
for table_spec in test_tables:
    sdtp_server_blueprint.table_server.add_sdtp_table(table_spec['name'], table_spec['table'])

def _subsets(aList):
    if len(aList) == 0: return [[]]
    partial = _subsets(aList[:-1])
    full = [l + [aList[-1]] for l in partial]
    return full + partial

client = app.test_client()

def test_get_table_names():
    response = client.get('/get_table_names')
    assert response.status_code == 200
    result = response.json
    assert result is not None and len(result) == len(test_tables)
    names = [table["name"] for table in test_tables]
    for table_name in result:
        assert(table_name in names)

def test_get_tables():
    response = client.get('/get_tables')
    assert response.status_code == 200
    result = response.json
    table_dict = {}
    for table in test_tables:
        table_dict[table["name"]] = table["table"].schema
    assert(result == table_dict)

def test_get_table_schema():
    response = client.get('/get_table_schema')
    assert response.status_code  == 400
    response = client.get('/get_table_schema?table_name=foo')
    assert response.status_code  == 404
    for table in test_tables:
        response = client.get(f'/get_table_schema?table_name={table["name"]}')
        assert(response.status_code == 200)
        assert(response.json == table["table"].schema)

# Test the  column routes. We don't need to extensively check the functionality,
# since this was tested in test_sdtp_table and test_table_server.  All we need is
# to ensure that the results match when passed over the network, and we need
# to check the error conditions

#  the errors in get_range_spec and get_all_values are the same, so check
# for them in a common routine

def column_errors(route):
    response = client.get(route)
    assert response.status_code  == 400
    response = client.get(f'{route}?table_name=foo')
    assert response.status_code  == 400
    response = client.get(f'{route}?table_name=foo')
    assert response.status_code  == 400
    response = client.get(f'{route}?column_name=foo')
    assert response.status_code  == 400
    response = client.get(f'{route}?table_name=foo&column_name=name')
    assert response.status_code  == 404
    response = client.get(f'{route}?table_name=test1&column_name=foo')
    assert response.status_code  == 404

def test_get_range_spec():
    column_errors('/get_range_spec')
    for entry in test_tables:
        table = entry["table"]
        for column in table.schema:
            response = client.get(f'/get_range_spec?table_name={entry["name"]}&column_name={column["name"]}')
            assert(response.status_code == 200)
            table_result = table.range_spec(column["name"])
            expected_result = jsonifiable_column(table_result, column["type"])
            assert(response.json == expected_result)

def test_get_all_values():
    column_errors('/get_all_values')
    for entry in test_tables:
        table = entry["table"]
        for column in table.schema:
            response = client.get(f'/get_all_values?table_name={entry["name"]}&column_name={column["name"]}')
            assert(response.status_code == 200)
            table_result = table.all_values(column["name"])
            expected_result = jsonifiable_column(table_result, column["type"])
            assert(response.json == expected_result)


def test_get_column():
    column_errors('/get_column')
    for entry in test_tables:
        table = entry["table"]
        for column in table.schema:
            response = client.get(f'/get_column?table_name={entry["name"]}&column_name={column["name"]}')
            assert(response.status_code == 200)
            table_result = table.get_column(column["name"])
            expected_result = jsonifiable_column(table_result, column["type"])
            assert(response.json == expected_result)

# Test get_filtered_rows. Once again, we've thoroughly tested this in test_sdtp_table_and_filter
# and test_table_server, so all we need to do here is check error conditions and
# check that the filter_spec gets through OK and the result is what we expect -- IOW,
# test every error case and a couple of good cases

# A utility which does a query that should work -- runs the query both on 
# the server and the table, and makes sure that the answers match.

def _do_good_row_test(table_name, table, filter_spec = None, columns = None, format=None):
    json_arg = {"table": table_name}
    
    if filter_spec is not None: json_arg["filter"] = filter_spec
    if columns is not None: json_arg["columns"] = columns
    if format is not None: json_arg["result_format"] = format
    response = client.post('/get_filtered_rows', json = json_arg)
    assert response.status_code == 200
    result = table.get_filtered_rows(filter_spec = filter_spec, columns = columns, format=format)
    
    # response.json is ALMOST json -- Booleans are converted to upper case
    # so to match this, we jsonify the result coming out of 
    # table.get_filtered_rows and then turn it into Python serialized form
    if format == 'sdml': # result is a table and response is an sdml file
        table_form = response.json
        assert table_form is not None
        assert isinstance(result, RowTable)
        result_table = RowTable(table_form["schema"], table_form["rows"])
        assert result.schema == result_table.schema
        assert result.rows == result_table.rows
    else:
        jsonified_result = json.dumps(result, default=json_serialize)
        reread_result = json.loads(jsonified_result)
        assert response.json == reread_result
        

def test_get_filtered_rows():
    # test missing JSON body
    route = '/get_filtered_rows'
    response = client.post(route)
    assert response.status_code == 400
    # test missing table
    sdml_query = {'operator': 'IN_RANGE', 'column': 'age', 'min_val': 20, 'max_val': 30}
    response = client.post(route, json = {"filter": sdml_query})
    assert response.status_code == 400
    # test invalid spec
    sdml_query_bad = {'operator': 'IN_RANGE', 'min_val': 20, 'max_val': 30}
    response = client.post(route, json = {"table": "test3", "filter": sdml_query_bad})
    assert response.status_code == 400
    table = sdtp_server_blueprint.table_server.get_table('test3')
    # test valid
    _do_good_row_test("test3", table, filter_spec = sdml_query, format="sdml")

    # test with missing filter
    _do_good_row_test("test3", table, filter_spec = sdml_query, format="sdml")
    # add bad columns
    response = client.post(route, json = {"table": "test3", "filter": sdml_query, "columns" : "foo"})
    assert response.status_code == 400
    # add bad columns
    response = client.post(route, json = {"table": "test3", "filter": sdml_query, "columns" : ["name", "foo"]})
    assert response.status_code == 400
    # add good columns
    _do_good_row_test("test3", table, filter_spec = sdml_query, columns = ['name', 'age'])
    # specify empty columns
    _do_good_row_test("test3", table, filter_spec = sdml_query, columns = [])
    _do_good_row_test("test3", table, filter_spec = sdml_query, columns = ['name', 'age'], format="sdml")
    # specify empty columns
    _do_good_row_test("test3", table, filter_spec = sdml_query, columns = [], format="sdml")
