import json
from collections.abc import Callable
from contextlib import contextmanager
from typing import Optional

import urllib3.exceptions

from lakewatch_api import ApiException


class ConflictError(Exception):
    """
    Simple exception wrapper for 409 errors returned from the API
    """

    def __init__(self, resource: str, identifier: str, message: str) -> None:
        self.resource = resource
        self.identifier = identifier
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return f"Conflict: resource_type='{self.resource}' identifier='{self.identifier}' message='{self.message}'"


class NotFoundError(Exception):
    """
    Simple exception wrapper for 404 errors returned from the API
    """

    def __init__(
        self, identifier: str, message: str, resource_type: str = None
    ) -> None:
        self.identifier = identifier
        self.message = message
        self.resource_type = resource_type
        super().__init__(message)

    def __str__(self) -> str:
        if self.resource_type:
            return f"NotFound: resource_type='{self.resource_type}' identifier='{self.identifier}' message='{self.message}'"
        return f"NotFound: identifier='{self.identifier}' message='{self.message}'"


class BadRequestError(Exception):
    """
    Simple exception wrapper for 400 errors returned from the API
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return f"BadRequest: message='{self.message}'"


class UnauthorizedError(Exception):
    """
    Simple exception wrapper for 401 errors returned from the API
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return f"Unauthorized: message='{self.message}'"


class ForbiddenError(Exception):
    """
    Simple exception wrapper for 403 errors returned from the API
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return f"Forbidden: message='{self.message}'"


class WorkspaceLookupError(Exception):
    """Internal exception wrapper for workspace lookup errors"""

    def __init__(self, message: str, reason: Exception = None) -> None:
        self.message = message
        self.reason = reason
        super().__init__(message)

    def __str__(self) -> str:
        return f"Workspace lookup error: {self.message}"



def handle_errors(f: Callable) -> Callable:
    """
    A decorator that handles errors returned from the API.

    :param f: the function that could return an API error
    :return: The output from the callable 'f'. If an Api error was raise,
             re-cast it to a library error before re-raising.
    """

    def error_handler(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ApiException as e:
            body = json.loads(e.body)
            if e.status == 400:
                raise BadRequestError(body["message"])
            if e.status == 401:
                raise BadRequestError(body["message"])
            if e.status == 403:
                raise ForbiddenError(body["message"])
            if e.status == 404:
                raise NotFoundError(
                    body["identifier"], body["message"], body.get("resourceType")
                )
            if e.status == 409:
                raise ConflictError(
                    body["resourceType"], body["identifier"], body["message"]
                )
            else:
                raise e
        except Exception as e:
            raise e

    return error_handler


@contextmanager
def error_handler(**context):
    """
    A context manager that handles errors returned from the API.

    Within the context, if an API error is raised, it is re-cast to a library
    error before re-raising.

    :param context: Optional context including 'workspace_url' and 'host' for
                    better error messages in region mismatch scenarios.
    """

    workspace_url = context.get("workspace_url")
    current_host = context.get("host")

    try:
        yield
    except ApiException as e:
        body = json.loads(e.body)
        if e.status == 400:
            raise BadRequestError(body["message"])
        if e.status == 401:
            raise BadRequestError(body["message"])
        if e.status == 403:
            raise ForbiddenError(body["message"])
        if e.status == 404:
            raise NotFoundError(
                body["identifier"], body["message"], body.get("resourceType")
            )
        if e.status == 409:
            raise ConflictError(
                body["resourceType"], body["identifier"], body["message"]
            )
        else:
            raise e
    except (urllib3.exceptions.SSLError, urllib3.exceptions.MaxRetryError) as e:
        # Check if this is a region mismatch issue
        # TODO: this has been removed until we understand how regions will
        #       need to be supported moving forward.

        # Raise the original error, if not
        raise e
    except Exception as e:
        raise e

