from __future__ import annotations

from typing import Any, Self

from django.forms import Form
from django.forms.formsets import BaseFormSet
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.test import SimpleTestCase


class TemplateContextAssertionsMixin:
    _response: HttpResponse

    def assert_template_used(self, template_name: str) -> Self:
        SimpleTestCase().assertTemplateUsed(self._response, template_name)
        return self  # type: ignore[return-value]

    def assert_template_not_used(self, template_name: str) -> Self:
        SimpleTestCase().assertTemplateNotUsed(self._response, template_name)
        return self  # type: ignore[return-value]

    def assert_context_has(self, key: str) -> Self:
        assert hasattr(self._response, "context") and self._response.context is not None, "Response has no context"
        assert key in self._response.context, f"Expected context to contain '{key}'"
        return self  # type: ignore[return-value]

    def assert_context_equals(self, key: str, expected: object) -> Self:
        assert hasattr(self._response, "context") and self._response.context is not None, "Response has no context"
        assert key in self._response.context, f"Expected context to contain '{key}'"
        actual = self._response.context[key]
        assert actual == expected, f"Expected context['{key}'] == {expected}, got {actual}"
        return self  # type: ignore[return-value]


class FormValidationAssertionsMixin:
    _response: HttpResponse

    def assert_form_error(self, form: str, field: str, error: str | list[str]) -> Self:
        assert isinstance(self._response, TemplateResponse), "Response must be a TemplateResponse"
        assert hasattr(self._response, "context"), "Response has no context"
        assert form in self._response.context, f"'{form}' not found in response context"

        form_obj = self._response.context[form]
        assert isinstance(form_obj, Form), f"Context variable '{form}' is not a Form instance"

        SimpleTestCase().assertFormError(form_obj, field, error)
        return self  # type: ignore[return-value]

    def assert_formset_error(self, formset: str, form_index: int, field: str, error: str | list[str]) -> Self:
        assert isinstance(self._response, TemplateResponse), "Response must be a TemplateResponse"
        assert hasattr(self._response, "context"), "Response has no context"
        assert formset in self._response.context, f"'{formset}' not found in response context"

        formset_obj = self._response.context[formset]
        assert isinstance(formset_obj, BaseFormSet), f"Context variable '{formset}' is not a FormSet instance"

        SimpleTestCase().assertFormSetError(formset_obj, form_index, field, error)
        return self  # type: ignore[return-value]


class SessionAssertionsMixin:
    _response: HttpResponse

    def _get_session(self) -> dict:
        if not hasattr(self._response, "wsgi_request"):
            raise AssertionError("Response has no request context (use Client, not RequestFactory)")
        return dict(self._response.wsgi_request.session)

    def assert_session_has(self, key: str, value: Any = None) -> Self:
        session = self._get_session()
        assert key in session, f"Session key '{key}' not found. Available keys: {list(session.keys())}"
        if value is not None:
            assert session[key] == value, f"Session key '{key}' expected '{value}', got '{session[key]}'"
        return self  # type: ignore[return-value]

    def assert_session_missing(self, key: str) -> Self:
        session = self._get_session()
        assert key not in session, f"Session key '{key}' should not exist but has value '{session[key]}'"
        return self  # type: ignore[return-value]

    def assert_session_has_all(self, keys: list[str]) -> Self:
        session = self._get_session()
        missing = [k for k in keys if k not in session]
        assert not missing, f"Session missing keys: {missing}. Available keys: {list(session.keys())}"
        return self  # type: ignore[return-value]
