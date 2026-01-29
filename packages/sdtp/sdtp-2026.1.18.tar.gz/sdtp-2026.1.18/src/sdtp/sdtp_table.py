'''
A SDMLTable class and associated utilities.  The SDMLTable class is initialized
with the table's schema,  single function,get_rows(), which returns the rows of the table.  To
use a  SDMLTable instance, instantiate it with the schema and a get_rows() function.
The SDMLTable instance can then be passed to a SDTPServer with a call to
galyleo_server_framework.add_table_server, and the server will then be able to serve
the tables automatically using the instantiated SDMLTable.
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


import pandas as pd

import requests
import json
from typing import List, Dict, Any, Union, Callable
import os

from .sdtp_schema import SDML_SCHEMA_TYPES, ColumnSpec, RowTableSchema, RemoteTableSchema, _make_table_schema 
from typing import List
from .sdtp_utils import InvalidDataException
from .sdtp_utils import jsonifiable_column, jsonifiable_rows,  type_check, json_serialize
from .sdtp_utils import SDMLTypeConverter, convert_list_to_type, convert_rows_to_type_list
from .sdtp_filter import SDQLFilter, make_filter


def _row_dict(row, columns):
    result = {}
    for i in range(len(columns)):
        result[columns[i]] = row[i]
    return result

def _convert_filter_result_to_format(rows, columns, schema, format):
    result_rows = rows
    column_names = [entry['name'] for entry in schema]
    column_indices = [column_names.index(column) for column in columns]
    result_rows = [[row[index] for index in column_indices] for row in rows]
            
    if format == 'list':
        return result_rows
        
    if format == 'dict':
        return [_row_dict(row, columns) for row in result_rows]
    # format is SDML, return a RowTable
    row_table_schema = [schema[i] for i in column_indices]
    return RowTable(row_table_schema, result_rows)


ALLOWED_FILTERED_ROW_RESULT_FORMATS = {'dict', 'list', 'sdml'}
DEFAULT_FILTERED_ROW_RESULT_FORMAT = 'list'

        
def _select_entries_from_row(row, indices):
    # Pick the entries of row trhat are in indices, maintaining the order of the
    # indices.  This is to support the column-choice operation in SDMLTable.get_filtered_rows
    # Arguments:
    #     row: the tow of vaslues
    #     indices: the indices to pick
    # Returns:
    #     The subset of the row corresponding to the indices
    return [row[i] for i in range(len(row)) if i in indices]



DEFAULT_HEADER_VARIABLES = {"required": [], "optional": []}
'''
The Default for header variables for a table is both required and optional lists are empty.
'''

def get_errors(entry):
    '''
    A Utility to make sure that a schema entry is valid.  It must have a name, a type, both must be strings, 
    and the type is one of SDML_SCHEMA_TYPES.
    Arguments:
        entry: a dictionary with (at least) the keys name, type
    Returns:
        A list of errors, which will be the empty list if no errors are found.
    '''
    if not type(entry) == dict:
        return [f'Schema entry {entry} must be a dictionary, not {type(entry)}']
    result = []
    keys = set(entry.keys())
    if not 'name' in keys:
        result.append(f'Column {entry} must have a name')
    elif type(entry['name']) != str:
        result.append(f'Name of column {entry} must be a string')
    if not 'type' in keys:
        result.append(f'Column {entry} must have a type')
    elif not (type(entry['type']) == str and entry['type'] in SDML_SCHEMA_TYPES):
        result.append(f'Type of column {entry} must be one of {SDML_SCHEMA_TYPES}' )
    return result
            
    

class SDMLTable:
    '''
    An SDMLTable.  This is the abstract superclass for all Simple Data Markup Language tables, and 
    implements the schema methods of every SDML class.  The data methods are implemented
    by the concrete classes.  Any new SDMLTable class should:
    1. Subclass SDMLTable
    2. Have a constructor with the argument schema
    3. call super(<classname, self).__init__(schema) in the constructor
    4. Implement the methods:
        (a) all_values(self, column_name)
        (b) range_spec(self, column_nam)
        (c) _get_filtered_rows_from_filter(self, filter, columns = None)
        (d) to_json(self)
    where:
        i. column_name is the name of the column to get the values/range_spec from
        ii. filter is a an instance of SDQLFilter
        iii. if columns is not None for get_filtered_rows, only return entries from those columns
            in the result from get_filtered_rows
    Arguments:
        schema: a list of records of the form {"name": <column_name, "type": <column_type>}.
           The column_type must be a type from galyleo_constants.SDTP_TYPES.
    '''
    def __init__(self, schema):
        if type(schema) != list:
            raise InvalidDataException(f'The schema must be a list of dictionaries, not {type(schema)}')
        error_entries = [get_errors(entry) for entry in schema]
        error_entries = [entry for entry in error_entries if len(entry) > 0]
        if len(error_entries) > 0:
            raise InvalidDataException(f"Errors in schema {schema}: {error_entries}")
           
        self.schema = schema
        # self.is_sdtp_table = True

    def column_names(self):
        '''
        Return the names of the columns
        '''
        return [column["name"] for column in self.schema]

    def column_types(self):
        '''
        Return the types of the columns
        '''
        return [column["type"] for column in self.schema]

    def get_column_type(self, column_name):
        '''
        Returns the type of column column_name, or None if this table doesn't have a column with
        name  column_name.

        Arguments:
            column_name(str): name of the column to get the type for
        '''
        matches = [column["type"] for column in self.schema if column["name"] == column_name]
        if len(matches) == 0:
            return None
        else:
            return matches[0]
    
    def all_values(self, column_name: str)  -> list:
        '''
        get all the values from column_name
        Arguments:
            column_name: name of the column to get the values for
           
        Returns:
            list: List of the values

        '''
        raise InvalidDataException(f'all_values has not been in {type(self)}.__name__')
    
    def get_column(self, column_name: str)  -> list:
        '''
        get the column  column_name
        Arguments:
            column_name: name of the column to get 
             

        Returns:
            list: List of the values in the column

        '''
        raise InvalidDataException(f'get_column has not been in {type(self)}.__name__')
    

    def range_spec(self, column_name: str) -> list:
        '''
        Get the list [min_val, max_val] for column_name
        Arguments:

            column_name: name of the column to get the range spec for

        Returns:
            list: the minimum and  maximum of the column

        '''
        raise InvalidDataException(f'range_spec has not been in {type(self)}.__name__')
    
    def _get_filtered_rows_from_filter(self, filter=None):
        '''
        Returns the rows for which the  filter returns True.  Returns a list of the matching rows 

        Arguments:
            filter: A SDQLFilter 
        Returns:
            The subset of self.get_rows() which pass the filter 
        '''
        raise InvalidDataException(f'_get_filtered_rows_from_filter has not been in {type(self)}.__name__')


    def get_filtered_rows(self, filter_spec=None, columns=None, format = DEFAULT_FILTERED_ROW_RESULT_FORMAT):
        '''
        Filter the rows according to the specification given by filter_spec.
        Returns the rows for which the resulting filter returns True.

        Arguments:
            filter_spec(dict): Specification of the filter, as a dictionary
            columns(list): the names of the columns to return.  Returns all columns if absent
            format(str): one of 'list', 'dict', 'sdml'.  Default is list.  
        Returns:
            list: The subset of self.get_rows() which pass the filter in the format specified by format
        '''
        # Check to make sure that the format is valid
        if format is None: format = DEFAULT_FILTERED_ROW_RESULT_FORMAT
        
        if format not in ALLOWED_FILTERED_ROW_RESULT_FORMATS:
            raise InvalidDataException(f'format for get_filtered rows must be one of {ALLOWED_FILTERED_ROW_RESULT_FORMATS}, not {format}')
        requested_columns = columns  if columns else []
        # Note that we don't check if the column names are all valid
        filter = make_filter(filter_spec) if filter_spec is not None else None
        rows =  self._get_filtered_rows_from_filter(filter = filter)
        columns_in_result = self.column_names() if len(requested_columns) == 0 else requested_columns
        return _convert_filter_result_to_format(rows, columns_in_result, self.schema, format)
        

    
    def to_dictionary(self):
        '''
        Return the dictionary  of this table, for saving on disk or transmission.
        '''
        raise InvalidDataException(f'to_dictionary has not been in {type(self)}.__name__')
    
    def to_json(self):
        '''
        Return the JSON form of this table, for saving on disk or transmission.
        '''
        # Since the columns are already a dictionary, they are simply directly jsonified.  For the rows,
        # just use jjson.dumps, making sure to convert types appropriately

        return json.dumps(self.to_dictionary(), default = json_serialize, indent = 2)
    




class SDMLFixedTable(SDMLTable):
    '''
    A SDMLFixedTable: This is a convenience class for subclasses which generate a fixed 
    number of rows locally, independent of filtering. This is instantiated with a function get_rows() which  delivers the
    rows, rather than having them explicitly in the Table.  Note that get_rows() *must* return 
    a list of rows, each of which has the appropriate number of entries of the appropriate types.
    all_values, range_spec, and _get_filtered_rows_from_filter are all implemented on top of 
    get_rows.  Note that these methods can be overridden in a subclass if there is a
    more efficient method than the obvious implementation, which is what's implemented here.

    Arguments:
        schema(List): a list of records of the form {"name": <column_name, "type": <column_type>}.
            The column_type must be a type from galyleo_constants.SDTP_TYPES.
        get_rows (Callable): a function which returns a list of list of values.  Each component list
            must have the same length as schema, and the jth element must be of the
            type specified in the jth element of schema
    '''

    def __init__(self, schema: list, get_rows: Callable[[], List]):
        super(SDMLFixedTable, self).__init__(schema)
        self.get_rows = get_rows

    # This is used to get the names of a column from the schema

    def _get_column_values_and_type(self, column_name: str):
        # get all the column  column_name
        # Arguments:
        #     column_name (str): name of the column to get
        
        # Returns:
        #     The column as a list
 
        try:
            index = self.column_names().index(column_name)
        except ValueError as original_error:
            raise InvalidDataException(f'{column_name} is not a column of this table') from original_error
        sdtp_type = self.schema[index]["type"]
        rows = self.get_rows()
        return([row[index] for row in rows], sdtp_type)


    
    def all_values(self, column_name: str) -> list:
        '''
        get all the values from column_name
        Arguments:
            column_name: name of the column to get the values for
            

        Returns:
            list: List of the values

        '''
        (values, sdtp_type) = self._get_column_values_and_type(column_name)
        result = list(set(values))
        result.sort()
        return result
    
    def get_column(self, column_name: str)  -> list:
        '''
        get all the column  column_name
        Arguments:
            column_name: name of the column to get
            

        Returns:
            list: The column as a list

        '''
        (result, sdtp_type) = self._get_column_values_and_type(column_name)
        return  result
    
    def check_column_type(self, column_name):
        '''
        For testing.  Makes sure that all the entries in column_name are the right type
        No return, but throws an InvalidDataException if there's a bad element in the column
        '''
        value_list = self.all_values(column_name)
        required_type = self.get_column_type(column_name)
        if required_type is not None:
            bad_values = [val for val in value_list if not type_check(required_type, val)]
        else:
            bad_values = []
        if len(bad_values) > 0:
            raise InvalidDataException(f'Values {bad_values} could not be converted to {required_type} in column {column_name}')
        

    def range_spec(self, column_name: str) -> list:
        '''
        Get the dictionary {min_val, max_val} for column_name
        Arguments:
            column_name: name of the column to get the range spec for

        Returns:
            list: the minimum and  maximum of the column

        '''
        (values, sdtp_type) = self._get_column_values_and_type(column_name)
        values.sort()
        result = [values[0], values[-1]]
        return result
    
    def _get_filtered_rows_from_filter(self, filter=None):
        '''
        Returns the rows for which the  filter returns True.  

        Arguments:
            filter: A SDQLFilter 
    
           
        Returns:
            The subset of self.get_rows() which pass the filter
        '''
        
        if filter is None:
            return  self.get_rows()
        else:
            match_columns = self.column_names()
            return  [row for row in self.get_rows() if filter.matches(row, match_columns)]
        


    def to_dataframe(self):
        '''
        Convert the table to a PANDAS DataFrame.  This is very straightforward; just 
        use get_rows to get the rows and convert the schema to the appropriate dtypes.
        Note this relies on PANDAS type inference.
        '''
        
        return  pd.DataFrame(self.get_rows(), columns = self.column_names())
    
    def to_dictionary(self):
        '''
        Return the intermediate form of this table as a dictioary
        '''
        return {
            "type": "RowTable",
            "schema": self.schema,
            "rows": jsonifiable_rows(self.get_rows(), self.column_types())
        }
    
class SDMLDataFrameTable(SDMLFixedTable):
    '''
    A simple utility class to serve data from a PANDAS DataFrame.  The general idea is 
    that the values are in the PANDAS Dataframe, which must have the same column names
    as the schema and compatible types.
    '''
    def __init__(self, schema, dataframe,  type_converter=None, converter_kwargs=None):
        super(SDMLDataFrameTable, self).__init__(schema, self._get_rows)
        self.dataframe = dataframe.copy()
        # Make sure the column names and types match
        self.dataframe.columns = self.column_names()
         # make sure that the types match
        if type_converter is not None:
            tc = type_converter
        else:
            tc = SDMLTypeConverter(**(converter_kwargs or {}))
        for column in schema:
            column_values = self.dataframe[column["name"]].tolist()
            try:
               
                fixed_series = convert_list_to_type(column["type"], column_values, tc)
                self.dataframe[column["name"]] = fixed_series
            except Exception as exc:
                raise InvalidDataException(f'error {exc} converting {column["name"]}')
            
    def _get_column_and_type(self, column_name):
        try:
            index = self.column_names().index(column_name)
        except ValueError as original_error:
            raise InvalidDataException(f'{column_name} is not a column of this table') from original_error
        return  {
            "type": self.schema[index]["type"],
            "values": self.dataframe[column_name].to_list()
        }
    
    def all_values(self, column_name: str)  -> list:
        '''
        get all the values from column_name
        Arguments:
            column_name: name of the column to get the values for
           

        Returns:
            list: List of the values

        '''
        type_and_values = self._get_column_and_type(column_name)
        result = list(set(type_and_values['values']))
        result.sort()
        return  result
    
    def get_column(self, column_name: str)  -> list:
        '''
        get the column  column_name
        Arguments:
            column_name: name of the column to get 
            

        Returns:
            list: List of the values in the column

        '''
        type_and_values = self._get_column_and_type(column_name)
        return type_and_values['values']
    

    def range_spec(self, column_name: str)  -> list:
        '''
        Get the dictionary {min_val, max_val} for column_name
        Arguments:

            column_name: name of the column to get the range spec for

        Returns:
            list: the minimum and  maximum of the column

        '''
        type_and_values = self._get_column_and_type(column_name)
        result = list(set(type_and_values['values'])) 
        if len(result) == 0:
            return []
        result.sort()
        response = [result[0], result[-1]]
        return response
         
    def _get_rows(self):
        '''
        Very simple: just return the rows
        '''
        return self.dataframe.values.tolist()

    def to_dataframe(self):
        return self.dataframe.copy()


class RowTable(SDMLFixedTable):
    '''
    A simple utility class to serve data from a static list of rows, which
    can be constructed from a CSV file, Excel File, etc.  The idea is to
    make it easy for users to create and upload simple datasets to be
    served from a general-purpose server.  Note that this will need some
    authentication.
    '''

    def __init__(self, schema, rows, type_converter=None, converter_kwargs=None):
        """
        Construct a RowTable with type-aware conversion.

        Args:
            schema: SDML schema object/list
            rows: list of row data
            type_converter: (optional) an SDMLTypeConverter instance (if None, one will be constructed)
            converter_kwargs: (optional) dict of args to SDMLTypeConverter (if no type_converter provided)
        """
        self.schema = schema  # set this *before* calling self.column_types()
        type_list = self.column_types()
        # print("RowTable.__init__ received schema:", schema)
        # print("RowTable.__init__ received rows:", rows)
        # print("RowTable.__init__ inferred column types:", self.column_types(), type_list)
        if type_converter is not None:
            tc = type_converter
        else:
            tc = SDMLTypeConverter(**(converter_kwargs or {}))
        self.rows = convert_rows_to_type_list(type_list, rows, tc)
        super(RowTable, self).__init__(schema, self._get_rows)
    
    def _get_rows(self):
        return [row for row in self.rows]
    
               
def _column_names(schema):
    return [entry["name"] for entry in schema]

def _generate_ordered_lists(remoteRowTable, localRemoteTable, requestedColumns):
    # The results of a remote table get_filtered_rows query
    # can return columns in a different order from the request; this
    # happens when the columns on the remote table are in a different
    # order than the columns on the local table.  There is no problem
    # when the user requested sdml or dict as a return, because these
    # are self-documenting.    When the user requested list, we need
    # to reorder the values to match the expected order.
    def reorder_row(row, source_index_list, target_index_list):
        result = row.copy()
        for i in range(len(row)):
            result[target_index_list[i]] = row[source_index_list[i]]
        return result
    def get_index_list(table):
        table_columns = table.column_names()
        return [table_columns.index(column) for column in requestedColumns]
    source_index_list = get_index_list(remoteRowTable)
    target_index_list = get_index_list(localRemoteTable)
    return [reorder_row(row, source_index_list, target_index_list) for row in remoteRowTable.rows]

def _make_headers(auth_info, header_dict):
    '''
    A Utility which makes the headers for requests from the
    given auth info and header_dict.  Returns None if there are no
    headers.  Elements of header_dict are passed directly to the
    output.  auth_info is None, or one of {'env', 'env_var'};
    {'file', 'path' }, {'token', 'value'}. The latter is not
    reccommended.   It resolves the authorization into a bearer 
    toekn, and if successful attaches 'Authorization': f'Bearer {token}'
    to the result headers.
    Arguments:
        auth_info: authorization info
        header_dict: a dictionary of headers
    Returns:
        The augmented header dictionary, or None if both arguments are None
    Raises:
        ValueError if there's an error in getting the auth token
    '''
    has_auth = auth_info is not None and auth_info.get("type")
    if not has_auth:
        return header_dict.copy() if header_dict is not None else None
    auth_type = auth_info["type"]
    auth_token = None
    headers = {}

    match auth_type:
        case 'env':
            env_var = auth_info["env_var"]
            auth_token = os.environ.get(env_var)
            if not auth_token:
                raise ValueError(f"Environment variable {env_var} not set")
        case "file":
            path = auth_info["path"]
            if not os.path.isfile(path):
                raise ValueError(f"Auth file {path} not found")
            with open(path, "r") as f:
                auth_token = f.read().strip()
        case "token":
            auth_token = auth_info["value"]
        case _:
            raise ValueError(f"Unsupported auth type: {auth_type}")

    if auth_token is not None:
        headers = {"Authorization": f"Bearer {auth_token}"}
    if header_dict is not None:
        for (key, value) in header_dict.items():
            headers[key] = value
    return None if headers == {} else headers
    
        
class RemoteSDMLTable(SDMLTable):
    '''
    A SDTP Table on a remote server.  This just has a schema, an URL, and 
    header variables. This is the primary class for the client side of the SDTP,
    and in many packages would be a separate client module.  However, the SDTP is 
    designed so that Remote Tables can be used to serve local tables, so this 
    is part of a server-side framework to.
    Parameters:
        table_name: name of the resmote stable
        schema: schema of the remote table
        url: url of the server hosting the remore table
        auth: dictionary of variables and values required to access the table
    Throws:
        InvalidDataException if the table doesn't exist on the server, the 
        url is unreachable, the schema doesn't match the downloaded schema

    ''' 
    def __init__(self, table_name, schema, url,  auth = None, header_dict  = None): 
        super(RemoteSDMLTable, self).__init__(schema)
        self.url = url
        self.schema: List[ColumnSpec] = schema
        self.table_name = table_name
        self.auth = auth
        self.ok = False
        self.header_dict = header_dict
        self.headers = _make_headers(auth, header_dict)

    def to_dictionary(self):
        result =  {
            "table_name": self.table_name,
            "type": "RemoteSDMLTable",
            "schema": self.schema,
            "url": self.url,
        }
        if self.auth is not None:
            result["auth"] = self.auth
        if self.header_dict is not None:
            result["header_dict"]  = self.header_dict
        
        return result

    def _connect_error(self, msg):
        self.ok = False
        raise InvalidDataException(f'Error: {msg}')

    def _check_entry_match(self, schema, index, field, mismatches):
        if self.schema[index][field] == schema[index][field]: return
        mismatches.append(f'Mismatch in field {field} at entry {index}. Server value: {schema[index][field]}, declared value: {self.schema[index][field]}')

    def _check_schema_match(self, schema):
        if len(schema) != len(self.schema):
            self._connect_error(f'Server schema {_column_names(schema)} has {len(schema)} columns, declared schema {_column_names(self.schema)} has {len(self.schema)} columns')
        mismatches = []
        for i in range(len(schema)):
            self._check_entry_match(schema, i, "name", mismatches)
            self._check_entry_match(schema, i, "type", mismatches)
        
        if len(mismatches) > 0:
            mismatch_report = 'Schema mismatch: ' + ', '.join(mismatches)
            self._connect_error(mismatch_report)


    def _execute_get_request(self, url):
        if self.header_dict:
            return requests.get(url, headers = self.headers)
        else:
            return requests.get(url)
        
    def connect_with_server(self):
        '''
        Connect with the server, ensuring that the server is:
        a. a SDTP server
        b. has self.table_name in its list of tables
        c. the table there has a matching schema
        '''
        
        try:
            response = self._execute_get_request(f'{self.url}/get_tables')
            if response.status_code >= 300:
                self._connect_error(f'Bad connection with {self.url}: code {response.status_code}')
        except Exception as e:
            self._connect_error(f'Error connecting with {self.url}/get_tables: {repr(e)}')
        try:
            server_tables = response.json()
        except Exception as e:
            self._connect_error(f'Error {repr(e)} reading tables from  {self.url}/get_tables')
        if self.table_name in server_tables:
            server_schema: List[ColumnSpec] = server_tables[self.table_name]
            self._check_schema_match(server_schema)
            self.server_schema = server_schema
        else:
            self._connect_error(f'Server at {self.url} does not have table {self.table_name}')
        # if we get here, everything worked:
        self.ok = True
        
        # also check to make sure that we can authenticate to the table.  See /get_table_spec
    
    def _check_column_and_get_type(self, column_name):
         if not column_name in self.column_names():
            raise InvalidDataException(f'Column {column_name} is not a column of {self.table_name}')
         return self.get_column_type(column_name)

        
    def _do_request(self,  request):
        # check to see if we have a connection, and then do a GET request using GET,
        # supplying header variables if required. 
        # Note that the wire format is json, so the return from this function is json,
        # and (if required) converted to the right datatype by the calling routing
        if not self.ok:
            self.connect_with_server()
        try:
            response = self._execute_get_request(request)
            if response.status_code >= 300:
                raise InvalidDataException(f'{request} returned error code{response.status_code}')
            return response.json()
        except Exception as exc:
            raise InvalidDataException(f'Exception {repr(exc)} ocurred in {request}')
        
    def _execute_column_route(self, column_name,  route):
        # The code for all_values, get_column, and range_spec are identical except for the route, 
        # so this method does both of them with the route passed in as an extra parameter
        # use _do_request to execute the request
        # 
        column_type = self._check_column_and_get_type(column_name)
        request = f'{self.url}/{route}?table_name={self.table_name}&column_name={column_name}'
        result = self._do_request(request)
        type_converter = SDMLTypeConverter()
        return convert_list_to_type(column_type, result, type_converter)
        
    def all_values(self, column_name: str) -> list:
        '''
        get all the values from column_name
        Arguments:

            column_name: name of the column to get the values for

        Returns:
            list: List of the values

        '''
        return self._execute_column_route(column_name,  'get_all_values')
        
        
    def get_column(self, column_name: str)  -> list:
        '''
        get the column  column_name
        Arguments:
            column_name: name of the column to get
           

        Returns:
            List: The column as a list
        '''
        return self._execute_column_route(column_name, 'get_column')


    def range_spec(self, column_name: str)  -> list:
        '''
        Get the dictionary {min_val, max_val} for column_name
        Arguments:

            column_name: name of the column to get the range spec for

        Returns:
            list: the minimum and  maximum of the column

        '''
        return self._execute_column_route(column_name, 'get_range_spec')
    
    def _get_filtered_rows_from_remote(self, filter_spec = None, columns = []):
        if not self.ok:
            self.connect_with_server()
        request = f'{self.url}/get_filtered_rows'
        data = {
            'table': self.table_name,
            'result_format': 'sdml'
        }
        if filter_spec:
            data['filter'] = filter_spec
        if columns is not None and len(columns) > 0:
            data['columns'] = columns
        
        try:
            response = requests.post(request, json=data, headers=self.headers) if self.headers is not None else requests.post(request, json=data)
            if response.status_code >= 300:
                raise InvalidDataException(f'get_filtered_rows to {self.url}: caused error response {response.status_code}')
            raw_result = response.json()
            from .sdtp_table_factory import TableBuilder
            resultTable = TableBuilder.build_table(raw_result)
            return resultTable
        except Exception as exc:
            raise InvalidDataException(f'Error in get_filtered_rows to {self.url}: {repr(exc)}')
       

        

    def _get_filtered_rows_from_filter(self, filter=None) -> list:
        '''
        Returns the rows for which the  filter returns True.  

        Arguments:
            filter: A SDQLFilter 
            columns: the names of the columns to return.  Returns all columns if absent
            
        Returns:
            List: The subset of self.get_rows() which pass the filter
        '''
        filter_spec = None if filter is None else filter.to_filter_spec()
        return self._get_filtered_rows_from_remote(filter_spec, columns=[]).get_rows()
    
    def get_filtered_rows(self, filter_spec=None, columns=None, format = DEFAULT_FILTERED_ROW_RESULT_FORMAT) -> Union[list, list[dict[str, Any]], RowTable]:
        '''
        Filter the rows according to the specification given by filter_spec.
        Returns the rows for which the resulting filter returns True.
        Reorders columns to match client request, even if remote server responds in different order. This guarantees protocol safety.

        Arguments:
            filter_spec (dict): Specification of the filter, as a dictionary
            columns (list): the names of the columns to return.  Returns all columns if absent
            format (str): one of 'list', 'dict', 'sdml'.  Default is list.  
        Returns:
            The subset of self.get_rows() which pass the filter in the format specified by format
        '''
        # Check to make sure that the format is valid
        if format is None: format = DEFAULT_FILTERED_ROW_RESULT_FORMAT
        requested_columns = columns if columns else []
    
        
        if format not in ALLOWED_FILTERED_ROW_RESULT_FORMATS:
            raise InvalidDataException(f'format for get_filtered rows must be one of {ALLOWED_FILTERED_ROW_RESULT_FORMATS}, not {format}')
        # Note that we don't check if the column names are all valid
       
        remoteRowTable = self._get_filtered_rows_from_remote(filter_spec, columns=requested_columns)
        if format == 'list':
            column_names = self.column_names() if len(requested_columns) == 0 else requested_columns
            return _generate_ordered_lists(remoteRowTable, self, column_names)
        elif format == 'dict':
            result_columns = remoteRowTable.column_names()
            return [_row_dict(row, result_columns) for row in remoteRowTable.rows]
        else:
            return remoteRowTable
        