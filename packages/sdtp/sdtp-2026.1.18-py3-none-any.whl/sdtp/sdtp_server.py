'''
A framework to easily and quickly implement a web server which serves tables according to
the SDTP REST  protocol.  This implements the URL methods get_filtered_rows, get_all_values,
and get_numeric_spec.  It parses the arguments, checking for errors, takes the
table argument, looks up the appropriate SDMLTable to serve for that table, and
then calls the method on that server to serve the request.  If no exception is thrown,
returns a 200 with the result as a JSON structure, and if an exception is thrown, returns
a 400 with an approrpriate error message.
All of the methods here except for add_sdtp_table are simply route targets: none are
designed for calls from any method other than flask.
The way to use this is very simple:
1. For each Table to be served, create an instance of sdtp_table.SDMLTable
2. Call add_sdtp_table(table_name, sdtp_table)
After that, requests for the named table will be served by the created data server.

'''

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

import logging
from json import JSONDecodeError, loads, dumps
import datetime
from flask import Blueprint, abort, jsonify, request, Response
from typing import NoReturn
from .sdtp_utils import InvalidDataException, json_serialize
from .sdtp_filter import check_valid_spec
from .table_server import TableServer, TableNotFoundException, ColumnNotFoundException
from .sdtp_table import SDMLTable, RowTable
from .sdtp_table import ALLOWED_FILTERED_ROW_RESULT_FORMATS, DEFAULT_FILTERED_ROW_RESULT_FORMAT
class SDTPServer(Blueprint):
    '''
    An SDTP Server.  This is just an overlay on a Flask Blueprint, added so 
    we can expose initialize methods to the application
    '''
    def __init__(self, name, import_name, **kwargs):
        super(SDTPServer, self).__init__(name, import_name, **kwargs)
        self.table_server = TableServer()
        self.logger = None
        self.ROUTES = [
            {"url": "/get_table_names", "method": "GET", "headers": "None",
                "description": "Return the list of table names"},
            {"url": "/get_table_schema?table_name string, required", "method": "GET", "headers": "None",
                "description": 'Returns the schema of the table as a list of objects.  Each object will  contain the fields "name" and "type", where "type"is an SDML type.'},
            {"url": "/get_tables", "method": "GET", "headers": "None",
                "description": 'Dumps a JSONIfied dictionary of the form:{table_name: <table_schema>}, where <table_schema> is a dictionary{"name": name, "type": type}'},
            {"url": "/get_filtered_rows", "method": "POST",
                "body": {"table": " required, the name of the table to get the rows from",
                        "columns": " If  present, a list of the names of the columns to fetch",
                        "filter": " optional, a filter_spec in the SDTP filter language"},
                
                "description": "Get the rows from table table which match filter filter.  If columns is present, return only those columns.  Returns a simple list of lists of columns"},
            {"url": "/get_range_spec?column_name string, required&table_name string, required", "method": "GET",
                "headers": "None",
                "description": "Get the  minimum and maximum values for column column_name in table table_name, returned as a list [min_val, max_val]."},
            {"url": "/get_all_values?column_name string, required&table_name string, required", "method": "GET",
                "headers": "None",
                "description": "Get all the distinct values for column column_name in table table_name, returned as a sorted list."},
            {"url": "/get_column?column_name string, required&table_name string, required", "method": "GET",
                "headers": "None",
                "description": "Return the column <column_name> in table <table_name> as a list.  The behavior is undefined when the table is infinite"},
            
        ]

    def init_logging(self, __name__, logfile = None):
        if logfile is None:
            logfile = f'/tmp/sdtp_server_{datetime.datetime.now().isoformat()}.log'
        logging.basicConfig(filename = logfile, level = logging.INFO)
        self.logger = logging.getLogger(__name__)

sdtp_server_blueprint = SDTPServer('sdtp_server', __name__)


# utilities

def _log_and_abort(message, code=400)->NoReturn:
    '''
    Sent an abort with error code (default 400) and log the error message.  Utility, internal use only

    Arguments:
        message: string with the message to be logged/sent
    '''
    if sdtp_server_blueprint.logger is not None:
        sdtp_server_blueprint.logger.error(message)
    abort(code, message)


def _table_server(request_api, table_name:str)->SDMLTable:
    '''
    Utility for _get_table_server and _get_table_servers.  Get the server for  table_name and return it.
    Aborts the request with a 400 if the table isn't found.  Aborts with a 403 if the
    table isn't authorized

    Arguments:
        request_api: api  of the request
        table_name: the table to get
    '''
    try:
        return sdtp_server_blueprint.table_server.get_table(table_name)
    except TableNotFoundException:
        msg = f'Table {table_name} not found for request {request_api}'
        code = 404
        _log_and_abort(msg, code)

    
def _get_json_body_from_post_request_data(request):
    '''
    Get the json body (if any) from the data field of a  request.  The JSON
    body might be as a dict or as a string; if the latter, decode it
    Arguments:
        request: a Flask request 
    Returns:
        A dictionary the json decode of the body, or None for a decode failure, no
        data
    '''
    if request.data is None: return None
    if not type(request.data) in {bytes, str}: return request.data
    try:
        return loads(request.data)
    except JSONDecodeError:
        return None

def _get_post_argument(key, form_data, data, get_multi = False):
    '''
    Get the value of the POST argument key from a request.  These can be either in the
    form (which is a MultiDict) or in the data body.  Accepts both
    to ensure that spurious errors aren't thrown
    
    Arguments:
        key: the key for the request
        form_data: the contents of request.form
        data: the contents of request.data, parsed into a JSON dict
        get_multi: if true and the results are in a MultiDict (request.form) returns a list of all values
    Returns:
        The value, or None if it is not present.  Raised no exceptions
    '''
    if form_data:
        try:
            result = form_data.getlist(key) if get_multi else form_data.get(key)
            if result is not None: return result
        except KeyError:
            pass
    if data:
        try:
            return data[key]
        except KeyError:
            return None
    return None


def _check_required_parameters(route, required_parameters):
    '''
    Internal use only.  Check that the required parameters are present.
    If they aren't, aborts with a 400 and an error message
    Arguments:
        route: the route of the call, for an error message
        required_parameters: the parameters that are supposed to be present
    '''
    missing = [parameter for parameter in required_parameters if request.args.get(parameter) is None]
    if len(missing) > 0:
        parameter_string = f'parameters {set(missing)} ' if len(missing) > 1 else f'parameter {missing[0]} '
        msg = 'Missing ' + parameter_string + f'for route {route}'
        _log_and_abort(msg, 400)



#------------------------ROUTES-------------------------------------------------

# A global route to return all of the routes
@sdtp_server_blueprint.route('/')
@sdtp_server_blueprint.route('/routes')
def routes():
    return jsonify(sdtp_server_blueprint.ROUTES)

# Table routes

@sdtp_server_blueprint.route('/get_table_names')
def get_table_names():
    '''
    Target for the /get_table_names route.  Returns the list of names of tables hosted by this server, as a simple list of strings.
    Parameters: none
    Errors: none
    '''
    return jsonify(list(sdtp_server_blueprint.table_server.servers.keys()))

@sdtp_server_blueprint.route('/get_tables')
def get_tables():
    '''
    Target for the /get_tables route.  Dumps a JSONIfied dictionary of the form:
    {table_name: <table_schema>}, where <table_schema> is a dictionary
    {"name": name, "type": type}

    '''
    items = sdtp_server_blueprint.table_server.servers.items()
    result = {}
    for (name, table) in items:
        result[name] = table.schema

    return jsonify(result)

@sdtp_server_blueprint.route('/get_table_schema')
def get_table_schema():
    '''
    Target for the /get_table_schema.  Returns the schema of the table as a list
    of objects.  Each object will contain the fields "name" and "type", where "type"
    is an SDML type.
    Returns 400 if the table is not found.
    Arguments:
            table_name: the name of the table
    '''
    _check_required_parameters('/get_table_schema', ['table_name'])
    table_name = request.args.get('table_name')
    assert table_name is not None # shuts PyLance up -- this is guaranteed, otherwise _check_required_parameters would have aborted
    table = _table_server('/get_table_schema', table_name)
    return jsonify(table.schema)

def _execute_column_operation(route):
    # A utility for all of the column routes: they are all identical except for the TableServer method name, which 
    # even takes the same arguments
    _check_required_parameters(route, ['table_name', 'column_name'])
    column_name = request.args.get('column_name')
    table_name = request.args.get('table_name')
    methods = {
        '/get_range_spec': sdtp_server_blueprint.table_server.get_range_spec,
        '/get_all_values': sdtp_server_blueprint.table_server.get_all_values,
        '/get_column': sdtp_server_blueprint.table_server.get_column
    }
    method = methods[route]
    
    try:
        result = method(table_name, column_name)
        return Response(
            dumps(result, default= json_serialize),
            mimetype = "application/json"
        )
    except TableNotFoundException:
        _log_and_abort(f'No  table {table_name} present, request {route}', 404)
    except ColumnNotFoundException:
        _log_and_abort(f'No column {column_name} in table {table_name}, request {route}', 404)

@sdtp_server_blueprint.route('/get_range_spec')
def get_range_spec():
    '''
    Target for the /get_range_spec route.  Makes sure that column_name and table_name are  specified in the call, then returns the
    range  spec [min_val, max_val] as a list. Aborts with a 400
    for missing arguments, missing table, bad column name or if there is no column_name in the arguments, and a 403 if the table is not authorized.

    Arrguments:
            None
    '''
    return _execute_column_operation('/get_range_spec')
    


@sdtp_server_blueprint.route('/get_all_values')
def get_all_values():
    '''
    Target for the /get_all_values route.  Makes sure that column_name and table_name are  specified in the call, then returns the
    sorted list of all distinct values in the column.    Aborts with a 400
    for missing arguments, missing table, bad column name or if there is no column_name in the arguments, and a 403 if the table is not authorized.

    '''
    return _execute_column_operation('/get_all_values')
    

@sdtp_server_blueprint.route('/get_column')
def get_column():
    '''
    Target for the /get_column route.  Makes sure that column_name and table_name are  specified in the call, then returns the
    sorted list of all distinct values in the column.    Aborts with a 400
    for missing arguments, missing table, bad column name or if there is no column_name in the arguments, and a 403 if the table is not authorized.

    '''
    return _execute_column_operation('/get_column')
 

# A route solely intended for debugging/diagnostics -- just echo back the 
# POST form data

@sdtp_server_blueprint.route('/_echo_json_post', methods = ['POST'])
def _echo_json_post():
    json_data = _get_json_body_from_post_request_data(request)
    return jsonify(json_data)


# Sole row route: get_filtered_rows

@sdtp_server_blueprint.route('/get_filtered_rows', methods=['POST'])
def get_filtered_rows() -> Response:
    '''
    Get the filtered rows from a request.   Gets the filter_spec from the filter  field in the body, the table name from the table field
    in the body.  If there is a columns field in the body, returns
    onlyt the named columns.  If there is no filter_spec, returns all rows using server.get_rows().
    Aborts with a 400 if there is no table, or if check_valid_spec or get_filtered_rows throws an InvalidDataException, or if the filter_spec is not valid JSON.

    Returns:
        The filtered rows as a JSONified list of lists
    '''
    try:
        # print(request.data)
        json_data = _get_json_body_from_post_request_data(request)
        filter_spec = _get_post_argument('filter', request.form, json_data)
        columns = _get_post_argument('columns', request.form, json_data)
        table_name = _get_post_argument('table', request.form, json_data)
        format = _get_post_argument('result_format', request.form, json_data)
        if table_name is None:
            _log_and_abort('table is a required parameter to get filtererd rows', 400)
        if format is None:
            format = DEFAULT_FILTERED_ROW_RESULT_FORMAT

    except JSONDecodeError as error:
        _log_and_abort(f'Bad arguments to /get_filtered_rows.  Error {error.msg}')
    table = _table_server('/get_filtered_rows', table_name)
    if columns is None: columns = []
    if not isinstance(columns, list):
        _log_and_abort(f'Columns to /get_filtered_rows must be a list of strings, not {columns}, 400')
    # Make sure that the columns are all valid columns of this table
    names = table.column_names()
    bad_columns = [column for column in columns if column not in names]
    if (len(bad_columns) > 0):
        _log_and_abort(f'Bad Columns {bad_columns} sent to /get_filtered_rows, table {table_name}', 400)

    # If there is no filter, just return the table's rows.  If
    # there is a filter, make sure it's valid and then return the filtered
    # rows
    if filter_spec is not None:
        try:
            check_valid_spec(filter_spec)
        except InvalidDataException as invalid_error:
            _log_and_abort(invalid_error)

    # Check to make sure the requested format is OK
    if format not in ALLOWED_FILTERED_ROW_RESULT_FORMATS:
        _log_and_abort(f'Bad result_format {format} requested for get_filtered_rows.  Request format must be in {ALLOWED_FILTERED_ROW_RESULT_FORMATS}')

    result = table.get_filtered_rows(filter_spec=filter_spec, columns=columns, format=format)

    if isinstance(result, RowTable):
        # Safe to call .to_dictionary()
        result = result.to_dictionary()
        
    return Response(
            dumps(result, default= json_serialize),
            mimetype = "application/json"
        )
    # types = _column_types(table, columns)
    # jsonifiable_result = jsonifiable_rows(result, types)

    # return jsonify(jsonifiable_result)