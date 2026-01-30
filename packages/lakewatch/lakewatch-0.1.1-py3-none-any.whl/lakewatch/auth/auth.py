import abc
import base64
import os
import time
from datetime import datetime

from lakewatch_api import ApiClient
from databricks.sdk.errors import ResourceDoesNotExist

from lakewatch.conn.conn import get_base_conn
from lakewatch.errors.errors import error_handler

from databricks.sdk import WorkspaceClient
from typing import Optional


# Base path for the DASL API within Databricks
DASL_API_BASE_PATH = "/api/2.0/dasl-apiserver"

class Authorization(abc.ABC):
    """
    A common interface for Authentication
    """

    @abc.abstractmethod
    def client(self) -> ApiClient:
        raise NotImplementedError("conn method must be implemented")

    def workspace(self) -> str:
        raise NotImplementedError("client method must be implemented")

class NotebookAuth(Authorization):
    """
    Authorization implementation for use within Databricks notebooks.

    This auth class uses the native Databricks notebook context to obtain
    the API URL and token, then uses those directly to authenticate with
    the Lakewatch API (dasl-apiserver) running within Databricks.

    This is the simplest auth method when running inside a Databricks notebook
    as it requires no additional configuration.
    """

    def __init__(self):
        """
        Initialize NotebookAuth by extracting the API URL and token from
        the Databricks notebook context.

        :raises Exception: If not running inside a Databricks notebook.
        """
        if "DATABRICKS_RUNTIME_VERSION" not in os.environ:
            raise Exception(
                "NotebookAuth can only be used within a Databricks notebook. "
                "Use a different Authorization class outside of notebooks."
            )

        # Import dbutils only when inside a notebook context
        from databricks.sdk.runtime import dbutils

        context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()


        # Get the API URL and token from notebook context
        api_url = context.apiUrl().getOrElse(None)
        if api_url is None:
            raise Exception("Could not obtain API URL from notebook context")

        self._token = context.apiToken().getOrElse(None)
        if self._token is None:
            raise Exception("Could not obtain API token from notebook context")

        # Extract workspace name from the browser host name
        self._workspace = context.browserHostName().getOrElse(None)
        if self._workspace is None:
            raise Exception("Could not obtain workspace hostname from notebook context")

        # Build the full host URL for the DASL API
        host = f"{api_url}{DASL_API_BASE_PATH}"

        # Create the API client and configure authentication
        self._client = get_base_conn(host=host)
        # Set access_token on configuration so auth_settings() returns proper auth
        self._client.configuration.access_token = self._token

    def client(self) -> ApiClient:
        """
        Return an API client configured for the Lakewatch API.

        The client uses the native Databricks token which is managed by
        the notebook runtime, so no refresh logic is needed.

        :return: An API client with valid authentication.
        """
        return self._client

    def workspace(self) -> str:
        """
        Return the workspace hostname.

        :return: The workspace hostname (e.g., 'myworkspace.cloud.databricks.com').
        """
        return self._workspace
