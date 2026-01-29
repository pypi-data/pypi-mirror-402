#  The Simple Data Transfer Protcol

This is a reference server and library  for the Simple Data Transfer Protocol.  It demonstrates the Simple Data Transfer Protocol Server API.  It also functions as an open framework, so new Tables can be attached to the Simple Data Transfer Protocol server by providing a Class with a `get_rows()` method and a `schema` property.
The README.md file in each directory gives the documentation for the utilities and classes in that directory.  

The structure is as follows:
```
├── sdtp
│   ├── sdtp_server: A reference SDTP server and middleware
│   ├── sdtp: The basic SDTP types, including Filters and Tables
```
  
# The Simple Data Transfer Protocol

The SDTP Server implements the Simple Data Transfer Protocol, a universal way to query and transmit tabular data.  The SDTP uses http/https as the underlying transport protocol.  There is no client; rather, a program accessing an SDTP server creates a `RemoteSDMLTable` (see `sdtp.sdtp_table.py`) and accesses that through the standard SDTP Table methods.

This is a quick summary of the Simple Data Transfer Protocol.  A more extended description can be found at:


## Basic Data Structure
The core data structure of the SDTP is a _table_, which is simply a list of list of values. Conceptually, it is equivalent to a SQL database table; each column has a specific type and each row is of the same, fixed length.  The Python definitions are in sdtp.sdtp_table.py.  `type` and `schema` are  the only mandatory entries for a table.  `type` is a strng specifying the table table.  `schema` is a list of columns, each of which is a dictionary with two mandatory fields: `name` and `type`.  Other fields (e.g., to express units or other metadata) are permitted.

The Python implementation of table types is in  `sdtp.sdtp_table.py`

### Simple Data Transfer Protocol Data Types
This is a list of the permissible types.  Each column of a table is of one of these types
See sdtp.sdtp_utils.py.  The native types these convert to are language-specific
1. SDML_STRING: A string.  In Python, class str.
2. SDML_NUMBER: A real or an integer.  In Python, class float or class int.
3. SDML_BOOLEAN: true or false. In Python, class bool.
4. SDML_DATE: A date.  In Python, class datetime.date
5. SDML_DATETIME: A datetime.  In Python, class datetime.datetime
6. SDML_TIME_OF_DAY: A time.  In Python, class datetime.time

