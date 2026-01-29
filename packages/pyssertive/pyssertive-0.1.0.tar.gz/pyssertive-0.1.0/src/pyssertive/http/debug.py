from __future__ import annotations

import json
import pprint
from json import JSONDecodeError
from typing import Self

from django.http import HttpResponse


class DebugResponseMixin:
    _response: HttpResponse

    def dump(self, content_format: str | None = None) -> Self:
        content_type = content_format or self._response.headers.get("Content-Type", "")

        print("\n[Response Dump - format:", content_type, "]")
        print("[Status]", self._response.status_code)
        print("[Headers]", dict(self._response.headers))

        match content_type:
            case "application/json":
                try:
                    pprint.pprint(json.loads(self._response.content))
                except JSONDecodeError:
                    print("[Invalid JSON]", self._response.content.decode(errors="replace"))
            case "text/plain":
                print(self._response.content.decode(errors="replace"))
            case _:
                print(repr(self._response.content))

        return self  # type: ignore[return-value]

    def dump_headers(self) -> Self:
        print("\n[Response Headers]")
        for key, value in self._response.headers.items():
            print(f"  {key}: {value}")
        return self  # type: ignore[return-value]

    def dump_json(self) -> Self:
        print("\n[Response JSON]")
        try:
            data = json.loads(self._response.content)
            print(json.dumps(data, indent=2, default=str))
        except JSONDecodeError:
            raise AssertionError("Response content is not valid JSON") from None
        return self  # type: ignore[return-value]

    def dump_session(self) -> Self:
        print("\n[Session Data]")
        if not hasattr(self._response, "wsgi_request"):
            print("  (no request context available)")
            return self  # type: ignore[return-value]
        session = dict(self._response.wsgi_request.session)
        if session:
            for key, value in session.items():
                print(f"  {key}: {value!r}")
        else:
            print("  (empty)")
        return self  # type: ignore[return-value]

    def dump_cookies(self) -> Self:
        print("\n[Response Cookies]")
        cookies = self._response.cookies
        if cookies:
            for name, cookie in cookies.items():
                print(f"  {name}: {cookie.value}")
                if cookie.get("max-age"):
                    print(f"    max-age: {cookie['max-age']}")
                if cookie.get("path"):  # pragma: no branch
                    print(f"    path: {cookie['path']}")
        else:
            print("  (none)")
        return self  # type: ignore[return-value]

    def dd(self) -> None:
        self.dump()
        raise RuntimeError("dd() called - stopping execution")
