'''
Constants and utilities for the Simple Data Transfer Protocol
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

import json
import datetime
import functools
import pandas as pd
from sdtp import type_check, SDML_PYTHON_TYPES
import math
from dateutil import parser

NULL_SENTINELS = {'None', 'none', 'nan', 'NaN', 'NaT', 'null', ''}

def json_serialize(obj):
    # Convert dates, times, and datetimes to isostrings 
    # for json serialization
    if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")



def check_sdml_type_of_list(sdml_type, list_of_values):
    '''
    Check to make sure the values in list_of_values are all the right Python 
    type for operations.
    Arguments:
        sdml_type: One of SDML_SCHEMA_TYPES
        list_of_values: a Python list to be tested
    '''
    type_check_list = [type_check(sdml_type, val) for val in list_of_values]
    return not (False in type_check_list)
    

'''
Exceptions for the Simple Data Transfer Protocol
'''



class InvalidDataException(Exception):
    '''
    An exception thrown when a data table (list of rows) doesn't match an accoompanying schema,
     or a bad schema is specified, or a table row is the wrong length, or..
    '''

    def __init__(self, message):
        super().__init__(message)
        self.message = message

NON_JSONIFIABLE_TYPES = {"date", "timeofday", "datetime"}

def jsonifiable_value(value, column_type):
    '''
    Python doesn't jsonify dates, datetimes, or times properly, so
    convert them to isoformat strings.  Return everything else as is
    Arguments:
        value -- the value to be converted
        column_type -- the SDTP type of the value
    Returns
        A jsonifiable form of the value
    '''
    if value is None:
        return None
    if column_type in NON_JSONIFIABLE_TYPES:
        return value.isoformat()
    else:
        return value

def jsonifiable_row(row, column_types):
    '''
    Return the jsonified form of the row, using jsonifiable_value for each element
    Arguments:
        row -- the row to be converted
        column_types -- the types of each element of the row
    Returns
        A row of jsonifiable values
    '''
    return [jsonifiable_value(row[i], column_types[i]) for i in range(len(row))]


def jsonifiable_rows(rows, column_types):
    '''
    Return the jsonifiable form of the list of rows, using jasonifiable_row for each row
    Arguments:
        rows -- the list of rows to be converted
        column_types -- the types of each element of the row
    Returns
        A list of rows  of jsonified values
    '''
    return [jsonifiable_row(row, column_types) for row in rows]


def jsonifiable_column(column, column_type):
    '''
    Return a jsonifiable version of the column of values, using jsonifiable_value
    to do the conversion.  We actually cheat a little, only calling _jsonifiable_value if column_type
    is one of SDML_TIME, "date", "datetime"
    '''
    if column_type in NON_JSONIFIABLE_TYPES:
        return [jsonifiable_value(value, column_type) for value in column]
    else:
        return column
    
        
def convert_list_to_type(sdml_type, value_list, type_converter):
    '''
    Convert value_list to sdml_type, so that comparisons can be done.  Currently only works for lists of string, number, and boolean.
    Returns a default value if value can't be converted
    Note that it's the responsibility of the object which provides the rows to always provide the correct types,
    so this really should always just return a new copy of value_list
    Arguments:
        sdml_type: type to convert to
        value_list: list of values to be converted
        typeConverter: the SDMLTypeConverter
    Returns:
        value_list with each element cast to the correct type
    '''
    try:
        return  [type_converter.convert(sdml_type, elem) for elem in value_list]
        
        # result = []
        # for i in range(len(value_list)): result.append(convert_to_type(sdml_type, value_list[i]))
        # return result
    except Exception as exc:
        raise InvalidDataException(f'Failed to convert {value_list} to {sdml_type}')
    
def convert_row_to_type_list(sdml_type_list, row, type_converter):
    # called from convert_rows_to_type_list, which should error check
    # to make sure that the row is the same length as sdml_type_list
    return [type_converter.convert(sdml_type_list[i], row[i]) for i in range(len(row))]


def convert_rows_to_type_list(sdml_type_list, rows, type_converter):
    '''
    Convert the list of rows to the appropriate sdml types,
    '''
    length = len(sdml_type_list)
    

    for row in rows:
        # print("convert_rows_to_type_list received types:", sdml_type_list)
        # print("Row:", row)
        # print("Expected length:", length, "Actual length:", len(row))

        if len(row) != length:
            raise InvalidDataException(f'Length mismatch: required number of columns {length}, length {row} = {len(row)}')
    return  [convert_row_to_type_list(sdml_type_list, row, type_converter) for row in rows]
    
def convert_dict_to_type(sdml_type, value_dict, type_converter):
    '''
    Convert value_dict to sdml_type, so that comparisons can be done.  Currently only works for lists of string, number, and boolean.

    Returns a default value if value can't be converted
    Note that it's the responsibility of the object which provides the rows to always provide the correct types,
    so this really should always just return a new copy of value_list
    Arguments:
        sdml_type: type to convert to
        value_dict: dictionary of values to be converted
    Returns:
        value_dict with each value in the dictionary cast to the correct type
    '''
    result = {}
    try:
        for (key, value) in value_dict.items():
            result[key] = type_converter.convert(sdml_type, value)
        return result
    except Exception as exc:
        raise InvalidDataException(f'Failed to convert {value_dict} to {sdml_type}')

#
# Classes and methods to support authentication for RemoteSDMLTables and the sdtp
# client.
#
from typing import TypedDict, Union, Optional
import os

class EnvAuthMethod(TypedDict):
    '''
    The authentication token is in an the environment variable env
    '''
    env: str

class PathAuthMethod(TypedDict):
    '''
    The authentication token is in the file at path
    '''
    path: str

class ValueAuthMethod(TypedDict):
    '''
    The authentication token is the value
    '''
    value: str

AuthMethod = Union[EnvAuthMethod, PathAuthMethod, ValueAuthMethod]

def resolve_auth_method(method: AuthMethod) -> Optional[str]:
    """
    Resolve an AuthMethod dict to a credential string.
    Returns None if the method can't be satisfied (env var/file missing, etc.).
    """
    if "env" in method:
        return os.environ.get(method["env"])
    elif "path" in method:
        try:
            with open(os.path.expanduser(method["path"]), "r") as f:
                return f.read().strip()
        except Exception:
            return None
    elif "value" in method:
        return method["value"]
    return None

import numpy as np
import datetime

def is_scalar(value):
    return (
        np.isscalar(value) or
        value is None or
        isinstance(value, (str, bytes, datetime.date, datetime.datetime, datetime.time, bool))
    )

class SDMLTypeConverter:
    '''
    Converts Python structures to SDML objects, with a number of options.
    Attributes:
        null_sentinels: Strings which should be converted into None
        strict: if True, raise an InvalidDataException for unparseable data.  If False, return None
        dayfirst: Are strings of the form 2/1/25 January 2, 2025 or February 1, 2025?
    '''
    def __init__(self, null_sentinels=None, strict=True, dayfirst=False):
        default_null_sentinels = {
            'None', 'none', 'nan', 'NaN', 'NaT', 'null', 'Null', '', '<NA>'
        }
        self.null_sentinels = null_sentinels or default_null_sentinels
        self.normalized_null_sentinels = {s.lower() for s in self.null_sentinels}
        self.strict = strict
        self.dayfirst = dayfirst
        self.error_log = {}

    def _noneOrError_(self, value, sdml_type):
        self.error_log.setdefault(sdml_type, []).append(value)
        if self.strict:
            raise InvalidDataException(f"Can't convert {value} to {sdml_type}")
        return math.nan if sdml_type == 'number' else None

    def is_null(self, value):
        try:
            return value is None or pd.isnull(value) or (isinstance(value, str) and value.strip().lower() in self.normalized_null_sentinels)
        except Exception:
            return False
        
    
    def convert(self, sdml_type, value):
        # dispatch based on sdml_type


        method = getattr(self, f'convert_{sdml_type}', self.convert_default)
        return method(value)
    
    def convert_default(self, value):
        return value  # fallback
    
    def convert_number(self, value):
        if self.is_null(value):
            return math.nan
        
        # Your number logic here
        if not is_scalar(value):
            return self._noneOrError_(value, 'number')

        
        if isinstance(value, int) or isinstance(value, float):
            return value


        # try an automated conversion to float.  If it fails, it still
        # might be an int in base 2, 8, or 16, so pass the error to try
        # all of those

        try:
            return float(value)
        except (ValueError, TypeError):
            pass
        # if we get here, it must be a string or won't convert
        if not isinstance(value, str):
            return self._noneOrError_(value, 'number')
        # Try to convert to binary, octal, decimal
        for base in [2, 8, 16]:
            try:
                return int(value, base)
            except ValueError:
                pass
        return self._noneOrError_(value, 'number')

    def convert_boolean(self, value):
        # Your boolean logic here
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value in {'True', 'true', 't', '1', '1.0'}
        if isinstance(value, int):
            return value != 0
        if isinstance(value, float):
            return value != 0.0
        return False

    def convert_datetime(self, value):

        if self.is_null(value):
            return None
      
        if not is_scalar(value):
            return self._noneOrError_(value, 'datetime')
        
        if isinstance(value, datetime.datetime):
            return value
        if type(value) == datetime.date:
            return datetime.datetime(value.year, value.month, value.day, 0, 0, 0)
        if isinstance(value, str):
            try:
                return parser.parse(value, dayfirst=self.dayfirst, fuzzy=True)
            except Exception:
                pass
        return self._noneOrError_(value, 'datetime')

    def convert_date(self, value):
        if self.is_null(value):
            return None
        
        if not is_scalar(value):
            return self._noneOrError_(value, 'date')
        
        if type(value) == datetime.date:
            return value
        if type(value) == datetime.datetime:
            return value.date()
        if isinstance(value, str):
            try:
                return parser.parse(value, dayfirst=self.dayfirst, fuzzy=True).date()
            except Exception:
                pass
        return self._noneOrError_(value, 'date')
    
    def convert_timeofday(self, value):
        
        if self.is_null(value):
            return None
        if not is_scalar(value):
            return self._noneOrError_(value, 'timeofday')
        
        if type(value) == datetime.time:
            return value
        if  type(value) == datetime.datetime:
            return value.time()
        if isinstance(value, str):
            try:
                return parser.parse(value, fuzzy=True).time()
            except Exception:
                pass
        return self._noneOrError_(value, 'timeofday')

    def convert_string(self, value):
        try:
            return str(value) if value is not None else None
        except Exception:
            return self._noneOrError_(value, 'string')
        