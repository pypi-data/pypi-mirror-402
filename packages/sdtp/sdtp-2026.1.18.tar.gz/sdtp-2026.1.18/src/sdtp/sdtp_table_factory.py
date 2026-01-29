'''
An SDMLTableFactory class and associated utilities.  The SDMLTableFactory builds
an SDMLTable of the appropriate type.  Each Table type has an associated Factory
class, and the factory class which builds the table  is registered with the
TABLE_REGISTRY.
Each SDMLFactory class has a single class method, 
build_table(table_spec, *args, **kwargs)
table_spec is a dictionary which must have two fields, type and schema
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
from abc import ABC, abstractmethod 
import inspect
from .sdtp_table import RowTable, RemoteSDMLTable
from .sdtp_utils import InvalidDataException
from .sdtp_schema import _make_table_schema


class SDMLTableFactory(ABC):
    '''
    A class which builds an SDMLTable of a specific type.  All SDMLTables have a schema, but after
    that the specification varies, depending on the method the table uses to get the table rows.
    Specific factories should subclass this and instantiate the class method build_table.
    The tag is the table type, simply a string which indicates which class of table should be
    built.
    A new SDMLTableFactory class should be built for each concrete subclass of SDMLTable, and ideally
    in the same file.  The SDMLTable subclass should put a "type" field in the intermediate form,
    and the value of "type" should be the type built by the SDTP Table field
    SDMLTableFactory is an abstract class -- each concrete subclass should call the init method on the 
    table_type on initialization.  build_table is the method which actually builds the table; the superclass 
    convenience version of the method throws an InvalidDataException if the spec has the wrong table type 
    Every subclass should set the table_type.  This attribute 
    registers the tables  which this Factory builds
    '''
   
    @classmethod
    def check_table_type(cls, table_type):
      '''
      Check to make sure the type is right.  If not, throw an InvalidDataException
      '''
      factory_class = TableBuilder.get_factory(table_type)
      if cls != factory_class:
          raise InvalidDataException(f"Wrong factory for {table_type}: expected {factory_class}, got {cls}")

    @classmethod
    @abstractmethod
    def build_table(cls, spec, *args, **kwargs):
        pass
      

class RowTableFactory(SDMLTableFactory):
    '''
    A factory to build RowTables -- in fact, all SDMLFixedTables.  build_table is very simple, just instantiating
    a RowTable on the rows and schema of the specification
    '''

    @classmethod
    def build_table(cls, spec, *args, **kwargs):
        cls.check_table_type(spec["type"])  
        table_spec = _make_table_schema(spec)
        allowed_keys = {'type_converter', 'strict', 'dayfirst'}
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in allowed_keys}
        return RowTable(table_spec['schema'], table_spec['rows'], **filtered_kwargs) # Type checking is done in the constructor


class RemoteSDMLTableFactory(SDMLTableFactory):
    '''
    A factory to build RemoteSDMLTables.  build_table is very simple, just instantiating
    a RemoteSDMLTables on the url and schema of the specification
    '''
    @classmethod
    def build_table(cls, table_spec, *args, **kwargs):
        cls.check_table_type(table_spec["type"])  
        spec = _make_table_schema(table_spec)

        return RemoteSDMLTable(
            table_spec['table_name'],
            spec['schema'],
            table_spec['url'],
            table_spec.get('auth'),
            table_spec.get('header_dict')
            
        ) 

class TableBuilder:
    '''
    A global table builder. This will build a table of any type.  This has four  methods, all class methods:
    (1) Build  a table from a specification
    (2) register a class to build a table for a type
    (3) Get the current mapping of table types to classes
    (4) Get the class for a particular table type
    '''
    table_registry = {}
    @classmethod
    def build_table(cls, spec, *args, **kwargs):
        '''
        Build a table from a spec.
        Argments:
          spec: an SDML table spec
          *args: additional arguments required to build the table, if any
          **kwargs: additional arguments required to build the table, if any
        Returns:
          The SDML Table
        Raises:
          Invalid Data Exception if the spec is not well-formed
        '''
        try:
            table_type = spec['type']
        except KeyError:
            raise InvalidDataException(f'{spec} does not have a table type')
        try:
            factory_class = cls.table_registry[table_type]['class']
        except KeyError:
          print('hello')
          raise InvalidDataException(f'{table_type} is  not have a valid table type.  Valid types are {list(cls.table_registry.keys())}')
        return factory_class.build_table(spec, *args, **kwargs)
    @classmethod

    def register_factory_class(cls, table_type: str, factory_class, locked = False):
        '''
        Register an SDMLTableFactory class to build tables of type table_type.
        If locked is True, then the SDMLTableFactory class can't be overriden by
        a subsequent register_factory_class invocation
        Arguments:
          table_type: the type of the table
          factory_class: the class to build it
          locked (default False): if True, the factory_class can't be overwritten
        Returns:
          None
        Raises:
          InvalidDataException if the type is already registered and locked, or if factory_class
          is not an SDMLFactoryClass
        '''
        if not inspect.isclass(factory_class) or not issubclass(factory_class, SDMLTableFactory):
          raise InvalidDataException(f"{factory_class} is not a subclass of SDMLTableFactory.")
   
        if table_type in cls.table_registry.keys():
            record = cls.table_registry[table_type]
            if record['class'] == factory_class:
                return
            elif record['locked']:
                raise InvalidDataException(f'The factory for {table_type} is locked')
        cls.table_registry[table_type] = {'class': factory_class, 'locked': locked}
    
    @classmethod
    def factory_class_registry(cls):
        '''
        Return the dictionary of table types to records (class, locked).  Note it returns 
        a COPY of the registry, so it can't be accidentally overwritten
        Arguments:
          None
        
        '''
        return cls.table_registry.copy()
    
    @classmethod
    def get_factory(cls, table_type):
        '''
        Get the class for table_type; return None if there is no class for tabletype
        Arguments:
          table_type: the type to get the class for
        Returns:
          the class which builds table_type, or None if there is no class
        Raises:
          None
        '''
        try:
            return cls.table_registry[table_type]['class']
        except KeyError:
            return None

TableBuilder.register_factory_class('RowTable', RowTableFactory, True)
TableBuilder.register_factory_class('RemoteSDMLTable', RemoteSDMLTableFactory, True)