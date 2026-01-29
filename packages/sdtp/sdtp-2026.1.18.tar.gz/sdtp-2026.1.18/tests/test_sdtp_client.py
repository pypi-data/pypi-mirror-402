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
import sys
sys.path.append('../src')
sys.path.append('./src')
from sdtp.sdtp_client import load_config, _query_credential_method, SDTPClient, SDTPClientError, _process_response
from unittest.mock import Mock
import yaml
import pytest
from requests import HTTPError


VALID_CONFIG = {
    "credentials": {
        "https://server1.example.com": {"env": "SDTP_API_TOKEN"},
        "https://server2.example.com": {"path": "~/.secrets/server2_token"},
        "default": {"value": "dummy-token"}
    }
}

INVALID_CREDENTIALS_CONFIG = {
    "credentials": {
        "https://bad.example.com": {"env": "SDTP_API_TOKEN", "path": "/bad/path"},  # too many keys
    }
}

NO_CREDENTIALS_CONFIG = {
    "not_credentials": {}
}
def make_response(
    status=200,
    json_data=None,
    text=None,
    raise_http=False,
    json_raises=False,
):
    response = Mock()
    response.status_code = status
    response.text = text or ""
    # Simulate .json() returning JSON or raising
    if json_raises:
        response.json.side_effect = Exception("Not JSON")
    else:
        response.json.return_value = json_data
    # Simulate .raise_for_status()
    if raise_http:
        response.raise_for_status.side_effect = HTTPError("Bad status")
    else:
        response.raise_for_status = lambda: None
    return response

def test_good_json():
    resp = make_response(json_data={"foo": "bar"})
    assert _process_response(resp) == {"foo": "bar"}

def test_good_not_json():
    resp = make_response(json_raises=True, text="not-json")
    assert _process_response(resp) == "not-json"

def test_bad_status_json_message():
    resp = make_response(
        status=400, 
        json_data={"message": "broken!"},
        raise_http=True
    )
    with pytest.raises(SDTPClientError) as e:
        _process_response(resp)
    assert "broken!" in str(e.value)

def test_bad_status_json_no_message():
    resp = make_response(
        status=500,
        json_data={"other": "fail"},
        raise_http=True
    )
    with pytest.raises(SDTPClientError) as e:
        _process_response(resp)
    assert "fail" in str(e.value)

def test_bad_status_text():
    resp = make_response(
        status=403,
        json_raises=True,
        text="Forbidden!",
        raise_http=True
    )
    with pytest.raises(SDTPClientError) as e:
        _process_response(resp)
    assert "Forbidden!" in str(e.value)

def test_bad_status_empty():
    resp = make_response(
        status=404,
        json_raises=True,
        text="",
        raise_http=True
    )
    with pytest.raises(SDTPClientError) as e:
        _process_response(resp)
    assert "404" in str(e.value)  # fallback is error string
    
@pytest.fixture
def tmp_yaml(tmp_path):
    def _make_yaml(data):
        file = tmp_path / "test_config.yaml"
        with open(file, "w") as f:
            yaml.safe_dump(data, f)
        return str(file)
    return _make_yaml

def test_valid_config_file(tmp_yaml):
    config_path = tmp_yaml(VALID_CONFIG)
    creds = load_config(config_path)
    assert "https://server1.example.com" in creds
    assert creds["default"]["value"] == "dummy-token"

def test_missing_config_file(tmp_path, monkeypatch):
    config_path = tmp_path / "no_such_file.yaml"
    creds = load_config(str(config_path))
    assert creds == {}

def test_invalid_authmethod(tmp_yaml):
    config_path = tmp_yaml(INVALID_CREDENTIALS_CONFIG)
    with pytest.raises(ValueError):
        load_config(config_path)

def test_no_credentials_section(tmp_yaml):
    config_path = tmp_yaml(NO_CREDENTIALS_CONFIG)
    with pytest.raises(ValueError):
        load_config(config_path)

def test_env_override(tmp_yaml, monkeypatch):
    config_path = tmp_yaml(VALID_CONFIG)
    monkeypatch.setenv("SDTP_CLIENT_CONFIG", config_path)
    creds = load_config(None)
    assert "https://server2.example.com" in creds

@pytest.fixture
def creds():
    return {
        "https://server1": {"env": "TOKEN1"},
        "https://server2": {"path": "/tmp/token2"},
        "default": {"value": "ABC"}
    }

def test_query_known_url(creds):
    method = _query_credential_method(creds, "https://server1")
    assert method == {"env": "TOKEN1"}

def test_query_other_known_url(creds):
    method = _query_credential_method(creds, "https://server2")
    assert method == {"path": "/tmp/token2"}

def test_query_default_used(creds):
    method = _query_credential_method(creds, "https://not-in-creds")
    assert method == {"value": "ABC"}

def test_query_none_found():
    creds = {"foo": {"env": "FOO"}}
    method = _query_credential_method(creds, "not-there")
    assert method is None

def test_empty_creds():
    assert _query_credential_method({}, "anything") is None

# Mock resolve_auth_method to just return the env/path/value name for test
def fake_resolve_auth_method(method):
    if "env" in method:
        return "envtoken"
    if "path" in method:
        return "pathtoken"
    if "value" in method:
        return method["value"]
    return None

@pytest.fixture
def monkeypatch_resolver(monkeypatch):
    monkeypatch.setattr("sdtp.sdtp_client.resolve_auth_method", fake_resolve_auth_method)


def make_config_file(tmp_path, creds_dict):
    import yaml
    config = {"credentials": creds_dict}
    file = tmp_path / "test_config.yaml"
    with open(file, "w") as f:
        yaml.safe_dump(config, f)
    return str(file)

def test_init_explicit_auth(monkeypatch_resolver, tmp_path, creds):
    # Explicit auth should override everything
    config_path = make_config_file(tmp_path, creds)
    client = SDTPClient("https://server1", config_path=config_path, auth={"value": "FOO"})
    assert client.auth == {"value": "FOO"}

def test_init_url_match(monkeypatch_resolver, tmp_path, creds):
    config_path = make_config_file(tmp_path, creds)
    client = SDTPClient("https://server2", config_path=config_path)
    assert client.auth == {"path": "/tmp/token2"}

def test_init_default(monkeypatch_resolver, tmp_path, creds):
    config_path = make_config_file(tmp_path, creds)
    client = SDTPClient("https://not-in-creds", config_path=config_path)
    assert client.auth == {"value": "ABC"}

def test_init_none(monkeypatch_resolver, tmp_path):
    config_path = make_config_file(tmp_path, {})
    client = SDTPClient("https://server", config_path=config_path)
    assert client.auth is None

def test_clear(monkeypatch_resolver, tmp_path, creds):
    config_path = make_config_file(tmp_path, creds)
    client = SDTPClient("https://server1", config_path=config_path)
    client.clear()
    assert client.auth is None

def test_query_credential_method(monkeypatch_resolver, tmp_path, creds):
    config_path = make_config_file(tmp_path, creds)
    client = SDTPClient("https://server1", config_path=config_path)
    assert client.query_credential_method("https://server1") == {"env": "TOKEN1"}
    assert client.query_credential_method("https://not-in-creds") == {"value": "ABC"}

def test_resolve_effective_token(monkeypatch_resolver, tmp_path, creds):
    config_path = make_config_file(tmp_path, creds)
    client = SDTPClient("https://server1", config_path=config_path)
    # 1. Offered string
    assert client._resolve_effective_token("supersecret") == "supersecret"
    # 2. Offered dict
    assert client._resolve_effective_token({"value": "bar"}) == "bar"
    # 3. None, but client.auth present
    assert client._resolve_effective_token(None) == "envtoken"
    # 4. None, no auth
    client.clear()
    assert client._resolve_effective_token(None) is None

def test_auth_header(monkeypatch_resolver, tmp_path, creds):
    config_path = make_config_file(tmp_path, creds)
    client = SDTPClient("https://server1", config_path=config_path)
    # With token
    assert client._auth_header("onetoken") == {"Authorization": "Bearer onetoken"}
    # With dict
    assert client._auth_header({"value": "bar"}) == {"Authorization": "Bearer bar"}
    # With None (should use client.auth)
    assert client._auth_header(None) == {"Authorization": "Bearer envtoken"}
    # After clear
    client.clear()
    assert client._auth_header(None) is None

def test_list_tables_requests(mocker):
    client = SDTPClient("https://foo")
    # Patch client._do_get_request to check internals, or patch requests.get
    mock_response = mocker.patch("requests.get")
    mock_response.return_value.status_code = 200
    mock_response.return_value.json.return_value = ["table1", "table2"]
    mock_response.return_value.raise_for_status = lambda: None
    mock_response.return_value.text = '["table1", "table2"]'
    
    result = client.list_tables(auth="mytoken")
    mock_response.assert_called_once()
    url = mock_response.call_args[0][0]
    headers = mock_response.call_args[1]['headers']
    assert url == "https://foo/get_table_names"
    assert headers["Authorization"] == "Bearer mytoken"
    assert headers["Accept"] == "application/json"
    assert result == ["table1", "table2"]

def test_get_filtered_rows_requests(mocker):
    client = SDTPClient("https://foo")
    mock_response = mocker.patch("requests.post")
    mock_response.return_value.status_code = 200
    mock_response.return_value.json.return_value = [{"row": 1}, {"row": 2}]
    mock_response.return_value.raise_for_status = lambda: None
    mock_response.return_value.text = '[{"row": 1}, {"row": 2}]'
    body = {
        "table": "mytable",
        "columns": ["a", "b"],
        "filter": {"operator": "IN_LIST", "column": "a", "values": [1, 2]},
        "result_format": "dict"
    }
    result = client.get_filtered_rows(
        table="mytable",
        columns=["a", "b"],
        filter={"operator": "IN_LIST", "column": "a", "values": [1, 2]},
        result_format="dict",
        auth="mytoken"
    )
    mock_response.assert_called_once()
    url = mock_response.call_args[0][0]
    headers = mock_response.call_args[1]['headers']
    json_payload = mock_response.call_args[1]['json']
    assert url == "https://foo/get_filtered_rows"
    assert headers["Authorization"] == "Bearer mytoken"
    assert headers["Accept"] == "application/json"
    assert json_payload == body
    assert result == [{"row": 1}, {"row": 2}]