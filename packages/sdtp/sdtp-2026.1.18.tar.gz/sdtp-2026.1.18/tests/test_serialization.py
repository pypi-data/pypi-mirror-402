from sdtp.sdtp_filter import make_filter

def test_to_filter_spec_roundtrip_atomic():
    spec = {
        "operator": "IN_LIST",
        "column": "foo",
        "values": [1, 2, 3]
    }
    filt = make_filter(spec)
    out = filt.to_filter_spec()
    assert out == spec

def test_to_filter_spec_roundtrip_compound():
    spec = {
        "operator": "ALL",
        "arguments": [
            {"operator": "IN_LIST", "column": "foo", "values": [1,2,3]},
            {"operator": "GE", "column": "bar", "value": 10}
        ]
    }
    filt = make_filter(spec)
    out = filt.to_filter_spec()
    assert out == spec

def test_to_filter_spec_roundtrip_macroexpanded():
    spec = {
        "operator": "IN_RANGE",
        "column": "foo",
        "min_val": 5,
        "max_val": 10,
        "inclusive": "both"
    }
    filt = make_filter(spec)
    out = filt.to_filter_spec()
    # It won't match input spec exactly, since macroexpansion changes it!
    assert out["operator"] == "ALL"
    assert len(out["arguments"]) == 2
