from __future__ import annotations

from typing import Any

from django.contrib.auth.models import AbstractBaseUser
from django.http import HttpRequest
from django.test import RequestFactory


class RequestBuilder:
    """
    Fluent builder for creating HttpRequest objects using Django's RequestFactory.

    Useful for unit testing views directly without going through the full
    HTTP request/response cycle (bypasses middleware and URL routing).

    Example::

        from pyssertive.http.request import RequestBuilder

        request = (
            RequestBuilder()
            .with_method("POST")
            .with_path("/api/users/")
            .with_body({"name": "John"})
            .with_user(user)
            .with_cookie("session", "abc123")
            .with_meta("HTTP_X_FORWARDED_FOR", "192.168.1.1")
            .build()
        )
        response = my_view(request)
    """

    def __init__(
        self,
        rf: RequestFactory | None = None,
        method: str = "GET",
        path: str = "/",
        data: dict[str, Any] | None = None,
    ) -> None:
        self.rf = rf or RequestFactory()
        self.method = method.upper()
        self.path = path
        self.data = data or {}
        self.user: AbstractBaseUser | None = None
        self.cookies: dict[str, str] = {}
        self.meta: dict[str, Any] = {}
        self.headers: dict[str, str] = {}
        self.custom_properties: dict[str, Any] = {}

    def with_method(self, method: str) -> RequestBuilder:
        self.method = method.upper()
        return self

    def with_path(self, path: str) -> RequestBuilder:
        self.path = path
        return self

    def with_data(self, data: dict[str, Any]) -> RequestBuilder:
        self.data = data
        return self

    def with_body(self, data: dict[str, Any]) -> RequestBuilder:
        if self.method not in ["POST", "PUT", "PATCH"]:
            raise ValueError(f"Cannot set body on {self.method} request")
        self.data = data
        return self

    def with_query_string(self, params: dict[str, Any]) -> RequestBuilder:
        self.data = params
        return self

    def with_user(self, user: AbstractBaseUser) -> RequestBuilder:
        self.user = user
        return self

    def with_cookie(self, key: str, value: Any) -> RequestBuilder:
        self.cookies[key] = str(value)
        return self

    def with_cookies(self, cookies: dict[str, Any]) -> RequestBuilder:
        for key, value in cookies.items():
            self.cookies[key] = str(value)
        return self

    def with_meta(self, key: str, value: Any) -> RequestBuilder:
        self.meta[key] = str(value)
        return self

    def with_header(self, key: str, value: str) -> RequestBuilder:
        self.headers[key] = value
        return self

    def with_headers(self, headers: dict[str, str]) -> RequestBuilder:
        self.headers.update(headers)
        return self

    def with_property(self, name: str, value: Any) -> RequestBuilder:
        self.custom_properties[name] = value
        return self

    def build(self) -> HttpRequest:
        method_map = {
            "GET": self.rf.get,
            "POST": self.rf.post,
            "PUT": self.rf.put,
            "PATCH": self.rf.patch,
            "DELETE": self.rf.delete,
            "HEAD": self.rf.head,
            "OPTIONS": self.rf.options,
        }

        if self.method not in method_map:
            raise ValueError(f"Unsupported HTTP method: {self.method}")

        request = method_map[self.method](self.path, self.data, headers=self.headers)

        if self.user:
            request.user = self.user

        for key, value in self.cookies.items():
            request.COOKIES[key] = value

        for key, value in self.meta.items():
            request.META[key] = value

        for key, value in self.custom_properties.items():
            setattr(request, key, value)

        return request
