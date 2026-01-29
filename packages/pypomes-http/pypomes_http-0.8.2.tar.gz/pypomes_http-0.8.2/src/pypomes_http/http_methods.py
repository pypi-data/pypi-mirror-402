import requests
import sys
from enum import IntEnum, StrEnum
from logging import Logger
from io import BytesIO
from pypomes_core import APP_PREFIX, env_get_int, exc_format
from requests import Response
from typing import Any, BinaryIO


class HttpMethod(StrEnum):
    """
    HTTP methods.
    """
    DELETE = "DELETE"
    GET = "GET"
    HEAD = "HEAD"
    PATCH = "PATCH"
    POST = "POST"
    PUT = "PUT"


class HttpTimeout(IntEnum):
    """
    default timeouts for Http methods.
    """
    DELETE = env_get_int(key=f"{APP_PREFIX}_HTTP_DELETE_TIMEOUT",
                         def_value=300)
    GET = env_get_int(key=f"{APP_PREFIX}_HTTP_GET_TIMEOUT",
                      def_value=300)
    HEAD = env_get_int(key=f"{APP_PREFIX}_HTTP_HEAD_TIMEOUT",
                       def_value=300)
    PATCH = env_get_int(key=f"{APP_PREFIX}_HTTP_PATCH_TIMEOUT",
                        def_value=300)
    POST = env_get_int(key=f"{APP_PREFIX}_HTTP_POST_TIMEOUT",
                       def_value=300)
    PUT = env_get_int(key=f"{APP_PREFIX}_HTTP_PUT_TIMEOUT",
                      def_value=300)


def http_delete(url: str,
                headers: dict[str, str] = None,
                params: dict[str, Any] = None,
                data: dict[str, Any] = None,
                json: dict[str, Any] = None,
                timeout: float | None = HttpTimeout.DELETE,
                errors: list[str] = None,
                logger: Logger = None) -> Response:
    """
    Issue a *DELETE* request to the given *url*, and return the response received.

    :param url: the destination URL
    :param headers: optional headers
    :param params: optional parameters to send in the query string of the request
    :param data: optionaL data to send in the body of the request
    :param json: optional JSON to send in the body of the request
    :param timeout: request timeout, in seconds (defaults to HTTP_DELETE_TIMEOUT - use None to omit)
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the response to the *DELETE* operation, or *None* if an exception was raised
    """
    return http_rest(method=HttpMethod.DELETE,
                     url=url,
                     headers=headers,
                     params=params,
                     data=data,
                     json=json,
                     timeout=timeout,
                     errors=errors,
                     logger=logger)


def http_get(url: str,
             headers: dict[str, str] = None,
             params: dict[str, Any] = None,
             data: dict[str, Any] = None,
             json: dict[str, Any] = None,
             timeout: float | None = HttpTimeout.GET,
             errors: list[str] = None,
             logger: Logger = None) -> Response:
    """
    Issue a *GET* request to the given *url*, and return the response received.

    :param url: the destination URL
    :param headers: optional headers
    :param params: optional parameters to send in the query string of the request
    :param data: optionaL data to send in the body of the request
    :param json: optional JSON to send in the body of the request
    :param timeout: request timeout, in seconds (defaults to HTTP_GET_TIMEOUT - use None to omit)
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the response to the *GET* operation, or *None* if an exception was raised
    """
    return http_rest(method=HttpMethod.GET,
                     url=url,
                     headers=headers,
                     params=params,
                     data=data,
                     json=json,
                     timeout=timeout,
                     errors=errors,
                     logger=logger)


def http_head(url: str,
              headers: dict[str, str] = None,
              params: dict[str, Any] = None,
              data: dict[str, Any] = None,
              json: dict[str, Any] = None,
              timeout: float | None = HttpTimeout.HEAD,
              errors: list[str] = None,
              logger: Logger = None) -> Response:
    """
    Issue a *HEAD* request to the given *url*, and return the response received.

    :param url: the destination URL
    :param headers: optional headers
    :param params: optional parameters to send in the query string of the request
    :param data: optionaL data to send in the body of the request
    :param json: optional JSON to send in the body of the request
    :param timeout: request timeout, in seconds (defaults to HTTP_HEAD_TIMEOUT - use None to omit)
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the response to the *HEAD* operation, or *None* if an exception was raised
    """
    return http_rest(method=HttpMethod.HEAD,
                     url=url,
                     headers=headers,
                     params=params,
                     data=data,
                     json=json,
                     timeout=timeout,
                     errors=errors,
                     logger=logger)


def http_patch(url: str,
               headers: dict[str, str] = None,
               params: dict[str, Any] = None,
               data: dict[str, Any] = None,
               json: dict[str, Any] = None,
               timeout: float | None = HttpTimeout.PATCH,
               errors: list[str] = None,
               logger: Logger = None) -> Response:
    """
    Issue a *PATCH* request to the given *url*, and return the response received.

    :param url: the destination URL
    :param headers: optional headers
    :param params: optional parameters to send in the query string of the request
    :param data: optionaL data to send in the body of the request
    :param json: optional JSON to send in the body of the request
    :param timeout: request timeout, in seconds (defaults to HTTP_PATCH_TIMEOUT - use None to omit)
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the response to the *PATCH* operation, or *None* if an exception was raised
    """
    return http_rest(method=HttpMethod.PATCH,
                     url=url,
                     headers=headers,
                     params=params,
                     data=data,
                     json=json,
                     timeout=timeout,
                     errors=errors,
                     logger=logger)


def http_post(url: str,
              headers: dict[str, str] = None,
              params: dict[str, Any] = None,
              data: dict[str, Any] = None,
              json: dict[str, Any] = None,
              files: (dict[str, bytes | BinaryIO] |
                      dict[str, tuple[str, bytes | BinaryIO]] |
                      dict[str, tuple[str, bytes | BinaryIO, str]] |
                      dict[str, tuple[str, bytes | BinaryIO, str, dict[str, Any]]]) = None,
              timeout: float | None = HttpTimeout.POST,
              errors: list[str] = None,
              logger: Logger = None) -> Response:
    """
    Issue a *POST* request to the given *url*, and return the response received.

    To send multipart-encoded files, the optional *files* parameter is used, formatted as
    a *dict* holding pairs of *name* and:
      - a *file-content*, or
      - a *tuple* holding *file-name, file-content*, or
      - a *tuple* holding *file-name, file-content, content-type*, or
      - a *tuple* holding *file-name, file-content, content-type, custom-headers*
    These parameter elements are:
      - *file-name*: the name of the file
      _ *file-content*: the file contents, or a pointer obtained from *Path.open()* or *BytesIO*
      - *content-type*: the mimetype of the file
      - *custom-headers*: a *dict* containing additional headers for the file

    :param url: the destination URL
    :param headers: optional headers
    :param params: optional parameters to send in the query string of the request
    :param data: optionaL data to send in the body of the request
    :param json: optional JSON to send in the body of the request
    :param files: optionally, one or more files to send
    :param timeout: request timeout, in seconds (defaults to HTTP_POST_TIMEOUT - use None to omit)
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the response to the *POST* operation, or *None* if an exception was raised
    """
    return http_rest(method=HttpMethod.POST,
                     url=url,
                     headers=headers,
                     params=params,
                     data=data,
                     json=json,
                     files=files,
                     timeout=timeout,
                     errors=errors,
                     logger=logger)


def http_put(url: str,
             headers: dict[str, str] = None,
             params: dict[str, Any] = None,
             data: dict[str, Any] = None,
             json: dict[str, Any] = None,
             timeout: float | None = HttpTimeout.PUT,
             errors: list[str] = None,
             logger: Logger = None) -> Response:
    """
    Issue a *PUT* request to the given *url*, and return the response received.

    :param url: the destination URL
    :param headers: optional headers
    :param params: optional parameters to send in the query string of the request
    :param data: optionaL data to send in the body of the request
    :param json: optional JSON to send in the body of the request
    :param timeout: request timeout, in seconds (defaults to HTTP_PUT_TIMEOUT - use None to omit)
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the response to the *PUT* operation, or *None* if an exception was raised
    """
    return http_rest(method=HttpMethod.PUT,
                     url=url,
                     headers=headers,
                     params=params,
                     data=data,
                     json=json,
                     timeout=timeout,
                     errors=errors,
                     logger=logger)


def http_rest(method: HttpMethod,
              url: str,
              headers: dict[str, str] = None,
              params: dict[str, Any] = None,
              data: dict[str, Any] = None,
              json: dict[str, Any] = None,
              files: (dict[str, bytes | BinaryIO] |
                      dict[str, tuple[str, bytes | BinaryIO]] |
                      dict[str, tuple[str, bytes | BinaryIO, str]] |
                      dict[str, tuple[str, bytes | BinaryIO, str, dict[str, Any]]]) = None,
              timeout: float = None,
              errors: list[str] = None,
              logger: Logger = None) -> Response:
    """
    Issue a *REST* request to the given *url*, and return the response received.

    To send multipart-encoded files, the optional *files* parameter is used, formatted as
    a *dict* holding pairs of *name* and:
      - a *file-content*, or
      - a *tuple* holding *file-name, file-content*, or
      - a *tuple* holding *file-name, file-content, content-type*, or
      - a *tuple* holding *file-name, file-content, content-type, custom-headers*
    These parameter elements are:
      - *file-name*: the name of the file
      _ *file-content*: the file contents, or a pointer obtained from *Path.open()* or *BytesIO*
      - *content-type*: the mimetype of the file
      - *custom-headers*: a *dict* containing additional headers for the file
     The *files* parameter is considered if *method* is *POST*, and disregarded otherwise.

    :param method: the REST method to use (DELETE, GET, HEAD, PATCH, POST or PUT)
    :param url: the destination URL
    :param headers: optional headers
    :param params: optional parameters to send in the query string of the request
    :param data: optionaL data to send in the body of the request
    :param json: optional JSON to send in the body of the request
    :param files: optionally, one or more files to send
    :param timeout: request timeout, in seconds (defaults to 'None')
    :param errors: incidental error messages (might be a non-empty list)
    :param logger: optional logger
    :return: the response to the *REST* operation, or *None* if an exception was raised
    """
    # initialize the return variable
    result: Response | None = None

    if logger:
        logger.debug(msg=f"{method} '{url}'")

    # adjust the 'files' parameter, converting 'bytes' to a file pointer
    x_files: Any = None
    if method == HttpMethod.POST and isinstance(files, dict):
        # SANITY-CHECK: use a copy of 'files'
        x_files: dict[str, Any] = files.copy()
        for key, value in files.items():
            if isinstance(value, bytes):
                # 'files' is type 'dict[str, bytes]'
                x_files[key] = BytesIO(value)
                x_files[key].seek(0)
            elif isinstance(value, tuple) and isinstance(value[1], bytes):
                # 'value' is type 'tuple[str, bytes, ...]'
                x_files[key] = list(value)
                x_files[key][1] = BytesIO(value[1])
                x_files[key][1].seek(0)
                x_files[key] = tuple(x_files[key])

    # send the request
    err_msg: str | None = None
    if logger:
        logger.debug(f"{method} {url}")
    try:
        result = requests.request(method=method,
                                  url=url,
                                  headers=headers,
                                  params=params,
                                  data=data,
                                  json=json,
                                  files=x_files,
                                  timeout=timeout)

        # truth value of 'result': 'True' if 'result.status_code < 400'
        if not result:
            # no, report the problem
            err_msg = (f"{method} {url} failure, "
                       f"status {result.status_code}, reason '{result.reason}'")
        elif logger:
            # yes, log the result
            from .http_statuses import HttpStatus
            http_status: HttpStatus = HttpStatus(result.status_code)
            logger.debug(msg=f"{method} {url} success, status {http_status} ({http_status.name})")
    except Exception as e:
        # the operation raised an exception
        err_msg = exc_format(exc=e,
                             exc_info=sys.exc_info())
        err_msg = f"{method} {url} error, '{err_msg}'"

    # log and save the error
    if err_msg:
        if logger:
            logger.error(msg=err_msg)
        if isinstance(errors, list):
            errors.append(err_msg)

    return result
