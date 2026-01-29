# Maler

A Python templating library for rendering dynamic HTML and MJML content in a type-safe way.

## Why Maler?

"Maler" is Norwegian for both "painters" and "templates" — fitting for a library that helps you paint your pages with reusable templates.

## Installation

```bash
uv add maler
```

Or with pip:

```bash
pip install maler
```

## Quick Start

Create your first template:

```python
from maler import div, span

my_page = div(
    "Hello ", span("World", class_="font-bold")
).render()
```

## Dynamic Content

Use the `@template` decorator for safe-dynamic content.
This will escape unsafe HTML content:

```python
from maler import div, span, template

@template
def hello_world(name: str | None = None):
    return div(
        "Hello ", span(name or "World", class_="font-bold")
    )

html = hello_world(name="<script>a_bad_script=...</script>")
```
Leading to the following:
```
<div>Hello <span class="font-bold">&lt;script&gt;a_bad_script...</span></div>
```

## FastAPI Integration

Maler integrates seamlessly with FastAPI using the `render_template` decorator:

```python
from fastapi import FastAPI
from maler import div, h1
from maler.fastapi import render_template

app = FastAPI()

def page_template(user: User):
    return div(
        h1("Welcome, ", user.name)
    )

def error_template(error: Exception):
    return div("Something went wrong!")

@app.get("/user/{user_id}")
@render_template(page_template, error_template)
async def get_user(user_id: int):
    return await fetch_user(user_id)
```

The decorator automatically returns an `HTMLResponse`. If the client sends `Accept-Encoding: application/json` will it return JSON instead.

## MJML Support

Create responsive emails using [MJML](https://mjml.io) syntax with the `@mjml_template` decorator:

```python
from maler.mjml import mjml_template
from maler.mjml_tags import mjml, mj_body, mj_section, mj_column, mj_text
from maler import Tag

@mjml_template
def welcome_email(name: str):
    return mjml(
        mj_body(
            mj_section(
                mj_column(
                    mj_text(f"Welcome, {name}!")
                )
            )
        )
    )

html = welcome_email("Alice")
```

This requires the `mrml` package for MJML-to-HTML conversion.
