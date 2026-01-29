import pytest

# Use your real filters; these examples assume import as in previous examples
from sdtp.sdtp_filter import AllFilter, AnyFilter, NoneFilter, NoneFilter, ColumnFilter

def always_true(*args, **kwargs): return True
def always_false(*args, **kwargs): return False

class DummyTrue(ColumnFilter):
    def matches_value(self, value): return True

class DummyFalse(ColumnFilter):
    def matches_value(self, value): return False

@pytest.mark.parametrize("Compound,expected", [
    (AllFilter(operator="ALL", arguments=[
        DummyTrue(operator="DUMMY", column="foo"),
        DummyTrue(operator="DUMMY", column="foo"),
    ]), True),
    (AllFilter(operator="ALL", arguments=[
        DummyTrue(operator="DUMMY", column="foo"),
        DummyFalse(operator="DUMMY", column="foo"),
    ]), False),
    (AllFilter(operator="ALL", arguments=[
        DummyFalse(operator="DUMMY", column="foo"),
        DummyFalse(operator="DUMMY", column="foo"),
    ]), False),
    (AllFilter(operator="ALL", arguments=[]), True),  # vacuously true
    (AllFilter(operator="ALL", arguments=[
        DummyTrue(operator="DUMMY", column="foo"),
    ]), True),
    (AllFilter(operator="ALL", arguments=[
        DummyFalse(operator="DUMMY", column="foo"),
    ]), False),
])
def test_all_filter_cases(Compound, expected):
    assert Compound.matches([None], ["foo"]) is expected

@pytest.mark.parametrize("Compound,expected", [
    (AnyFilter(operator="ANY", arguments=[
        DummyTrue(operator="DUMMY", column="foo"),
        DummyTrue(operator="DUMMY", column="foo"),
    ]), True),
    (AnyFilter(operator="ANY", arguments=[
        DummyTrue(operator="DUMMY", column="foo"),
        DummyFalse(operator="DUMMY", column="foo"),
    ]), True),
    (AnyFilter(operator="ANY", arguments=[
        DummyFalse(operator="DUMMY", column="foo"),
        DummyFalse(operator="DUMMY", column="foo"),
    ]), False),
    (AnyFilter(operator="ANY", arguments=[]), False),  # vacuously false
    (AnyFilter(operator="ANY", arguments=[
        DummyTrue(operator="DUMMY", column="foo"),
    ]), True),
    (AnyFilter(operator="ANY", arguments=[
        DummyFalse(operator="DUMMY", column="foo"),
    ]), False),
])
def test_any_filter_cases(Compound, expected):
    assert Compound.matches([None], ["foo"]) is expected

@pytest.mark.parametrize("Compound,expected", [
    (NoneFilter(operator="NONE", arguments=[
        DummyTrue(operator="DUMMY", column="foo"),
        DummyTrue(operator="DUMMY", column="foo"),
    ]), False),
    (NoneFilter(operator="NONE", arguments=[
        DummyTrue(operator="DUMMY", column="foo"),
        DummyFalse(operator="DUMMY", column="foo"),
    ]), False),
    (NoneFilter(operator="NONE", arguments=[
        DummyFalse(operator="DUMMY", column="foo"),
        DummyFalse(operator="DUMMY", column="foo"),
    ]), True),
    (NoneFilter(operator="NONE", arguments=[]), True),  # vacuously true
    (NoneFilter(operator="NONE", arguments=[
        DummyTrue(operator="DUMMY", column="foo"),
    ]), False),
    (NoneFilter(operator="NONE", arguments=[
        DummyFalse(operator="DUMMY", column="foo"),
    ]), True),
])
def test_none_filter_cases(Compound, expected):
    assert Compound.matches([None], ["foo"]) is expected

def test_compound_arguments_match_method():
    # One true, one false
    f1 = DummyTrue(operator="DUMMY", column="foo")
    f2 = DummyFalse(operator="DUMMY", column="foo")
    c = AllFilter(operator="ALL", arguments=[f1, f2])
    assert c.arguments_match([None], ["foo"]) == [True, False]
