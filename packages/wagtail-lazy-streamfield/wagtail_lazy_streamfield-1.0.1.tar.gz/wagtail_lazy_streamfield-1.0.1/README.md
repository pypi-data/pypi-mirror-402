# wagtail-lazy-streamfield

[![PyPI](https://img.shields.io/pypi/v/wagtail-lazy-streamfield.svg)](https://pypi.org/project/wagtail-lazy-streamfield/)
[![License](https://img.shields.io/pypi/l/wagtail-lazy-streamfield.svg)](https://github.com/bartTC/wagtail-lazy-streamfield/blob/main/LICENSE)

This module provides a lazy-loading StreamField for Wagtail. Resolves circular import issues between blocks and models, and keeps migrations free of block structure bloat.

## The Circular Import Problem

In Wagtail projects, blocks often become interdependent. A `CardBlock` might reference a page model that has a `StreamField` using `CardBlock`. This causes `ImportError` at startup:

```python
# Fails if CardBlock imports this file
from .blocks import CardBlock

class MyPage(Page):
    body = StreamField([
        ('card', CardBlock()),  # Instantiation requires immediate import
    ])
```

With `LazyStreamField`, block paths are strings. Resolution happens at runtime, not import time:

```python
class MyPage(Page):
    body = LazyStreamField(StreamBlockDefinition(
        ('card', 'myapp.blocks.CardBlock'),
    ))
```

## The Migration Bloat Problem

Wagtail freezes the entire `StreamField` block structure into migration files. Complex sites can have migrations exceeding 10,000 lines. This makes migrations slow to generate, hard to review, and prone to merge conflicts.

`LazyStreamField` excludes block definitions from migration serialization:

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

## Installation

```bash
pip install wagtail-lazy-streamfield
```

## Usage

### Define Blocks

Use `StreamBlockDefinition` with string paths instead of instantiating blocks directly:

```python
# blocks.py
from lazy_streamfield import StreamBlockDefinition

BASE_BLOCKS = StreamBlockDefinition(
    ("text", "myapp.blocks.TextBlock"),
    ("image", "myapp.blocks.ImageBlock"),
)

# Combine definitions with |
MEDIA_BLOCKS = StreamBlockDefinition(
    ("video", "myapp.blocks.VideoBlock"),
)

ALL_BLOCKS = BASE_BLOCKS | MEDIA_BLOCKS
```

### Use in Models

Replace `StreamField` with `LazyStreamField`:

```python
# models.py
from wagtail.models import Page
from lazy_streamfield import LazyStreamField
from .blocks import ALL_BLOCKS

class BlogPage(Page):
    content = LazyStreamField(ALL_BLOCKS, blank=True)
```

### Nested Blocks

Use `LazyStreamBlock` inside a `StructBlock` to prevent recursion or break import cycles:

```python
# blocks.py
from wagtail.blocks import StructBlock
from lazy_streamfield import LazyStreamBlock, StreamBlockDefinition

NESTED_BLOCKS = StreamBlockDefinition(
    ("card", "myapp.blocks.CardBlock"),
)

class CardBlock(StructBlock):
    content = LazyStreamBlock(NESTED_BLOCKS)
```
