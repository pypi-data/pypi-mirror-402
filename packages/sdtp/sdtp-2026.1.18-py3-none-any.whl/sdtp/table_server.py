'''
Middleware for a server deployment.  This is designed
to sit between the SDTP objects (in sdtp)
and a server.  These objects provide two principal
functions:
1. Keep the set of tables by name
2. Handle authentication on a table-specific basis
3. Convert results into the wire format for transmission

There are two major classes: 
1. Table, which provides a wrapper around the SDTP Table with the table's
   name, authentication requirememts, and result-conversion utilities
2. TableServer, which provides a registry and lookup service to Tables
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


import os
from json import load
import pandas as pd
import requests

from .sdtp_utils import InvalidDataException
from .sdtp_table_factory import TableBuilder
from .sdtp_table import SDMLTable
from abc import ABC, abstractmethod

class TableNotFoundException(Exception):
    '''
    An exception that is thrown when a table is not found in the TableServer
    '''

    def __init__(self, message):
        super().__init__(message)


class ColumnNotFoundException(Exception):
    '''
    An exception that is thrown when a column is not found for a specific table
    '''

    def __init__(self, message):
        super().__init__(message)

def _check_type(value, python_type, message_prefix):
    # A utility that checks that value is of the correct type, which should be a Python type.
    # Doesn't return: instead, throws an Assertion Failure with a message when the type doesn't check
    assert isinstance(value, python_type), f'{message_prefix} {type(value)}'

def _check_dict_and_keys(dictionary, keys, dict_message, dict_name):
    # A utility that checks that dictionary is a dict, and that the keys keys are all present.  
    # Doesn't return: instead, throws an Assertion Failure with a message when the type doesn't check
    _check_type(dictionary, dict, dict_message)
    missing_keys = keys - dictionary.keys() if keys is not None else {}
    assert len(missing_keys) == 0, f'{dict_name} is missing keys {missing_keys}'


class TableServer:
    '''
    The server for tables.  Its task is to maintain a correspondence
    between table names and the actual tables.  It also maintains the security information for a table (the variables and values required to access the table), and gives column information across tables
    '''

    # Conceptually, there is only a single TableServer  (why would there #  be more?), and so this could be in a global variable and its # methods global.
    def __init__(self):
        self.servers = {}
        self.factories = {}
        self.loaders = {
            "file": FileTableLoader,
            "uri": HTTPTableLoader,
            # Add additional loaders here as needed
        }
        

    def init_from_config(self, config_path):
        """
        Initialize TableServer from config file.
        Config must be a JSON list as specified above.
        """
        with open(config_path, "r") as f:
            config = load(f)

        for entry in config:
            name = entry["name"]
            load_spec = entry["load_spec"]

            location_type = load_spec["location_type"]
            loader_cls = self.loaders.get(location_type)
            if loader_cls is None:
                raise ValueError(f"No loader for location_type '{location_type}'")

            loader = loader_cls(load_spec)
            table_spec = loader.load()  # Should return a dict

            # Figure out the table type (e.g. "row", "remote") from the spec
            table = TableBuilder.build_table(table_spec)
            self.add_sdtp_table(name, table)


    def add_sdtp_table(self, table_name, sdtp_table):
        '''
        Register a SDMLTable to serve data for a specific table name.
        Raises an InvalidDataException if table_name is None or sdtp_table is None or is not an instance of SDMLTable.

        Arguments:
            table_name (str): name of the table
            sdtp_table (SDMLTable): table to add

        '''
        _check_type(sdtp_table, SDMLTable, 'The sdtp_table argument to add_sdtp_table must be a Table, not')
        self.servers[table_name] = sdtp_table

    def add_sdtp_table_from_dictionary(self, name, table_dictionary):
        '''
        Add an  SDMLTable from a dictionary (intermediate on-disk form).   The table dictionary has fields schema and type, and then type-
        specific fields.  Calls TableBuilder to build the table,
        then calls self.add_sdtp_table to add the table.
        Raises an InvalidDataException if self.add_sdtp_table or TableBuilder.buildTable raises it 
        Arguments:
            name (str): the name of the table
            table_dictionary (dict): dictionary of the form {"type", "table"}, where table is a table specification: a dictionary
                             with the fields type and schema

        '''

       
        table = TableBuilder.build_table(table_dictionary)
        self.add_sdtp_table(name,  table)
    


    def get_all_tables(self) -> list:
        '''
        Get all the tables.  This
        is to support a request for a numeric_spec or all_values for a column name when the
        table_name is not specified. In this case, all tables will be searched for this column name.
        

        Returns:
            list: a list of all tables
        '''
        tables = self.servers.values()
        return list(tables)

    
    def get_table(self, table_name) -> SDMLTable:
        '''
        Get the table with name table_name, first checking to see
        if  table access is authorized by the passed headers.
        Arguments:
            table_name: name of the table to search for
            
        Returns:
            SDMLTable: The SDML table corresponding to the request
        Raises:
            TableNotFoundException if the table is not found
            
        '''
        try:
            return self.servers[table_name]
           
        except KeyError:
            raise TableNotFoundException(f'Table {table_name} not found')

   
    def get_all_values(self, table_name, column_name) -> list:
        '''
        Get all of the distinct values for column column_name for table
        table_name.  Returns the list of distinct values for the columns
        Arguments:
            table_name (str): table to be searched
            column_name (str): name of the column
           
        Returns:
            list: Returns the list of distinct values for the columns
        Raises:
            TableNotFoundException if the table is not found
            ColumnNotFoundException if the column can't be found
        '''

        _check_type(column_name, str, 'Column name must be a string, not')
        table = self.get_table(table_name)  # Note this will throw the TableNotFoundException

        try:
            return table.all_values(column_name)
        except InvalidDataException:
            raise ColumnNotFoundException(f'Column {column_name} not found in table {table_name}')

    def get_range_spec(self, table_name, column_name) -> list:
        '''
        Get the range specification for column column_name for table
        table_name.  Returns  a two-length list [min_val, max_val]
        Arguments:
            table_name: table to be searched
            column_name: name of the column
            
        Returns:
            list: Returns  a dictionary with keys{max_val, min_val}
        Raises:
            TableNotFoundException if the table is not found
            ColumnNotFoundException if the column can't be found
        '''
        _check_type(column_name, str, 'Column name must be a string, not')
        table = self.get_table(table_name)  # Note this will throw the TableNotFoundException
        try:
            return table.range_spec(column_name)
        except InvalidDataException:
            raise ColumnNotFoundException(f'Column {column_name} not found in table {table_name}')
        
    def get_column(self, table_name, column_name) -> list:
        '''
        Get the column for column column_name for table
        table_name.  Returns the column as a list
        Arguments:
            table_name: table to be searched
            column_name: name of the column
           
        Returns:
            list: Returns  a dictionary with keys{max_val, min_val}
        Raises:
            TableNotFoundException if the table is not found
            ColumnNotFoundException if the column can't be found
        '''
        _check_type(column_name, str, 'Column name must be a string, not')
        table = self.get_table(table_name)  # Note this will throw the TableNotFoundException
        try:
            return table.get_column(column_name)
        except InvalidDataException:
            raise ColumnNotFoundException(f'Column {column_name} not found in table {table_name}')

class TableLoader(ABC):
    @abstractmethod
    def load(self):
        """Returns a dict spec for the table"""

class FileTableLoader(TableLoader):
    """
    Loads a table from a path
    """
    def __init__(self, spec):
        self.path = spec["path"]

    def load(self):
        with open(self.path, "r") as f:
            return load(f)


class HTTPTableLoader(TableLoader):
    def __init__(self, spec):
        self.url = spec["url"]
        self.auth = HeaderInfo(spec["auth_info"]) if "auth_info" in spec else None

    def load(self):
        headers = self.auth.headers() if self.auth else {}
        response = requests.get(self.url, headers=headers)
        response.raise_for_status()
        return response.json()
    
class HeaderInfo:
    """
    Supports loading headers from file or env according to our spec:
    - {"from_file": "path/to/headers.json"}
    - {"headers": {"Authorization": {"from_env": "API_AUTH"}}}
    """
    def __init__(self, spec, error_on_missing_env=True):
        self.headers_dict = {}

        if spec is None:
            return

        # Case 1: Load headers from a JSON file
        if "from_file" in spec:
            if not os.path.exists(spec["from_file"]):
                raise FileNotFoundError(f"Header file not found: {spec['from_file']}")
            with open(spec["from_file"], "r") as f:
                data = load(f)
                if not isinstance(data, dict):
                    raise ValueError(f"Headers file must be a JSON object (dict), got {type(data)}")
                # No inline validation: assume secret file is trusted
                self.headers_dict = data

        # Case 2: Load each header from an env var
        elif "headers" in spec:
            headers_spec = spec["headers"]
            if not isinstance(headers_spec, dict):
                raise ValueError(f"'headers' must be a dict, got {type(headers_spec)}")
            for k, v in headers_spec.items():
                if isinstance(v, dict) and "from_env" in v:
                    env_key = v["from_env"]
                    env_val = os.environ.get(env_key)
                    if env_val is None:
                        msg = f"Environment variable '{env_key}' for header '{k}' is not set."
                        if error_on_missing_env:
                            raise EnvironmentError(msg)
                        else:
                            print(f"Warning: {msg} (header omitted)")
                            continue
                    self.headers_dict[k] = env_val
                else:
                    raise ValueError(f"Header '{k}' value must be a dict with 'from_env', got {v}")
        else:
            raise ValueError("auth_info must contain 'from_file' or 'headers' as its only key.")

        # Strict: Disallow extra keys
        allowed_keys = {"from_file", "headers"}
        extra_keys = set(spec.keys()) - allowed_keys
        if extra_keys:
            raise ValueError(f"auth_info has unsupported keys: {extra_keys}")

    def headers(self):
        # Only return headers with non-None values
        return {k: v for k, v in self.headers_dict.items() if v is not None}