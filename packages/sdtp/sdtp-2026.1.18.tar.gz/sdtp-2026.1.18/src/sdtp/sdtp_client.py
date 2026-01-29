import os
from typing import List, Optional, Dict, Any, Union
import requests
from .sdtp_utils import AuthMethod, resolve_auth_method
import yaml  # pip install pyyaml


class SDTPClientError(Exception):
    """Custom exception for SDTP client errors."""
    pass

def _process_response(response: requests.Response) -> Any:
    """
    Process an HTTP response:
      - Raises SDTPClientError for HTTP or SDTP errors with useful info.
      - Returns decoded JSON if possible, else raw text.
    """
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        # Try to extract error info from response, if any
        try:
            err = response.json()
            msg = err.get('message') or str(err)
        except Exception:
            msg = response.text.strip() or str(e)
        raise SDTPClientError(
            f"HTTP {response.status_code} error: {msg}"
        ) from e

    # Try to decode as JSON; fallback to text
    try:
        return response.json()
    except Exception:
        return response.text

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.sdtp_client_config.yaml")


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads and validates the SDTPClient YAML config file.

    Returns:
        Dict[str, AuthMethod] -- The credentials mapping (URL -> AuthMethod).
    Raises:
        Exception on parse or validation error.
    """
    if config_path is None:
        config_path = os.environ.get("SDTP_CLIENT_CONFIG", DEFAULT_CONFIG_PATH)
    config_path = os.path.expanduser(config_path)
    if not os.path.exists(config_path):
        # raise FileNotFoundError(f"Config file not found: {config_path}")
        print(f"Warning: No SDTP config file found at {config_path}. Proceeding with no credentials.")
        return {} # Or None

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Expect config with a 'credentials' mapping
    creds = config.get("credentials")
    if not isinstance(creds, dict):
        raise ValueError("Missing or invalid 'credentials' section in config.")

    for url, method in creds.items():
        if not isinstance(method, dict) or len(method) != 1 or not any(
            k in method for k in ("env", "path", "value")
        ):
            raise ValueError(f"Invalid AuthMethod for {url}: {method}")
    return creds  # type: Dict[str, AuthMethod]


def _query_credential_method(creds: Dict, url: str) -> Optional[AuthMethod]:
    """
    Utility for SDTPClient: Given a credentials mapping and a url, return the
    AuthMethod for that url, or 'default', or None if neither exists.
    """
    return creds.get(url) or creds.get('default')


    
class SDTPClient:
    """
    Minimal SDTP Client: Connects to SDTP REST endpoints with robust, flexible authentication.
   
    # Credential Discovery & Authentication

    SDTPClient uses a YAML config file as a minimal password manager, mapping each SDTP server URL to a credential retrieval method:

      - `env`: Get the credential from a named environment variable (supports ephemeral tokens from IdP or orchestration).
      - `path`: Read the credential from a file (works with secrets managers or file mounts).
      - `value`: Use the explicit token value (for dev/test only).

    The config file is read at instantiation (default: `~/.sdtp_client_config.yaml`), and may be overridden by the `SDTP_CLIENT_CONFIG` env var or `config_path` argument.

    For each API call:
      1. If an explicit `auth` argument is supplied, it overrides all other methods for that call only.
      2. Otherwise, the credential method for the client's server URL is looked up in the config file.
      3. If no entry is found for the URL, the 'default' entry (if any) is used.
      4. If no credential method is found, no Authorization header is sent (anonymous access).

    All credential methods are re-evaluated at each call — changes to env vars or files are picked up automatically.

    Power users may also specify `headers` per method to override or add HTTP headers directly.

    # Convenience Methods

    SDTPClient provides high-level helpers to build table schemas, filter specs, and DataFrames, minimizing boilerplate and making SDTP more accessible for data science and ETL workflows.

    See the user documentation for full config format, method details, and best practices.
    """

    def __init__(
        self,
        url: str,
        config_path: Optional[str] = "~/.sdtp_client_config.yaml",
        auth: Optional[AuthMethod] = None
    ):
        """
        Args:
            url: Base URL of the SDTP server (e.g., "http://localhost:5000")
            config_path: Optional path to the YAML credential config file (default: "~/.sdtp_client_config.yaml").
            auth: Optional explicit AuthMethod for this client (overrides config).
        """
        self.url = url.rstrip("/")
        self.credentials = load_config(config_path)
        self.auth = None
        if auth:
            self.auth = auth
        else:
            self.auth = _query_credential_method(self.credentials, self.url)
            

    def clear(self):
      """
      Clear the stored credential method for this client.
      After calling, further calls will use config or explicit per-method auth.
      """
      self.auth = None

    def query_credential_method(self, url: Optional[str] = None) -> Optional[AuthMethod]:
        """
        Return the authentication method (AuthMethod) for the specified URL, as stored in this client's credentials mapping.

        Args:
            url: The server URL to query (defaults to this client's URL if None).

        Returns:
            The AuthMethod dict (e.g., {'env': ...}, {'path': ...}, or {'value': ...}),
            or None if no method is configured for this URL.

        Example:
            method = client.query_credential_method()
            # returns this client's method

            method = client.query_credential_method("https://other.example.com")
            # returns method for another URL (if in credentials)
        """
        effective_url = url if url else self.url
        return _query_credential_method(self.credentials, effective_url)

    def _resolve_effective_token(self, offered: Optional[Union[str, AuthMethod]]) -> Optional[str]:
        """
        Given an offered credential (string token, AuthMethod, or None),
        returns the correct token to use according to precedence.

        Args:
            offered: May be a string (token), an AuthMethod dict, or None.

        Returns:
            The resolved token (str), or None if nothing can be resolved.
        """
        if isinstance(offered, str):
            return offered
        elif isinstance(offered, dict):
            return resolve_auth_method(offered)
        elif self.auth is not None:
            return resolve_auth_method(self.auth)
        else:
            return None

    def _auth_header(self, offered: Optional[Union[str, AuthMethod]]) -> Optional[Dict]:
        """
        Return the Authorization header for a call, if an auth token is
        provided.  Uses _resolve_effective_token to get the token
        Args:
            offered: May be a string (token), an AuthMethod dict, or None.

        Returns:
            Dict[str, str]: Authorization header (e.g., {'Authorization': 'Bearer ...'}) if a token is found,
            else None.
        """
        token = self._resolve_effective_token(offered)
        return {'Authorization': f'Bearer {token}'} if token else None
    
    def _do_get_request(self, url: str, offered_auth: Optional[Union[str, AuthMethod]]) -> Any:
        """
        Send a GET request to the specified URL with optional authorization.

        Args:
            url: The endpoint URL to query.
            offered_auth: Optional string token or AuthMethod dict to use for this call.

        Returns:
            Parsed JSON from the response (if possible), or raw text.

        Raises:
            SDTPClientError if the response indicates an error.
        """
        headers = {'Accept': 'application/json'}
        # auth_header = self._auth_header(offered_auth)
        token = self._resolve_effective_token(offered_auth)
        if token:
            headers['Authorization'] = f'Bearer {token}'
        response = requests.get(url, headers=headers) 
        return _process_response(response)
    
    def list_tables(self, auth: Optional[Union[str, AuthMethod]] = None) -> List[str]:
        """
        Returns a list of table names from the server.

        Args:
            auth: Optional string token or AuthMethod dict to use for this call.

        Returns:
            List[str]: list of table names.

        Raises:
            SDTPClientError: SDTPClientError on a bad response.
        """
        query = f'{self.url}/get_table_names'
        return self._do_get_request(query, auth)
    
    def get_tables(self, auth: Optional[Union[str, AuthMethod]] = None) -> Dict[str, Dict]:
        """
        Returns a dictionary indexed by table name with values the schema for each table.

        Args:
            auth: Optional string token or AuthMethod dict to use for this call.

        Returns:
            Dict[Dict]:  Dictionary of table schemas

        Raises:
            SDTPClientError: SDTPClientError on a bad response.
        """
        query = f'{self.url}/get_tables'
        return self._do_get_request(query, auth)
    


    def get_table_schema(
        self,
        table_name: str,
        auth: Optional[Union[str, AuthMethod]] = None
    ) -> List[Dict[str, str]]:
        """
        Returns the schema for a table.

        Args:
            table_name: Table to get the schema for.
            auth: Optional string token or AuthMethod dict for this call.

        Returns:
            List[Dict[str, str]]: Schema for the table.

        Raises:
            SDTPClientError: SDTPClientError on a bad response.
        """
        query = f"{self.url}/get_table_schema?table_name={table_name}"
        return self._do_get_request(query, auth)

    def _execute_column_query(
        self,
        query: str,
        table_name: str,
        column_name: str,
        auth: Optional[Union[str, AuthMethod]] = None
    ) -> List[Any]:
        """
        Utility to execute query?table_name=table_name&column_name=column_name.
        This covers /get_range_spec, /get_all_values, /get_column.

        Args:
            query: Route name (e.g., 'get_range_spec').
            table_name: Table containing the column.
            column_name: Column for the query.
            auth: Optional string token or AuthMethod dict for this call.

        Returns:
            List[Any]: Result of the query.

        Raises:
            SDTPClientError: SDTPClientError on a bad response.
        """
        query_to_execute = f"{self.url}/{query}?table_name={table_name}&column_name={column_name}"
        return self._do_get_request(query_to_execute, auth)

    def get_range_spec(
        self,
        table_name: str,
        column_name: str,
        auth: Optional[Union[str, AuthMethod]] = None
    ) -> List[Any]:
        """
        Returns [min, max] for a column.

        Args:
            table_name: Table containing the column.
            column_name: Column to get min/max for.
            auth: Optional string token or AuthMethod dict for this call.

        Returns:
            List[Any]: List of length 2: [min, max]

        Raises:
            SDTPClientError: SDTPClientError on a bad response.
        """
        return self._execute_column_query('get_range_spec', table_name, column_name, auth)

    def get_all_values(
        self,
        table_name: str,
        column_name: str,
        auth: Optional[Union[str, AuthMethod]] = None
    ) -> List[Any]:
        """
        Returns all distinct values for a column.

        Args:
            table_name: Table containing the column.
            column_name: Column to get values for.
            auth: Optional string token or AuthMethod dict for this call.

        Returns:
            List[Any]: List of column values.

        Raises:
            SDTPClientError: SDTPClientError on a bad response.
        """
        return self._execute_column_query('get_all_values', table_name, column_name, auth)

    def get_column(
        self,
        table_name: str,
        column_name: str,
        auth: Optional[Union[str, AuthMethod]] = None
    ) -> List[Any]:
        """
        Returns the entire column as a list.

        Args:
            table_name: Table containing the column.
            column_name: Column to get.
            auth: Optional string token or AuthMethod dict for this call.

        Returns:
            List[Any]: The column as a list.

        Raises:
            SDTPClientError: SDTPClientError on a bad response.
        """
        return self._execute_column_query('get_column', table_name, column_name, auth)



    def get_filtered_rows(
        self,
        table: str,
        columns: Optional[List[str]] = None,
        filter: Optional[Dict[str, Any]] = None,
        result_format: Optional[str] = None,
        auth: Optional[Union[str, AuthMethod]] = None,
    ) -> Any:
        """
        POST /get_filtered_rows — Fetch filtered rows from a table.

        Args:
            table: Name of the table (required).
            columns: List of columns to return (optional).
            filter: SDTP filter spec (optional).
            result_format: Output format (optional).
            auth: Auth token or method for this request (overrides all others).

        Returns:
            List of rows (list of lists), or as specified by result_format.

        Raises:
            SDTPClientError: SDTPClientError on a bad response.
        """
        headers = {'Accept': 'application/json'}
        token = self._resolve_effective_token(auth)
        if token:
            headers['Authorization'] = f'Bearer {token}'
        body: Dict[str, Any] = {"table": table}
        if columns is not None:
            body["columns"] = columns
        if filter is not None:
            body["filter"] = filter
        if result_format is not None:
            body["result_format"] = result_format

        response = requests.post(
            f"{self.url}/get_filtered_rows",
            json=body,
            headers=headers
        )
        return _process_response(response)

    def echo_json_post(
        self,
        payload: dict,
        auth: Optional[Union[str, AuthMethod]] = None,
    ) -> dict:
        """
        POST /_echo_json_post — Echoes posted JSON (debug/testing only).

        Args:
            payload: Payload in JSON form.
            auth: Auth token or method for this request (overrides all others).

        Returns:
            The echoed payload (dict).

        Raises:
            SDTPClientError: SDTPClientError on a bad response.
        """
        headers = {'Accept': 'application/json'}
        token = self._resolve_effective_token(auth)
        if token:
            headers['Authorization'] = f'Bearer {token}'
        response = requests.post(
            f"{self.url}/_echo_json_post",
            json=payload,
            headers=headers
        )
        return _process_response(response)

    

    def table_exists(self, table_name: str, auth: Optional[Union[str, AuthMethod]] = None)->bool:
        """
        Return True if and only if table table_name exists on the server
        Args:
            table_name: Table to check.
            auth: Optional string token or AuthMethod dict for this call.
        Returns:
            bool: True if the table exists, False otherwise.
        """
        names = self.get_tables(auth).keys()
        return table_name in names
    

