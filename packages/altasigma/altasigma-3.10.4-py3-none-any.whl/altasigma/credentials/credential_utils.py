"""
Credential utilities for managing authentication and secure data source access. For example in the Workbench and in Code Capsules.

This module provides tools for obtaining, refreshing, and managing authentication 
credentials required to access various data sources within the AltaSigma ecosystem.
It supports both interactive authentication flows for notebooks and automated 
authentication for production environments.
"""
import logging

import requests
import json
from time import sleep
import os
from IPython.display import HTML, clear_output
from pathlib import Path

from altasigma.utils.notebook import is_in_notebook, display_or_print
from ..config.http_session import _http_session

logger = logging.getLogger(__name__)


class CredentialUtils:
    """
    Manages authentication and data source credential access.
    
    This class handles the complete credential lifecycle including token retrieval,
    refresh, storage, and data source-specific credential acquisition. It supports
    both interactive device authentication flows (for notebooks) and automated
    token refresh (for production).
    
    Attributes:
        _SECRET_FILE_PATH (str): Read-only path for mounted credentials in production.
        _TMP_FILE_PATH (str): Read/write path for working credentials storage.
        dashboard_api_host (str): AltaSigma installation host URL (external ingress).
    """

    # Read only. May be set or not. It's set when not executed in the workbench and then comes from a mounted secret.
    _SECRET_FILE_PATH = '/var/lib/altasigma_credentials.json'
    # Read/write. The working path for new tokens. Since the user jovyan typically does not have many permissions outside of home and /workbench it must be this.
    # Need a dir to allow an emptyDir mount
    _TMP_FILE_PATH = '/home/jovyan/altasigma/tmp_altasigma_credentials.json'
    # Does not actually have anything to do with the dashboard api. It's just the host for the AltaSigma installation. i.e. externalIngress
    # And it's used to access keycloak from outside, as usual, to get the correct issuer.
    dashboard_api_host: str

    def __init__(self, host_url=None):
        """
        Initialize the CredentialUtils with the AltaSigma host URL.
        
        Args:
            host_url (str, optional): The AltaSigma installation host URL.
                If None, uses the HOST_URL environment variable.
        """
        if host_url is None:
            self.dashboard_api_host = os.environ['HOST_URL']
        else:
            self.dashboard_api_host = host_url
        Path(self._TMP_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)

    def get_credentials(self, data_source_name: str) -> tuple[str, str, str] | tuple[None, None, None]:
        """
        Retrieve credentials for accessing a specific data source.
        
        This method handles the complete authentication flow, first trying to use
        existing tokens, refreshing if necessary, or initiating device authentication
        if no valid tokens exist.
        
        Args:
            data_source_name (str): Name of the data source to access.
            
        Returns:
            tuple: A tuple containing (accessKey, secretKey, expiresAt) if successful,
                  or (None, None, None) if credential retrieval failed.
        """
        (access_token, refresh_token) = self._existing_token()
        if access_token is None or refresh_token is None:
            (access_token, refresh_token) = self._device_auth_flow()

        return self._datasource_access(data_source_name=data_source_name, access_token=access_token)

    def _refresh_token(self, refresh_token: str) -> tuple[str, str] | tuple[None, None]:
        """
        Refresh an existing authentication token.
        
        Uses the refresh token to obtain a new access token and refresh token pair
        from the authentication server.

        Cases this handles:
        1. Workbench (Device Auth Flow):
             client_id env: id of the client created for this user on workbench start (jupyter-hun auth_utils.py)
                            e.g. workbench-136060b7-7a84-4b9f-b910-8abe3d64ff56
             client_secret env: secret of this client
        2. Workbench (Refresh Token from altasigma-frontend, passed in from the browser)
             client_id env: existing id from Device Auth Flow has been overwritten with "altasigma-frontend"
             client_secret env: existing secret from Device Auth Flow has been removed
        3. Orchestration Job
             client_id env: the client for tokens created like for a normal user "altasigma-frontend"
             client_secret env: empty because "altasigma-frontend" is a public client

        Args:
            refresh_token (str): The current refresh token.
            
        Returns:
            tuple: A tuple containing (access_token, refresh_token_new) if successful,
                  or (None, None) if refresh failed.
        """
        # The client_secret may not be set. This may happen when it's not executed in the workbench.
        client_id = os.environ['CLIENT_ID']
        client_secret = os.environ.get('CLIENT_SECRET')

        token_url = f'{self.dashboard_api_host}/auth/realms/altasigma/protocol/openid-connect/token'

        if client_secret is not None:
            data = {
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }
        else:
            data = {
                'client_id': client_id,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }

        response = _http_session().post(token_url, data=data)
        token_response = response.json()
        if "access_token" in token_response.keys():
            access_token = token_response["access_token"]
            refresh_token_new = token_response["refresh_token"]
            self._write_tokens_to_file(access_token=access_token, refresh_token=refresh_token_new)
            return access_token, refresh_token_new
        else:
            logger.error(f"Could not obtain a new refresh token. {token_response}")
            return None, None

    def _existing_token(self) -> tuple[str, str] | tuple[None, None]:
        """
        Check for and validate existing authentication tokens.
        
        Looks for tokens in temporary and secret file locations, and attempts
        to refresh them if found.

        Note: Currently always refreshes tokens for simplicity and to ensure validity.
        Future optimization: Check if access_token is still valid for sufficient time
        before refreshing to reduce unnecessary API calls.

        Returns:
            tuple: A tuple containing (access_token, refresh_token) if valid tokens exist,
                  or (None, None) if no valid tokens are found.
        """
        # check if there are any saved tokens
        # For a restart we expect to find a current token from the previous container (realtime module only). Normal jobs don't restart
        if os.path.exists(self._TMP_FILE_PATH):
            with open(self._TMP_FILE_PATH, 'rb') as file:
                contents = file.read().strip().decode('utf-8')

            credentials_json = json.loads(contents)

            if credentials_json['refresh_token'] == '':
                # This is unexpected because the file should only exist if it also contains a valid token. But the caller may still recover.
                logger.warning(f"Refresh token is missing from {self._TMP_FILE_PATH}")
                return None, None
            else:
                return self._refresh_token(credentials_json['refresh_token'])
        # Check if there is a mounted secret with tokens (initial tokens). Only for jobs, not in the Workbench
        if os.path.exists(self._SECRET_FILE_PATH):
            with open(self._SECRET_FILE_PATH, 'rb') as file:
                contents = file.read().strip().decode('utf-8')

            credentials_json = json.loads(contents)

            if credentials_json['refresh_token'] == '':
                # This is unexpected and a recovery is unlikely, but we can let the caller try
                logger.error(f"Refresh token is missing from {self._SECRET_FILE_PATH}")
                return None, None
            else:
                return self._refresh_token(credentials_json['refresh_token'])
        # Expected case for the first call from the workbench with the device flow auth
        else:
            return None, None

    def _write_tokens_to_file(self, access_token: str, refresh_token: str):
        """
        Save authentication tokens to temporary file storage.
        
        Args:
            access_token (str): The access token to save.
            refresh_token (str): The refresh token to save.
        """
        credentials_json = '{"access_token": "' + access_token + '", "refresh_token": "' + refresh_token + '"}'

        with open(self._TMP_FILE_PATH, 'w') as file:
            file.write(credentials_json)

    def _device_auth_flow(self) -> tuple[str, str] | tuple[None, None]:
        """
        Initiate an interactive device authentication flow.
        
        This method is designed for interactive sessions in notebooks where a user
        can follow a link to authenticate. It displays a URL for authentication
        and polls for completion.
        
        Returns:
            tuple: A tuple containing (access_token, refresh_token) if authentication succeeds,
                  or (None, None) if authentication fails.
                  
        Note:
            Should only be executed in workbench/notebook environments.
        """
        # retrieve URL for client authorization
        device_auth_url = f'{self.dashboard_api_host}/auth/realms/altasigma/protocol/openid-connect/auth/device'

        # Both client_id and secret are set when in the workbench
        client_id = os.environ['CLIENT_ID']
        client_secret = os.environ['CLIENT_SECRET']

        if client_id is None or client_secret is None:
            print("ERROR: environment variables for credentials are not set!")
            return None, None

        data = {
            'client_id': client_id,
            'client_secret': client_secret
        }

        response = _http_session().post(device_auth_url, data=data)
        if response.status_code == 200:
            device_response = response.json()
            device_code = device_response["device_code"]
            authorization_url = device_response["verification_uri_complete"]
            display_or_print(
                msg_notebook=HTML(
                    f'Please authenticate using the following link: <a href="{authorization_url}" target="_blank">{authorization_url}</a>'),
                msg_other=f'Please authenticate using the following link: {authorization_url}')
        else:
            print(f"ERROR: Unexpected response {response.status_code}, {response.text}")
            return None, None

        # retrieve token when the user has used the link
        token_url = f'{self.dashboard_api_host}/auth/realms/altasigma/protocol/openid-connect/token'

        data = {
            'device_code': device_code,
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
        }

        keep_polling = True
        access_token = None
        refresh_token = None
        i = 0
        while keep_polling:
            try:
                response = _http_session().post(token_url, data=data)
                if response.status_code == 200:
                    token_response = response.json()
                    if "access_token" in token_response.keys():
                        access_token = token_response["access_token"]
                        refresh_token = token_response["refresh_token"]
                        keep_polling = False
                elif response.status_code == 400 and response.json().get('error') == 'authorization_pending':
                    if is_in_notebook():
                        clear_output(wait=True)
                    display_or_print(msg_notebook=HTML(
                        f'Please authenticate using the following link: <a href="{authorization_url}" target="_blank">{authorization_url}</a>'),
                        msg_other=f'Please authenticate using the following link: {authorization_url}')
                    display_or_print(
                        msg_notebook=HTML(f"Authorization pending {'.' * i}"),
                        msg_other=f"Authorization pending {'.' * i}")
                    i = (i + 1) % 4
                else:
                    print(f"ERROR: Unexpected response from keycloak: {response.status_code}, {response.text}")
                    keep_polling = False
                sleep(10)
            except requests.RequestException as e:
                print(f"ERROR: {e}")

        # store tokens in file, so the user does not have to re-authorize for every request
        self._write_tokens_to_file(access_token=access_token, refresh_token=refresh_token)
        return access_token, refresh_token

    def _datasource_access(self, data_source_name: str, access_token: str) -> tuple[str, str, str] | tuple[
        None, None, None]:
        """
        Retrieve credentials for a specific data source using an authenticated token.
        
        This method queries the data management API to find the specified data source
        and retrieve its access credentials.
        
        Args:
            data_source_name (str): Name of the data source to access.
            access_token (str): A valid authentication token.
            
        Returns:
            tuple: A tuple containing either:
                  - (accessKey, secretKey, expiresAt) for key-based sources
                  - (username, password, expiresAt) for password-based sources
                  - (None, None, None) if credential retrieval failed
        """
        header_get_cred = {'Authorization': f'Bearer {access_token}'}
        data_sources_request = _http_session().get(f'{self.dashboard_api_host}/dataman/datasources',
                                                   headers=header_get_cred)
        if data_sources_request.status_code == 200:
            data_sources_response = data_sources_request.json()
            # use data_source_name to search for fitting data source code
            data_source = [entry for entry in data_sources_response if entry["name"] == data_source_name][0]
            data_source_code = data_source["code"]
            data_source_type = data_source["ds_type"]

            # request credentials for datasource
            url_get_cred = f'{self.dashboard_api_host}/dataman/{data_source_type}/{data_source_code}/credentials'
            res = _http_session().get(url_get_cred, headers=header_get_cred).json()

            if "accessKey" in res.keys():
                display_or_print(msg_notebook=HTML("Successfully obtained data source credentials"),
                                 msg_other="Successfully obtained data source credentials")
                return res["accessKey"], res["secretKey"], res["expiresAt"]
            if "password" in res.keys():
                display_or_print(
                    msg_notebook=HTML("Successfully obtained data source credentials"),
                    msg_other="Successfully obtained data source credentials")
                return res["username"], res["password"], res["expiresAt"]
            else:
                print(f"ERROR: failed to get credentials for data source {res}")
        else:
            print(
                f"ERROR: Unexpected response from dataman: {data_sources_request.status_code}, {data_sources_request.text}")
        return None, None, None


_credential_utils_instance = None


def _credential_utils():
    """Gets or creates a generic CredentialsUtils class.

    Returns:
        CredentialUtils
    """
    global _credential_utils_instance
    if _credential_utils_instance is not None:
        return _credential_utils_instance
    else:
        _credential_utils_instance = CredentialUtils()
        return _credential_utils_instance
