from __future__ import annotations

import html
import json
import re
from typing import Any, Self
from urllib.parse import urlparse

from django.http import HttpResponse
from django.test import SimpleTestCase
from django.utils.html import strip_tags


class HttpStatusAssertionsMixin:
    _response: HttpResponse

    def assert_ok(self) -> Self:
        assert 200 <= self._response.status_code < 300, f"Expected 2xx, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_created(self) -> Self:
        assert self._response.status_code == 201, f"Expected 201 Created, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_accepted(self) -> Self:
        assert self._response.status_code == 202, f"Expected 202 Accepted, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_no_content(self) -> Self:
        assert self._response.status_code == 204, f"Expected 204 No Content, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_redirect(self, to: str | None = None) -> Self:
        assert 300 <= self._response.status_code < 400, f"Expected redirect (3xx), got {self._response.status_code}"
        if to is not None:
            location = self._response.headers.get("Location") or self._response.get("Location")
            assert location, "Redirect location header is missing"
            expected_path = urlparse(to).path
            actual_path = urlparse(location).path
            assert actual_path.endswith(expected_path), f"Expected redirect to '{to}', got '{location}'"
        return self  # type: ignore[return-value]

    def assert_moved_permanently(self) -> Self:
        assert self._response.status_code == 301, f"Expected 301 Moved Permanently, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_found(self) -> Self:
        assert self._response.status_code == 302, f"Expected 302 Found (redirect), got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_see_other(self) -> Self:
        assert self._response.status_code == 303, f"Expected 303 See Other, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_bad_request(self) -> Self:
        assert self._response.status_code == 400, f"Expected 400 Bad Request, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_unauthorized(self) -> Self:
        assert self._response.status_code == 401, f"Expected 401 Unauthorized, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_payment_required(self) -> Self:
        assert self._response.status_code == 402, f"Expected 402 Payment Required, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_forbidden(self) -> Self:
        assert self._response.status_code == 403, f"Expected 403 Forbidden, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_not_found(self) -> Self:
        assert self._response.status_code == 404, f"Expected 404 Not Found, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_method_not_allowed(self) -> Self:
        assert self._response.status_code == 405, f"Expected 405 Method Not Allowed, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_request_timeout(self) -> Self:
        assert self._response.status_code == 408, f"Expected 408 Request Timeout, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_conflict(self) -> Self:
        assert self._response.status_code == 409, f"Expected 409 Conflict, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_gone(self) -> Self:
        assert self._response.status_code == 410, f"Expected 410 Gone, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_unprocessable(self) -> Self:
        assert self._response.status_code == 422, f"Expected 422 Unprocessable Entity, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_too_many_requests(self) -> Self:
        assert self._response.status_code == 429, f"Expected 429 Too Many Requests, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_internal_server_error(self) -> Self:
        assert self._response.status_code == 500, (
            f"Expected 500 Internal Server Error, got {self._response.status_code}"
        )
        return self  # type: ignore[return-value]

    def assert_service_unavailable(self) -> Self:
        assert self._response.status_code == 503, f"Expected 503 Service Unavailable, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_server_error(self) -> Self:
        assert 500 <= self._response.status_code < 600, f"Expected 5xx Server Error, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_client_error(self) -> Self:
        assert 400 <= self._response.status_code < 500, f"Expected 4xx Client Error, got {self._response.status_code}"
        return self  # type: ignore[return-value]

    def assert_status(self, status_code: int) -> Self:
        assert self._response.status_code == status_code, (
            f"Expected status {status_code}, got {self._response.status_code}"
        )
        return self  # type: ignore[return-value]


class HeaderAssertionsMixin:
    _response: HttpResponse

    def assert_header(self, name: str, value: str) -> Self:
        actual = self._response.headers.get(name)
        assert actual == value, f"Expected header '{name}' to be '{value}', got '{actual}'"
        return self  # type: ignore[return-value]

    def assert_header_contains(self, name: str, fragment: str) -> Self:
        actual = self._response.headers.get(name)
        assert actual is not None, f"Expected header '{name}' to exist"
        assert fragment in actual, f"Expected header '{name}' to contain '{fragment}', got '{actual}'"
        return self  # type: ignore[return-value]

    def assert_header_missing(self, name: str) -> Self:
        assert name not in self._response.headers, (
            f"Expected header '{name}' to be missing, but found: '{self._response.headers.get(name)}'"
        )
        return self  # type: ignore[return-value]

    def assert_content_type(self, expected: str) -> Self:
        actual = self._response.headers.get("Content-Type")
        assert actual == expected, f"Expected Content-Type '{expected}', got '{actual}'"
        return self  # type: ignore[return-value]


class HTMLContentAssertionsMixin:
    _response: HttpResponse

    def assert_see(self, text: str) -> Self:
        body = html.unescape(self._response.content.decode("utf-8", errors="replace"))
        body = re.sub(r"\s+", " ", body).strip()
        assert text in body, f"Expected to see '{text}', got: {body}"
        return self  # type: ignore[return-value]

    def assert_dont_see(self, text: str) -> Self:
        body = html.unescape(self._response.content.decode("utf-8", errors="replace"))
        body = re.sub(r"\s+", " ", body).strip()
        assert text not in body, f"Did not expect to see '{text}', got: {body}"
        return self  # type: ignore[return-value]

    def assert_see_text(self, text: str) -> Self:
        plain = html.unescape(strip_tags(self._response.content.decode("utf-8", errors="replace")))
        plain = re.sub(r"\s+", " ", plain).strip()
        assert text in plain, f"Expected to see plain text '{text}', got: {plain}"
        return self  # type: ignore[return-value]

    def assert_dont_see_text(self, text: str) -> Self:
        plain = html.unescape(strip_tags(self._response.content.decode("utf-8", errors="replace")))
        plain = re.sub(r"\s+", " ", plain).strip()
        assert text not in plain, f"Did not expect plain text '{text}', got: {plain}"
        return self  # type: ignore[return-value]

    def assert_see_in_order(self, texts: list[str]) -> Self:
        body = html.unescape(self._response.content.decode("utf-8", errors="replace"))
        body = re.sub(r"\s+", " ", body).strip()
        last_index = -1
        last_text = ""
        for key, text in enumerate(texts):
            index = body.find(text, last_index + 1)
            message = "" if last_text == "" else f"after '{last_text}'"
            assert index != -1, f"'{text}' ({key}) not found {message}"
            last_index = index
            last_text = texts[key]
        return self  # type: ignore[return-value]

    def assert_html_contains(self, html_fragment: str) -> Self:
        SimpleTestCase().assertInHTML(html_fragment, self._response.content.decode())
        return self  # type: ignore[return-value]


class JsonContentAssertionsMixin:
    _response: HttpResponse

    def _get_json(self) -> Any:
        try:
            return json.loads(self._response.content)
        except json.JSONDecodeError:
            raise AssertionError("Response content is not valid JSON") from None

    def _resolve_path(self, data: Any, path: str) -> Any:
        for part in path.split("."):
            if isinstance(data, dict):
                data = data.get(part)
            elif isinstance(data, list) and part.isdigit():
                data = data[int(part)]
            else:
                raise AssertionError(f"Path '{path}' not found in response JSON")
        return data

    def assert_json(self) -> Self:
        self._get_json()
        return self  # type: ignore[return-value]

    def assert_json_path(self, path: str, expected: Any) -> Self:
        data = self._get_json()
        actual = self._resolve_path(data, path)
        assert actual == expected, f"Expected '{expected}' at path '{path}', got '{actual}'"
        return self  # type: ignore[return-value]

    def assert_json_fragment(self, fragment: dict) -> Self:
        data = self._get_json()
        flat = json.dumps(data)
        for key, value in fragment.items():
            pair = f'"{key}": {json.dumps(value)}'
            assert pair in flat, f"Fragment {key}: {value} not found in response JSON"
        return self  # type: ignore[return-value]

    def assert_json_missing_fragment(self, fragment: dict) -> Self:
        data = self._get_json()
        flat = json.dumps(data)
        for key, value in fragment.items():
            pair = f'"{key}": {json.dumps(value)}'
            assert pair not in flat, f"Unexpected fragment {key}: {value} found in response JSON"
        return self  # type: ignore[return-value]

    def assert_json_count(self, expected: int, path: str | None = None) -> Self:
        data = self._get_json()
        if path:
            data = self._resolve_path(data, path)
        assert isinstance(data, list), f"Expected a list at path '{path}', got {type(data)}"
        assert len(data) == expected, f"Expected {expected} items at '{path}', got {len(data)}"
        return self  # type: ignore[return-value]

    def assert_exact_json(self, expected: Any) -> Self:
        data = self._get_json()
        assert data == expected, f"Expected exact JSON: {expected}, got: {data}"
        return self  # type: ignore[return-value]

    def assert_json_structure(self, structure: dict) -> Self:
        data = self._get_json()
        assert isinstance(data, dict), f"Expected JSON object, got {type(data).__name__}"
        for key, expected_type in structure.items():
            assert key in data, f"Key '{key}' missing from JSON response"
            if expected_type is not None:
                actual_type = type(data[key])
                assert isinstance(data[key], expected_type), (
                    f"Key '{key}' expected type {expected_type.__name__}, got {actual_type.__name__}"
                )
        return self  # type: ignore[return-value]

    def assert_json_missing_path(self, path: str) -> Self:
        data = self._get_json()
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                if part not in current:
                    return self  # type: ignore[return-value]
                current = current[part]
            elif isinstance(current, list) and part.isdigit():
                idx = int(part)
                if idx >= len(current):
                    return self  # type: ignore[return-value]
                current = current[idx]
            else:
                return self  # type: ignore[return-value]
        raise AssertionError(f"Path '{path}' should not exist but has value: {current}")

    def assert_json_is_array(self) -> Self:
        data = self._get_json()
        assert isinstance(data, list), f"Expected JSON array, got {type(data).__name__}"
        return self  # type: ignore[return-value]

    def assert_json_is_object(self) -> Self:
        data = self._get_json()
        assert isinstance(data, dict), f"Expected JSON object, got {type(data).__name__}"
        return self  # type: ignore[return-value]


class CookieAssertionsMixin:
    _response: HttpResponse

    def assert_cookie(self, name: str, value: str | None = None) -> Self:
        cookies = self._response.cookies
        assert name in cookies, f"Cookie '{name}' not found. Available cookies: {list(cookies.keys())}"
        if value is not None:
            actual = cookies[name].value
            assert actual == value, f"Cookie '{name}' expected '{value}', got '{actual}'"
        return self  # type: ignore[return-value]

    def assert_cookie_missing(self, name: str) -> Self:
        cookies = self._response.cookies
        assert name not in cookies, f"Cookie '{name}' should not exist but has value '{cookies[name].value}'"
        return self  # type: ignore[return-value]

    def assert_cookie_expired(self, name: str) -> Self:
        cookies = self._response.cookies
        assert name in cookies, f"Cookie '{name}' not found"
        cookie = cookies[name]
        max_age = cookie.get("max-age")
        is_expired = max_age == 0 or max_age == "0" or cookie.value == ""
        assert is_expired, f"Cookie '{name}' is not expired (max-age={max_age}, value='{cookie.value}')"
        return self  # type: ignore[return-value]
