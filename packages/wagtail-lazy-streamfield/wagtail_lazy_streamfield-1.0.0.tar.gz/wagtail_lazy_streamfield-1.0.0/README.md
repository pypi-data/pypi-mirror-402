# wagtail-lazy-streamfield

[![PyPI](https://img.shields.io/pypi/v/wagtail-lazy-streamfield.svg)](https://pypi.org/project/wagtail-lazy-streamfield/)
[![License](https://img.shields.io/pypi/l/wagtail-lazy-streamfield.svg)](https://github.com/bartTC/wagtail-lazy-streamfield/blob/main/LICENSE)

A lightweight utility for Wagtail that defers `StreamField` block instantiation. It resolves circular import issues in complex block dependencies and eliminates block definitions from Django migrations to keep them clean and manageable.

## Features

- **Lazy Loading**: Defers block import and instantiation until runtime, preventing circular import errors.
- **Clean Migrations**: Excludes block definitions from migration files, reducing file size and generation time.
- **Zero Database Overhead**: Works with standard `JSONField` storage; no database schema changes required.
- **Typed**: Fully type-hinted and PEP 561 compatible.

## Installation

Install via pip:

```bash
pip install wagtail-lazy-streamfield
```

## Usage

### 1. Define Blocks

Instead of instantiating blocks directly, define them using `StreamBlockDefinition` and string paths. This decouples your models from your block implementations.

```python
# blocks.py
from lazy_streamfield import StreamBlockDefinition

# Define blocks using their python import path
BASE_BLOCKS = StreamBlockDefinition(
    ("text", "myapp.blocks.TextBlock"),
    ("image", "myapp.blocks.ImageBlock"),
)

# You can combine definitions using the | operator
MEDIA_BLOCKS = StreamBlockDefinition(
    ("video", "myapp.blocks.VideoBlock"),
)

ALL_BLOCKS = BASE_BLOCKS | MEDIA_BLOCKS
```

### 2. Use `LazyStreamField` in Models

Replace standard `StreamField` with `LazyStreamField`.

```python
# models.py
from wagtail.models import Page
from lazy_streamfield import LazyStreamField
from .blocks import ALL_BLOCKS

class BlogPage(Page):
    content = LazyStreamField(ALL_BLOCKS, blank=True)
```

### 3. Use `LazyStreamBlock` for Nesting

If you need lazy loading inside a `StructBlock` (e.g., to prevent recursion or just to tidy up), use `LazyStreamBlock`.

```python
# blocks.py
from wagtail.blocks import StructBlock
from lazy_streamfield import LazyStreamBlock, StreamBlockDefinition

# This references the block below, which would normally cause a circular import
NESTED_BLOCKS = StreamBlockDefinition(
    ("card", "myapp.blocks.CardBlock"),
)

class CardBlock(StructBlock):
    # ... fields ...
    # Use LazyStreamBlock for nested stream content
    content = LazyStreamBlock(NESTED_BLOCKS)
```

## Rationale

### The Circular Import Problem

In large Wagtail projects, blocks often become interdependent. For example, a `PageBlock` might import a `Page` model, which has a `StreamField` that uses `PageBlock`. This cycle causes `ImportError` at startup.

**Standard Wagtail:**

```python
# Fails if CardBlock imports this file
from .blocks import CardBlock

class MyPage(Page):
    body = StreamField([
        ('card', CardBlock()),  # Instantation requires immediate import
    ])
```

**With LazyStreamField:**

```python
# Safe: "myapp.blocks.CardBlock" is just a string at module level
body = LazyStreamField(BLOCKS)
```

### The Migration Bloat Problem

Wagtail freezes the entire `StreamField` block structure into Django migration files. For complex sites, a single migration can easily exceed 10,000 lines of code. This makes migrations slow to generate, hard to review, and prone to conflicts.

`LazyStreamField` strips block definitions from the migration serialization, resulting in concise migrations:

```python
# migrations/0001_initial.py
operations = [
    migrations.AddField(
        model_name='blogpage',
        name='content',
        field=lazy_streamfield.streamfield.LazyStreamField(blank=True, null=True),
    ),
]
```
