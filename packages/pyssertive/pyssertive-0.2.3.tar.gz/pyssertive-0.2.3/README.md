# pyssertive

[![Build Status](https://github.com/othercodes/pyssertive/actions/workflows/test.yml/badge.svg)](https://github.com/othercodes/pyssertive/actions/workflows/test.yml)

Fluent, chainable assertions for Django tests. Inspired by Laravel's elegant testing API.

## Features

- Fluent, chainable API for readable test assertions
- HTTP status code assertions (2xx, 3xx, 4xx, 5xx)
- JSON response validation with path navigation
- HTML content assertions
- Template and context assertions
- Form and formset error assertions
- Session and cookie assertions
- Header assertions
- Streaming response and file download assertions
- Debug helpers for test development

## Requirements

- Python 3.11+
- Django 4.2+

## Installation

```bash
pip install pyssertive
```

## Usage

### Basic Example

```python
import pytest
from pyssertive.http import FluentHttpAssertClient

@pytest.fixture
def client():
    from django.test import Client
    return FluentHttpAssertClient(Client())

@pytest.mark.django_db
def test_user_api(client):
    response = client.get("/api/users/")
    
    response.assert_ok()\
        .assert_json()\
        .assert_json_path("count", 10)\
        .assert_header("Content-Type", "application/json")
```

### HTTP Status Assertions

```python
response.assert_ok()              # 2xx
response.assert_created()         # 201
response.assert_not_found()       # 404
response.assert_forbidden()       # 403
response.assert_redirect("/login/")
response.assert_status(418)       # Any status code
```

### JSON Assertions

```python
response.assert_json()\
    .assert_json_path("user.name", "John")\
    .assert_json_fragment({"status": "active"})\
    .assert_json_count(5, path="items")\
    .assert_json_structure({"id": int, "name": str})\
    .assert_json_is_array()
```

### Session and Cookie Assertions

```python
response.assert_session_has("user_id", 123)\
    .assert_session_missing("temp_token")\
    .assert_cookie("session_id")\
    .assert_cookie_missing("tracking")
```

### Template Assertions

```python
response.assert_template_used("users/list.html")\
    .assert_context_has("users")\
    .assert_context_equals("page", 1)
```

### Streaming and Download Assertions

```python
response.assert_streaming()\
    .assert_download("report.csv")\
    .assert_streaming_contains("Expected content")\
    .assert_streaming_not_contains("Sensitive data")\
    .assert_streaming_matches(r"ID:\d+")\
    .assert_streaming_line_count(exact=10)\
    .assert_streaming_line_count(min=5, max=20)\
    .assert_streaming_csv_header(["id", "name", "email"])\
    .assert_streaming_line(0, "header,row")\
    .assert_streaming_empty()
```

### Debug Helpers

```python
response.dump()           # Print full response
response.dump_json()      # Pretty print JSON
response.dump_headers()   # Print headers
response.dump_session()   # Print session data
response.dd()             # Dump and die (raises exception)
```

### Database Assertions

```python
from pyssertive.db import (
    assert_model_exists,
    assert_model_count,
    assert_num_queries,
)

assert_model_exists(User, username="john")
assert_model_count(User, 5)

with assert_num_queries(2):
    list(User.objects.all())
```

## License

Apache License 2.0
