from sdtp.sdtp_filter import expand_in_range_spec, make_filter
def spec_check(expected_operators, inclusive=None):
    spec = {
        "operator": "IN_RANGE",
        "column": "foo",
        "min_val": 5,
        "max_val": 10,
    }
    if inclusive is not None:
        spec["inclusive"] = inclusive
    
    expanded = expand_in_range_spec(spec)
    assert expanded["operator"] == "ALL"
    assert len(expanded["arguments"]) == 2
    ops = set(a["operator"] for a in expanded["arguments"])
    assert ops == expected_operators


def test_expand_in_range_spec_both_bounds():
    spec_check({"LE", "GE"})
    spec_check({"LE", "GE"}, "both")
    spec_check({"LT", "GE"}, "left")
    spec_check({"LE", "GT"}, "right")
    spec_check({"LT", "GT"}, "neither")
    

def test_expand_in_range_spec_one_bound():
    spec = {
        "operator": "IN_RANGE",
        "column": "foo",
        "min_val": 5,
        "inclusive": "left"
    }
    expanded = expand_in_range_spec(spec)
    assert expanded["operator"] == "GE" 

def test_expand_in_range_macro_match():
    # Actually constructs the filter and tests match logic
    spec = {
        "operator": "IN_RANGE",
        "column": "foo",
        "min_val": 5,
        "max_val": 10,
        "inclusive": "both"
    }
    filt = make_filter(spec)
    columns = ["foo"]
    assert filt.matches([5], columns)
    assert filt.matches([10], columns)
    assert filt.matches([7], columns)
    assert not filt.matches([4], columns)
    assert not filt.matches([11], columns)
