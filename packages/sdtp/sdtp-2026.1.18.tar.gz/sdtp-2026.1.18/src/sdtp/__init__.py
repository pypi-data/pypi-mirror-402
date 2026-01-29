"""Top-level package for The Simple Data Transfer Protocol."""

__author__ = """Rick McGeer"""
__email__ = 'rick@mcgeer.com'
from importlib.metadata import version
__version__ = version("sdtp")


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

from .sdtp_schema import (
    SDML_STRING,
    SDML_NUMBER,
    SDML_BOOLEAN,
    SDML_DATE,
    SDML_DATETIME,
    SDML_TIME_OF_DAY,
    SDMLType,
    SDML_SCHEMA_TYPES,
    SDML_PYTHON_TYPES,
    type_check,
    make_table_schema,
    is_valid_sdml_type,
    validate_column_spec,
    validate_table_schema,
    ColumnSpec,
    BaseTableSchema,
    RowTableSchema,
    RemoteAuthSpec,
    RemoteTableSchema,
    TableSchema
)


from .sdtp_table import (
    SDMLTable,
    SDMLFixedTable,
    SDMLDataFrameTable,
    RowTable,
    RemoteSDMLTable
)

from .sdtp_table_factory import (
    SDMLTableFactory,
    RowTableFactory,
    RemoteSDMLTableFactory,
    TableBuilder
)

from .sdtp_utils import (
    InvalidDataException,
    json_serialize,
    check_sdml_type_of_list,
    jsonifiable_value,
    jsonifiable_row,
    jsonifiable_rows,
    jsonifiable_column,
    SDMLTypeConverter,
    convert_list_to_type,
    convert_row_to_type_list,
    convert_rows_to_type_list,
    convert_dict_to_type,
    EnvAuthMethod,
    PathAuthMethod,
    ValueAuthMethod,
    AuthMethod,
    resolve_auth_method
)

from .sdtp_client import (
    SDTPClient,
    SDTPClientError,
    load_config
    )

from .sdtp_filter import (
    SDQL_FILTER_OPERATORS,
    SDQL_FILTER_FIELDS,
    check_valid_spec,
    check_valid_spec_return_boolean,
    SDQLFilter,
    InListFilter,    
    GEFilter,    
    GTFilter,    
    LEFilter,    
    LTFilter,    
    RegexFilter,    
    AllFilter,    
    AnyFilter,    
    NoneFilter,
    make_filter,
    IN_LIST,
    EQ,
    GE,
    GT,
    LE,
    LT,
    REGEX,
    ANY,
    ALL,
    NONE,
    NEQ,
)
# from .sdtp_table import SDMLTable, SDMLFixedTable, SDMLDataFrameTable, RowTable, RemoteSDMLTable, SDMLTableFactory, RowTableFactory, RemoteSDMLTableFactory, FileTable, FileTableFactory, GCSTable, GCSTableFactory, HTTPTable, HTTPTableFactory
from .table_server import (
    TableServer,
    TableNotFoundException,
    ColumnNotFoundException,
    TableLoader,
    FileTableLoader,
    HTTPTableLoader,
    HeaderInfo
)
from .sdtp_server import (
    sdtp_server_blueprint,
    SDTPServer
)

# Public API surface for the sdtp package


__all__ = [
    # sdtp_schema.py
    'SDML_STRING',
    'SDML_NUMBER',
    'SDML_BOOLEAN',
    'SDML_DATE',
    'SDML_DATETIME',
    'SDML_TIME_OF_DAY',
    'SDMLType',
    'SDML_SCHEMA_TYPES',
    'SDML_PYTHON_TYPES',
    'type_check',
    'make_table_schema',
    'is_valid_sdml_type',
    'validate_column_spec',
    'validate_table_schema',
    'ColumnSpec',
    'BaseTableSchema',
    'RowTableSchema',
    'RemoteAuthSpec',
    'RemoteTableSchema',
    'TableSchema',
    # sdtp_table.py
    'SDMLTable',
    'SDMLFixedTable',
    'SDMLDataFrameTable',
    'RowTable',
    'RemoteSDMLTable',
    # sdtp_table_factory.py
    'SDMLTableFactory',
    'RowTableFactory',
    'RemoteSDMLTableFactory',
    'TableBuilder',
    # sdtp_utils.py
    'InvalidDataException',
    'json_serialize',
    'check_sdml_type_of_list',
    'jsonifiable_value',
    'jsonifiable_row',
    'jsonifiable_rows',
    'jsonifiable_column',
    'SDMLTypeConverter',
    'convert_list_to_type',
    'convert_row_to_type_list',
    'convert_rows_to_type_list',
    'convert_dict_to_type',
    'EnvAuthMethod',
    'PathAuthMethod',
    'ValueAuthMethod',
    'AuthMethod',
    'resolve_auth_method',
    # sdtp_client.py
    'SDTPClient',
    'SDTPClientError',
    'load_config',
    # sdtp_filter.py
    'SDQL_FILTER_OPERATORS',
    'SDQL_FILTER_FIELDS',
    'check_valid_spec',
    'check_valid_spec_return_boolean',
    'SDQLFilter',
    'InListFilter',    
    'GEFilter',    
    'GTFilter',    
    'LEFilter',    
    'LTFilter',    
    'RegexFilter',    
    'AllFilter',    
    'AnyFilter',    
    'NoneFilter',
    'make_filter',
    'IN_LIST',
    'EQ',
    'GE',
    'GT',
    'LE',
    'LT',
    'REGEX',
    'ANY',
    'ALL',
    'NONE',
    'NEQ',
    # table_server.py
    'TableServer',
    'TableNotFoundException',
    'ColumnNotFoundException',
    'TableLoader',
    'FileTableLoader',
    'HTTPTableLoader',
    'HeaderInfo',
    # sdtp_server.py
    'sdtp_server_blueprint',
    'SDTPServer'
]
