"""Database assertion utilities for Django models."""

from collections.abc import Callable, Collection, Generator, Iterator
from contextlib import contextmanager
from typing import Any

from django.db import connection
from django.db.models import Model, QuerySet
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext


def assert_queryset_equal(
    actual: QuerySet | list[Any] | Iterator[Any],
    expected: Collection,
    *,
    transform: Callable[[Any], Any] = repr,
    ordered: bool = True,
) -> None:
    TransactionTestCase().assertQuerySetEqual(actual, expected, transform=transform, ordered=ordered)


@contextmanager
def assert_num_queries(expected: int) -> Generator[None, Any, None]:
    with CaptureQueriesContext(connection) as ctx:
        yield
        actual = len(ctx)
        assert actual == expected, f"Expected {expected} queries, but got {actual}.\nQueries:\n" + "\n".join(
            q["sql"] for q in ctx.captured_queries
        )


def assert_model_exists(model: type[Model], **filters) -> None:
    assert model.objects.filter(**filters).exists(), f"{model.__name__} does not exist with filters: {filters}"


def assert_model_not_exists(model: type[Model], **filters) -> None:
    assert not model.objects.filter(**filters).exists(), f"{model.__name__} unexpectedly exists with filters: {filters}"


def assert_model_count(model: type[Model], expected: int, **filters) -> None:
    actual = model.objects.filter(**filters).count()
    assert actual == expected, f"Expected {expected} records for {model.__name__}, got {actual}"


def assert_model_soft_deleted(model: type[Model], **filters) -> None:
    """Assumes model uses soft-deletion with a `deleted_at` datetime field."""
    obj = model.objects.filter(**filters).first()
    assert obj is not None, f"{model.__name__} does not exist with filters: {filters}"
    assert hasattr(obj, "deleted_at"), f"{model.__name__} has no 'deleted_at' field"
    assert obj.deleted_at is not None, f"{model.__name__} is not soft deleted"
