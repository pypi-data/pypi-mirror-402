"""Module with utilities to interact with Azure DevOps."""
# Copyright (c) 2023, Fred Stober
# SPDX-License-Identifier: MIT

import json as jsonlib
import pathlib
from contextlib import suppress
from functools import lru_cache
from html.parser import HTMLParser
from typing import Annotated, Any, Literal, TypeAlias
from uuid import UUID

import requests
from pydantic import BaseModel, PositiveInt
from pydantic.networks import HttpUrl, UrlConstraints


class HTMLTextFilter(HTMLParser):
    """Filter HTML error pages for useful text."""

    def __init__(self) -> None:
        """Construct the HTML text filter."""
        self.text = ""
        super().__init__()
        self._tags: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Add tags to the stack."""
        del attrs
        self._tags.append(tag)

    def handle_endtag(self, tag: str) -> None:
        """Remove tags from the stack."""
        if self._tags.pop() != tag:
            err_msg = "Invalid end tag!"
            raise ValueError(err_msg)

    def handle_data(self, data: str) -> None:
        """Add data if the tag context is correct."""
        if "style" in self._tags:
            return
        self.text = (self.text + " " + data.strip()).strip()


AccessToken: TypeAlias = str

ADOUrl: TypeAlias = Annotated[
    HttpUrl,
    UrlConstraints(
        max_length=256,
        allowed_schemes=[
            "https",
        ],
    ),
]


class JsonPatchAdd(BaseModel):
    """Type to store JSON patch information to add data."""

    op: Literal["add"] = "add"
    path: str
    value: Any


def _is_json_patch(value: Any | list[Any] | list[dict[str, str]]) -> bool:
    """Check if the value is a JSON patch."""
    if not isinstance(value, list):
        return False
    for item in value:
        if not isinstance(item, dict):
            return False
        if "op" not in item:
            return False
        if "path" not in item:
            return False
    return True


def _get_content_type(*, has_data: bool, json_value: Any) -> str:
    """Get the appropriate content type."""
    if has_data:
        return "application/octet-stream"
    if _is_json_patch(json_value):
        return "application/json-patch+json"
    return "application/json"


class ApiCall(BaseModel):
    """Class to call Azure DevOps APIs."""

    access_token: AccessToken
    parameters: dict[str, int | str] = {}
    timeout: PositiveInt = 10
    url: ADOUrl

    def build_call(
        self,
        *args: str | int | UUID,
        parameters: dict[str, int | str] | None = None,
        version: str | None = None,
    ) -> "ApiCall":
        """Build API call from arguments."""
        parameters = parameters or {}
        if version is not None:
            parameters["api-version"] = version

        url_parts = [str(arg) for arg in args]
        new_url = "/".join([self.url.unicode_string().rstrip("/"), *url_parts])
        return ApiCall(
            access_token=self.access_token,
            parameters=parameters | self.parameters,
            timeout=self.timeout,
            url=ADOUrl(new_url),
        )

    @staticmethod
    def _get_error_message(response: requests.Response) -> str:
        """Construct useful error message."""
        with suppress(Exception):
            error_message: str = response.json()["message"]
            return error_message
        error_message = repr(response.content)
        with suppress(Exception):
            html_filter = HTMLTextFilter()
            html_filter.feed(response.content.decode("utf-8"))
            error_message = repr(html_filter.text)
        return f"Invalid error response: {error_message}"

    @staticmethod
    def _parse_response(response: requests.Response, *, raw: bool = False) -> Any:
        """Parse API response from Azure DevOps."""
        try:
            response.raise_for_status()
        except Exception as ex:
            error_message = ApiCall._get_error_message(response)
            raise RuntimeError(error_message) from ex
        if raw:
            return response.content
        if not response.content:  # Handle b'' return values
            return None
        try:
            return response.json()
        except Exception as ex:
            error_message = f"Invalid API response: {response.content!r}"
            raise ValueError(error_message) from ex

    @staticmethod
    @lru_cache(maxsize=8)
    def _get_session(access_token: str) -> requests.Session:
        session = requests.Session()
        session.trust_env = False
        session.auth = requests.auth.HTTPBasicAuth("", access_token)
        return session

    @staticmethod
    def _request(
        method: str,
        api_call: "ApiCall",
        json: Any = None,
        data: Any = None,
        *,
        raw: bool = False,
    ) -> Any:
        """Helper function to interact with the Azure DevOps API."""
        headers = {
            "Content-Type": _get_content_type(
                has_data=data is not None, json_value=json
            ),
        }
        kwargs = {}
        if json is not None:
            kwargs = {"json": json}
        if data is not None:
            kwargs = {"data": data}
        session = ApiCall._get_session(api_call.access_token)
        max_retries = 3
        for retry in range(max_retries, 0, -1):  # max_retries, ..., 1
            try:
                response = session.request(
                    method,
                    headers=headers,
                    params=api_call.parameters,
                    timeout=api_call.timeout,
                    url=api_call.url.unicode_string(),
                    **kwargs,
                )
                return ApiCall._parse_response(response, raw=raw)
            except ConnectionResetError:
                if retry == 1:
                    raise
        return None

    def get(
        self,
        *args: str | int | UUID,
        parameters: dict[str, int | str] | None = None,
        version: str | None = None,
    ) -> Any:
        """Helper function to interact with the Azure DevOps API via GET."""
        api_call = self.build_call(*args, parameters=parameters, version=version)
        return ApiCall._request("GET", api_call)

    def get_raw(
        self,
        *args: str | int | UUID,
        parameters: dict[str, int | str] | None = None,
        version: str | None = None,
    ) -> Any:
        """Helper function to interact with the Azure DevOps API via GET."""
        api_call = self.build_call(*args, parameters=parameters, version=version)
        return ApiCall._request("GET", api_call, raw=True)

    def put(
        self,
        *args: str | int | UUID,
        parameters: dict[str, int | str] | None = None,
        version: str | None = None,
        json: Any = None,
        data: Any = None,
    ) -> Any:
        """Helper function to interact with the Azure DevOps API via POST."""
        api_call = self.build_call(*args, parameters=parameters, version=version)
        return ApiCall._request("PUT", api_call, json=json, data=data)

    def post(
        self,
        *args: str | int | UUID,
        parameters: dict[str, int | str] | None = None,
        version: str | None = None,
        json: Any = None,
        data: Any = None,
    ) -> Any:
        """Helper function to interact with the Azure DevOps API via POST."""
        api_call = self.build_call(*args, parameters=parameters, version=version)
        return ApiCall._request("POST", api_call, json=json, data=data)

    def patch(
        self,
        *args: str | int | UUID,
        parameters: dict[str, int | str] | None = None,
        version: str | None = None,
        json: Any = None,
    ) -> Any:
        """Helper function to interact with the Azure DevOps API via PATCH."""
        api_call = self.build_call(*args, parameters=parameters, version=version)
        return ApiCall._request("PATCH", api_call, json=json)

    def delete(
        self,
        *args: str | int | UUID,
        parameters: dict[str, int | str] | None = None,
        version: str | None = None,
    ) -> Any:
        """Helper function to interact with the Azure DevOps API via DELETE."""
        api_call = self.build_call(*args, parameters=parameters, version=version)
        return ApiCall._request("DELETE", api_call)


def get_test_api_call() -> tuple[ApiCall, Any]:
    """Get API call object for testing."""
    test_config_file = pathlib.Path(__file__).resolve().parent / "test.json"
    test_config = jsonlib.load(test_config_file.open(encoding="utf-8"))
    test_api_call = ApiCall(
        access_token=test_config["access_token"],
        url=test_config["url"],
    )
    return test_api_call, test_config
