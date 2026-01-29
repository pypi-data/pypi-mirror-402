
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

from __future__ import annotations
import re
from pydantic import BaseModel, PrivateAttr
from typing import Dict, List, Any, Union
from datetime import date, time, datetime
from .sdtp_utils import InvalidDataException


PrimitiveType = Union[str, float, int, bool]
DateLike = Union[datetime, date, time]
GDPType = Union[PrimitiveType, DateLike]

def is_primitive(val):
    return isinstance(val, (str, int, float, bool))

def format_error(msg: str, spec: Dict[str, Any]) -> str:
    return f"{msg}. Filter spec: {spec}"


def parse_iso(val):
    # Try to parse as date, time, or datetime; fallback to original value
    if isinstance(val, str):
        for parser in (date.fromisoformat, time.fromisoformat, datetime.fromisoformat):
            try:
                return parser(val)
            except Exception:
                pass
    return val


class SDQLFilter(BaseModel):
  """
  Abstract base class for all filters.  
  """
  operator: str

  def to_filter_spec(self):
    '''
    Generate a dictionary form of the SDQLFilter.  This is primarily for use on the client side, where
    A SDQLFilter can be constructed, and then a JSONified form of the dictionary version can be passed to
    the server for server-side filtering.  It's also useful for testing and debugging
    Returns:
        A dictionary form of the Filter
    '''
    raise NotImplementedError("to_filter_spec must be implemented by subclass")
    
  
  def matches(self, row, columns):
    # override in subclass
    return False

class ColumnFilter(SDQLFilter):
  """
  Abstract base class for IN_LIST, GE, LE, LT, GT, REGEX_MATCH filters
  """
  column: str

  def matches(self, row, columns):
    """
    Every ColumnFilter picks out the appropriate value from the row and runs the test on that, 
    so do that once, here
    """
    try:
      index = columns.index(self.column)
      return self.matches_value(row[index])
    except ValueError:
      return False
  
  def matches_value(self, value):
    # override in subclass
    return False
  
class InListFilter(ColumnFilter):
  """
  Implement an "IN_LIST" filter, which passes all rows in which the 
  value of column is in the list given by values
  Arguments:
    values: list of values to check for
  """

  values:List[PrimitiveType]
  _compare_values: list = PrivateAttr()

  def model_post_init(self, context: Any) -> None:
    super().model_post_init(context)
    self._compare_values = [parse_iso(v) for v in self.values]

  
  def matches_value(self, value):
    return value in self._compare_values
  
  def to_filter_spec(self):
    return {
      "operator": self.operator,
      "column": self.column,
      "values": self.values
    }

class CompareFilter(ColumnFilter):
  """
  Superclass for "GE", "LE", "GT", "LT" operators.  Takes care of
  finding the compare_value and generating the dictionary form
  """
  value: PrimitiveType
  _compare_value: PrimitiveType = PrivateAttr()

  def model_post_init(self, context: Any) -> None:
    super().model_post_init(context)
    self._compare_value = parse_iso(self.value) # type: ignore

  def to_filter_spec(self):
    return {
      "operator": self.operator,
      "column": self.column,
      "value": self.value
    }

class GEFilter(CompareFilter):
  """
  Implement >=
  """
  def matches_value(self, value):
    try:
      return value >= self._compare_value
    except TypeError:
      return False
  
class GTFilter(CompareFilter):
  """
  Implement > 
  """
  def matches_value(self, value):
    try:
      return value > self._compare_value
    except TypeError:
      return False

class LEFilter(CompareFilter):
  """
  Implement <=
  """
  def matches_value(self, value):
    try:
      return value <= self._compare_value
    except TypeError:
      return False

class LTFilter(CompareFilter):
  """
  Implement < 
  """
  def matches_value(self, value):
    try:
      return value < self._compare_value
    except TypeError:
      return False


class RegexFilter(ColumnFilter):
  """
  Implement a REGEX filter, which passes all rows in which the 
  value of column matches the regular expression expression

  """
  expression: str
  _regex = PrivateAttr()
  def model_post_init(self, context: Any) -> None:
    super().model_post_init(context)
    self._regex = re.compile(self.expression)

  def matches_value(self, value):
    return isinstance(value, str) and self._regex.fullmatch(value) is not None
  
  def to_filter_spec(self):
    return  {
      "operator": "REGEX_MATCH",
      "column": self.column,
      "expression": self.expression
    }


class CompoundFilter(SDQLFilter):
  """
  Superclass for a CompoundFilter (ALL, ANY, or NONE).  Just
  generates the intermediate form and implements a utility which
  maps a match across all arguments
  Arguments:
    operator: one of ANY, ALL, or NONE
    arguments: set of subfilters
  """
  arguments: List[SDQLFilter]

  def to_filter_spec(self):
    return {
      "operator": self.operator,
      "arguments": [f.to_filter_spec() for f in self.arguments]
    }
  
  def arguments_match(self, row, columns):
    return [argument.matches(row, columns) for argument in self.arguments]
  
class AllFilter(CompoundFilter):
  """
  An ALL Filter -- matches a row if ALL of the arguments match on the
  column
  """
  def matches(self, row, columns):
    return not (False in self.arguments_match(row, columns))

class AnyFilter(CompoundFilter):
  """
  An ANY Filter -- matches a row if ANY of the arguments match on the
  column
  """ 
  def matches(self, row, columns):
    return True in self.arguments_match(row, columns)

class NoneFilter(CompoundFilter):
  """
  A None Filter -- matches a row if NONE  of the arguments match on the
  column
  Arguments:
    arguments: set of subfilters
  """
  def matches(self, row, columns):
    return not (True in self.arguments_match(row, columns))

FILTER_CLASSES = {
  'IN_LIST': InListFilter,
  'GE': GEFilter,
  'LE': LEFilter,
  'LT': LTFilter,
  'GT': GTFilter,
  'REGEX_MATCH': RegexFilter,
  'ALL': AllFilter,
  'ANY': AnyFilter,
  'NONE': NoneFilter
}


FilterUnion = Union[
    InListFilter,
    GEFilter, LEFilter, GTFilter, LTFilter,
    RegexFilter,        # if you define it
    AllFilter, AnyFilter, NoneFilter
]
SDQLFilter.model_rebuild()

SDQL_FILTER_FIELDS = {
    'ALL': {'arguments'},
    'ANY': {'arguments'},
    'NONE': {'arguments'},
    'IN_LIST': {'column', 'values'},
    'IN_RANGE': {'column', 'max_val', 'min_val', 'inclusive'},
    'GE': {'column', 'value'},
    'GT': {'column', 'value'},
    'LE': {'column', 'value'},
    'LT': {'column', 'value'},
    'REGEX_MATCH': {'column', 'expression'}
}


# --- Use the discriminator for auto-parsing ---

SDQL_FILTER_OPERATORS = set(FILTER_CLASSES.keys())

def expand_in_range_spec(spec):
  """
  Expands an IN_RANGE filter spec into a list of atomic comparison specs.
  """
  min_val = spec.get("min_val")
  max_val = spec.get("max_val")
  inclusive = spec.get("inclusive", "both")
  column = spec["column"]

  atomic_specs = []
  # Left (min)
  if min_val is not None:
    op = "GE" if inclusive in ("both", "left") else "GT"
    atomic_specs.append({"operator": op, "column": column, "value": min_val})
  # Right (max)
  if max_val is not None:
    op = "LE" if inclusive in ("both", "right") else "LT"
    atomic_specs.append({"operator": op, "column": column,  "value": max_val})
  return atomic_specs[0] if len(atomic_specs) == 1 else {"operator": "ALL", "arguments": atomic_specs}


def make_filter(filter_spec):
  """
  Make a filter from a filter_spec.  Note that filter_spec should
  be free of errors (run filter_spec_errors first)
  Arguments:
    filter_spec: A valid dictionary form of a filter
  Returns:
    An instance of SDQL Filters
  """
  operator = filter_spec["operator"]
  if operator == "IN_RANGE":
    filter_spec = expand_in_range_spec(filter_spec)
    operator = filter_spec["operator"]

  cls = FILTER_CLASSES.get(operator)
  if not cls:
    raise ValueError(f"Unknown filter operator: {operator}")
  if issubclass(cls, CompoundFilter):
    return cls(operator = operator, arguments=[make_filter(s) for s in filter_spec["arguments"]])
  return cls(**filter_spec)
  

def check_valid_spec(filter_spec: dict):
  '''
  Method which checks to make sure that a filter spec is valid.
  Does not return, but throws an InvalidDataException with an error message
  if the filter spec is invalid

  Arguments:
    filter_spec (dict): spec to test for validity
  '''
  try:
    f = make_filter(filter_spec)
  except Exception as e:
    raise InvalidDataException(e)
  

def check_valid_spec_return_boolean(filter_spec: dict):
  '''
  Method which checks to make sure that a filter spec is valid.
  Returns True if and only if filter_spec has no errors

  Arguments:
    filter_spec(dict): spec to test for validity
  '''
  try:
    f = make_filter(filter_spec)
    return True
  except Exception as e:
    return False
  
#------ High-Level Convenience Methods for Filters ---#

def _iso_or_raw(val: GDPType) -> PrimitiveType:
  if isinstance(val, (datetime, date, time)):
    return val.isoformat()
  return val 


def IN_LIST(column: str, values: List[GDPType]) -> Dict:
  '''
  Return an InListFilter with column column and values values
  '''
  return {"operator": 'IN_LIST', 'column': column, 'values': [_iso_or_raw(v) for v in values]}
  


def EQ(column: str, value: GDPType) -> Dict:
   '''
  Return an InListFilter with column column and values [value]
  '''
   return IN_LIST(column, [value])


def GE(column: str, value: GDPType) -> Dict:
  '''
  Return a GreaterEqual Filter with column column and value value
  '''
  return  {"operator": 'GE', 'column': column, 'value':  _iso_or_raw(value)}
  

def GT(column: str, value: GDPType) -> Dict:
  '''
  Return a Greater Filter with column column and value value
  '''
  return  {"operator": 'GT', 'column': column, 'value':  _iso_or_raw(value)}


def LE(column: str, value: GDPType) -> Dict:
  '''
  Return a Less than or Equal  Filter with column column and value value
  '''
  return  {"operator": 'LE', 'column': column, 'value':  _iso_or_raw(value)}


def LT(column: str, value: GDPType) -> Dict:
  '''
  Return a Less than Filter with column column and value value
  '''
  return  {"operator": 'LT', 'column': column, 'value':  _iso_or_raw(value)}

def REGEX(column: str, expression: str) -> Dict:
  '''
  Return a RegexFilter with column column and expression expression
  '''
  return RegexFilter(operator = 'REGEX_MATCH', column=column, expression=expression).to_filter_spec()

def _extract_args(*args) -> list:
  """
  Accepts ANY([f1, f2]) or ANY(f1, f2); always returns a list of filters.
  """
  if len(args) == 1 and isinstance(args[0], (list, tuple)):
    return list(args[0])
  else:
    return list(args)

def ANY(*args) -> dict:
  """
  Return an AnyFilter with the given arguments.
  Accepts ANY([f1, f2]) or ANY(f1, f2).
  """
  return {"operator": 'ANY', "arguments":_extract_args(*args)}

def ALL(*args) -> dict:
  """
  Return an AllFilter with the given arguments.
  Accepts ALL([f1, f2]) or ALL(f1, f2).
  """
  return  {"operator": 'ALL', "arguments":_extract_args(*args)}

def NONE(*args) -> dict:
  """
  Return a NoneFilter with the given arguments.
  Accepts NONE([f1, f2]) or NONE(f1, f2).
  """
  return  {"operator": 'NONE', "arguments":_extract_args(*args)}


def NEQ(column: str, value: PrimitiveType) -> dict:
  """
  Return a NEQ filter (not equal).
  """
  return NONE(EQ(column, value))
