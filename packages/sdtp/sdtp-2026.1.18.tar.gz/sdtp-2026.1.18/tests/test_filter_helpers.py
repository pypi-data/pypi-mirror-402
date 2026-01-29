import pytest
from sdtp.sdtp_filter import ANY, ALL, NONE, NEQ, EQ, IN_LIST, GE, REGEX, GT, LE, LT
from sdtp.sdtp_filter import InListFilter, GEFilter, GTFilter, LEFilter, LTFilter, RegexFilter, AnyFilter, AllFilter, NoneFilter


from datetime import date, datetime, time

def test_in_list_normalizes_dates():
  d1 = date(2024, 5, 4)
  d2 = datetime(2024, 5, 5, 12, 0)
  spec = IN_LIST("when", [d1, d2, "foo", 42])
  assert spec["operator"] == "IN_LIST"
  assert spec["column"] == "when"
  # Should all be ISO strings (or primitive)
  assert spec["values"] == [d1.isoformat(), d2.isoformat(), "foo", 42]

def test_ge_normalizes_datetime():
  t = time(15, 30)
  spec = GE("at", t)
  assert spec["operator"] == "GE"
  assert spec["column"] == "at"
  assert spec["value"] == t.isoformat()

def test_regex_output():
  spec = REGEX("foo", r"\d{3}-[a-z]+")
  assert spec["operator"] == "REGEX_MATCH"
  assert spec["column"] == "foo"
  assert spec["expression"] == r"\d{3}-[a-z]+"

def test_any_list_and_varargs():
  f1 = GE("score", 90)
  f2 = IN_LIST("category", ["A", "B"])
  # As list
  c1 = ANY([f1, f2])
  # As varargs
  c2 = ANY(f1, f2)
  for c in (c1, c2):
    assert c["operator"] == "ANY"
    assert c["arguments"] == [f1, f2]
    # No objects, only dicts in arguments
    assert all(isinstance(x, dict) for x in c["arguments"])

# Run with:
# pytest tests/test_sdql_helpers_minimal.py -q

def test_any_varargs_and_list_are_equal():
  f1 = {"operator": "GE", "column": "x", "value": 1}
  f2 = {"operator": "LT", "column": "y", "value": 10}

  # Both forms should be equivalent
  

  a1 = ANY([f1, f2])
  a2 = ANY(f1, f2)
  assert a1 == a2
  assert a1["operator"] == "ANY"
  assert a1["arguments"] == [f1, f2]

  l1 = ALL([f1, f2])
  l2 = ALL(f1, f2)
  assert l1 == l2
  assert l1["operator"] == "ALL"
  assert l1["arguments"] == [f1, f2]

  n1 = NONE([f1, f2])
  n2 = NONE(f1, f2)
  assert n1 == n2
  assert n1["operator"] == "NONE"
  assert n1["arguments"] == [f1, f2]

def test_neq_is_none_of_eq():

  f = NEQ("z", 42)
  expected = {
    "operator": "NONE",
    "arguments": [
      EQ("z", 42)
    ]
  }
  assert f == expected

def test_matches():
  assert IN_LIST('y', [3]) == InListFilter(operator="IN_LIST", column="y", values=[3]).to_filter_spec()
  assert EQ('y', 3) == InListFilter(operator="IN_LIST", column="y", values=[3]).to_filter_spec()
  assert GE('y', 3) == GEFilter(operator="GE", column="y", value=3).to_filter_spec()
  assert GT('y', 3) == GTFilter(operator="GT", column="y", value=3).to_filter_spec()
  assert LE('y', 3) == LEFilter(operator="LE", column="y", value=3).to_filter_spec()
  assert LT('y', 3) == LTFilter(operator="LT", column="y", value=3).to_filter_spec()
  assert REGEX('y', '^foo') == RegexFilter(operator="REGEX_MATCH", column="y", expression="^foo").to_filter_spec()
  assert ANY(LE('y', 3), GT('z', 2)) == ANY([LE('y', 3), GT('z', 2)])
  arguments = [LEFilter(operator="LE", column="y", value=3), GTFilter(operator="GT", column="z", value=2)]
  assert ANY(LE('y', 3), GT('z', 2))  == AnyFilter(operator= 'ANY', arguments=arguments).to_filter_spec()
  assert ALL(LE('y', 3), GT('z', 2)) == ALL([LE('y', 3), GT('z', 2)])
  assert ALL(LE('y', 3), GT('z', 2))  == AllFilter(operator= 'ALL', arguments=arguments).to_filter_spec()
  assert NONE(LE('y', 3), GT('z', 2)) == NONE([LE('y', 3), GT('z', 2)])
  assert NONE(LE('y', 3), GT('z', 2))  == NoneFilter(operator= 'NONE', arguments=arguments).to_filter_spec()
  assert NEQ('y', 3) == NONE(EQ('y', 3))