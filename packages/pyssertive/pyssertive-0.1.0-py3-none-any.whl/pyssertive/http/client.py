from __future__ import annotations

from typing import Any

from django.http import HttpResponse
from django.test import Client

from pyssertive.http.assertions import (
    CookieAssertionsMixin,
    HeaderAssertionsMixin,
    HTMLContentAssertionsMixin,
    HttpStatusAssertionsMixin,
    JsonContentAssertionsMixin,
)
from pyssertive.http.debug import DebugResponseMixin
from pyssertive.http.django import (
    FormValidationAssertionsMixin,
    SessionAssertionsMixin,
    TemplateContextAssertionsMixin,
)


class FluentResponse(
    DebugResponseMixin,
    SessionAssertionsMixin,
    CookieAssertionsMixin,
    TemplateContextAssertionsMixin,
    FormValidationAssertionsMixin,
    HTMLContentAssertionsMixin,
    JsonContentAssertionsMixin,
    HeaderAssertionsMixin,
    HttpStatusAssertionsMixin,
):
    """
    Fluent assertion wrapper for Django HTTP responses.

    Example::

        response = client.get('/api/users/')
        FluentResponse(response).assert_ok().assert_json().assert_json_path('count', 10)
    """

    def __init__(self, response: HttpResponse) -> None:
        self._response: HttpResponse = response

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)

    @property
    def wrapped(self) -> HttpResponse:
        return self._response

    @property
    def status_code(self) -> int:
        return self._response.status_code

    @property
    def content(self) -> bytes:
        return self._response.content

    @property
    def headers(self) -> Any:
        return self._response.headers

    @property
    def cookies(self) -> Any:
        return self._response.cookies

    @property
    def charset(self) -> str | None:
        return self._response.charset

    @property
    def reason_phrase(self) -> str:
        return self._response.reason_phrase


class FluentHttpAssertClient:
    """
    Fluent wrapper for Django's test client.

    Example::

        client = FluentHttpAssertClient(Client())
        client.get('/api/').assert_ok().assert_json()
    """

    def __init__(self, base_client: Client) -> None:
        self._client: Client = base_client

    def get(self, *args: Any, **kwargs: Any) -> FluentResponse:
        response = self._client.get(*args, **kwargs)
        return FluentResponse(response)

    def post(self, *args: Any, **kwargs: Any) -> FluentResponse:
        response = self._client.post(*args, **kwargs)
        return FluentResponse(response)

    def put(self, *args: Any, **kwargs: Any) -> FluentResponse:
        response = self._client.put(*args, **kwargs)
        return FluentResponse(response)

    def patch(self, *args: Any, **kwargs: Any) -> FluentResponse:
        response = self._client.patch(*args, **kwargs)
        return FluentResponse(response)

    def delete(self, *args: Any, **kwargs: Any) -> FluentResponse:
        response = self._client.delete(*args, **kwargs)
        return FluentResponse(response)

    def head(self, *args: Any, **kwargs: Any) -> FluentResponse:
        response = self._client.head(*args, **kwargs)
        return FluentResponse(response)

    def options(self, *args: Any, **kwargs: Any) -> FluentResponse:
        response = self._client.options(*args, **kwargs)
        return FluentResponse(response)

    def trace(self, *args: Any, **kwargs: Any) -> FluentResponse:
        response = self._client.trace(*args, **kwargs)
        return FluentResponse(response)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)
