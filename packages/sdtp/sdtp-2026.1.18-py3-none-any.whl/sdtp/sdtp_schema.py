# Copyright (c) 2025, The Regents of the University of California (Regents)
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

from typing import TypedDict, Literal, Union, List, Optional, Tuple
import datetime
import pandas as pd

""" Types for the SDTP schema """

SDML_STRING = 'string'
SDML_NUMBER = 'number'
SDML_BOOLEAN = 'boolean'
SDML_DATE = 'date'
SDML_DATETIME = 'datetime'
SDML_TIME_OF_DAY = 'timeofday'

# ---- SDML Schema Types ----

SDMLType = Literal[
    "string",
    "number",
    "boolean",
    "date",
    "datetime",
    "timeofday"
]

# Optional: list for runtime introspection
SDML_SCHEMA_TYPES =  {
    "string",
    "number",
    "boolean",
    "date",
    "datetime",
    "timeofday"
}

# ---- Python Type Mapping ----

SDML_PYTHON_TYPES = {
    "string": {str},
    "number": {int, float},
    "boolean": {bool},
    "date": {datetime.date},
    "datetime": {datetime.datetime, pd.Timestamp},
    "timeofday": {datetime.time},
}

def type_check(sdml_type: str, val) -> bool:
    '''
    Check to make sure that the Python type of val matches the implementation
    of sdml_type
    Arguments:
      sdml_type: an SDMLType ()
      val:  a Python value (can be anything)
    '''
    """Check whether a value matches the given SDML type."""
    return type(val) in SDML_PYTHON_TYPES[sdml_type]

# ---- Schema Definitions ----

class ColumnSpec(TypedDict):
    '''
    A column is a dictionary: {"name", "type"}
    '''
    name: str
    type: Literal["string", "number", "boolean", "date", "datetime", "timeofday"]

def make_table_schema(columns: List[Tuple[str, Literal["string", "number", "boolean", "date", "datetime", "timeofday"]]]) -> List[ColumnSpec]:
    """
    Given a list of tuples of the form (<name>, <type>), return an SDTP table schema,
    which is a list of sdtp_schema.ColumnSpec. Raises a ValueError for an invalid type.
    Args:
        columns: List[Tuple[str, Literal["string", "number", "boolean", "date", "datetime", "timeofday"]]]
    Returns:
        The appropriate table schema
    Raises:
        ValueError if a type is not a valid sdtp_schema.SDMLType
    """
    errors = [column[1] for column in columns if column[1] not in SDML_SCHEMA_TYPES]
    if len(errors) > 0:
        raise ValueError(f'Invalid types {errors} sent to make_table_schema.  Valid types are {SDML_SCHEMA_TYPES}')
    return  [{"name": column[0], "type": column[1]} for column in columns]

def is_valid_sdml_type(t: str) -> bool:
    '''
    Returns True iff t is a valid SDML Type (["string", "number", "boolean", "date", "datetime", "timeofday"])
    Argument:
      t: a string
    '''
    return t in SDML_SCHEMA_TYPES

def validate_column_spec(col: dict) -> None:
    '''
    Validates that the given column dictionary includes required fields and a valid SDML type.
    Raises ValueError if invalid.
    Argument:
      col: a dictionary
    '''
    if "name" not in col or "type" not in col:
        raise ValueError("Column spec must include 'name' and 'type'")
    if not is_valid_sdml_type(col["type"]):
        raise ValueError(f"Invalid SDML type: {col['type']}")

def validate_remote_auth(auth: dict) -> None:
    '''
    Ensure that the selected auth type has the required parameters.
    Throws a ValueError if the auth type is unrecognized or the required
    parameter is not present.
    '''
    required_fields = {
        'env': 'env_var',
        'file': 'path',
        'token': 'value'
    }
    if not 'type' in auth:
        raise ValueError(f'Authorization object {auth} must have a type')
    if not auth['type'] in required_fields:
        raise ValueError(f'Authorization type {auth["type"]} is invalid.  Valid types are {required_fields.keys()}')
    required_field = required_fields[auth['type']]
    if required_field not in auth:
        raise ValueError(f'{auth["type"]} requires parameter {required_field} but this is not present in {auth}')

def _check_required_fields(table_schema: dict, table_type: str, required_fields: set):
    missing = required_fields - set(table_schema.keys())
    if missing:
        raise ValueError(
            f"{table_type} requires fields {required_fields}. Missing: {missing} from schema {table_schema}"
        )

def validate_table_schema(table_schema: dict) -> None:
    """
    Validates a table schema dictionary against known SDML types and structure.
    Raises ValueError on failure.

    Only 'schema' is allowed as the key for column definitions.
    """
    if "schema" not in table_schema:
        raise ValueError(f"Schema {table_schema} must include a 'schema' list (not 'columns')")
    if "columns" in table_schema:
        raise ValueError(
            f"Schema {table_schema} uses 'columns' — only 'schema' is supported. "
            "Please update your spec."
        )

    if not isinstance(table_schema["schema"], list):
        raise ValueError(f"{table_schema['schema']} must be a list of columns")

    for col in table_schema['schema']:
        validate_column_spec(col)

    table_type = table_schema.get("type")
    if not table_type:
        raise ValueError("Schema must include a 'type' field")
    
    required_fields_by_type = {
        "RemoteSDMLTable": {"url", "table_name"},
        "RowTable": {"rows"}
    }

    if table_type not in required_fields_by_type:
        raise ValueError(f"Unknown or unsupported table type: {table_type}")

    if table_type == "remote" and "auth" in table_schema:
        validate_remote_auth(table_schema["auth"])

    _check_required_fields(table_schema, table_type, required_fields_by_type[table_type])

# --- Base Table Schema ---
class BaseTableSchema(TypedDict):
    '''
    The base schema for a Table.  A Table MUST have a type, which is a valid table, and
    a schema, which is a ColumnSpec list.
    '''
    type: str  # Table type: "RowTable", "RemoteSDMLTable", etc.
    schema: list[ColumnSpec]

# --- Row Table Schema ---
class RowTableSchema(BaseTableSchema):
    '''
    The schema for a RowTable.  The type of a RowTable is "RowTable", and it must have a "rows" field.
    '''
    type: Literal["RowTable"]
    rows: list[list]

# --- RemoteAuthSpec ---
class RemoteAuthSpec(TypedDict, total=False):
    '''
    Specification of a Remote Authentication, for use with RemoteTables.
    It currently supports tokens, env variables, and files.
    '''
    type: Literal["bearer"]
    value: str
    file_path: str
    env_var: str

# --- Remote Table Schema ---
class RemoteTableSchema(BaseTableSchema):
    '''
    The schema for a RemoteTable.  The type of a RemoteTable is "RemoteSDMLTable", and it must have "url"
    and "table_name" fields.  An auth field is optional.
    '''
    type: Literal["RemoteSDMLTable"]
    url: str
    table_name: str
    auth: Optional[RemoteAuthSpec]

# --- Unified Table Schema Union ---
TableSchema = Union[RowTableSchema, RemoteTableSchema]

# --- Simple make_schema() dispatcher ---
def _make_table_schema(obj: dict):
    '''
    Converts a dict into the right kind of TableSchema
    '''
    table_type = obj.get("type")
    validate_table_schema(obj) 
    return obj  # type: ignore
