from __future__ import annotations

import importlib
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wagtail.blocks import Block

# Django Choices type
type Choices = Iterable[tuple[str, str]]
type GroupedChoices = Iterable[tuple[str, Choices]]


@dataclass
class StreamBlockDefinition:
    """
    StreamBlocks store Wagtail block types as a list of strings, rather than their
    actual class instance. This avoids importing the classes on module initialization
    and with that avoids circular imports.

    >>> BUTTON_BLOCKS = StreamBlockDefinition(
    ...     ("btn_internal_link", "app.blocks.InternalLinkButtonBlock"),
    ...     ("btn_external_link", "app.blocks.ExternalLinkButtonBlock"),
    ... )

    This dataclass can be used directly with the LazyStreamFields below:

    >>> from lazy_streamfield.streamfield import LazyStreamField
    >>> LazyStreamField(stream_blocks=BUTTON_BLOCKS)
    """

    items: tuple[tuple[str, str], ...]

    def __init__(self, *items: tuple[str, str]) -> None:
        self.items = items

    def __or__(self, other: StreamBlockDefinition) -> StreamBlockDefinition:
        """
        Combine two StreamBlockDefinition instances using the pipe operator (|).
        Duplicate items (by name) are excluded.

        >>> block1 = StreamBlockDefinition(("a", "path.A"), ("b", "path.B"))
        >>> block2 = StreamBlockDefinition(("b", "path.B"), ("c", "path.C"))
        >>> combined = block1 | block2
        >>> combined.items
        (("a", "path.A"), ("b", "path.B"), ("c", "path.C"))
        """
        combined = dict(self.items + other.items)
        return StreamBlockDefinition(*combined.items())

    @staticmethod
    def _import_object(dotted_path: str) -> type[Block]:
        """
        Imports and returns a class or object from a given dotted path string. The
        path should include both the module and the object/class name, separated
        by a dot.

        Example:
        >>> StreamBlockDefinition._import_object("app.blocks.accordion.AccordionBlock")
        app.blocks.accordion.AccordionBlock

        """
        module_path, class_name = dotted_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    def instantiate(self, *, skip: str | None = None) -> list[tuple[str, Block]]:
        """
        Returns a list of tuples containing the block name and the block class.
        This is suitable for use with the `block_types` argument of a StreamField
        or StreamBlocks.

        >>> BUTTON_BLOCKS = StreamBlockDefinition(
        ...     ("btn_internal_link", "app.blocks.InternalLinkButtonBlock"),
        ...     ("btn_external_link", "app.blocks.ExternalLinkButtonBlock"),
        ... )
        >>> StreamBlockDefinition.instantiate()
        (("btn_internal_link", InternalLinkButtonBlock()),
         ("btn_external_link", ExternalLinkButtonBlock()))
        """
        return [
            (name, self._import_object(path)())
            for name, path in self.items
            if name != skip
        ]
