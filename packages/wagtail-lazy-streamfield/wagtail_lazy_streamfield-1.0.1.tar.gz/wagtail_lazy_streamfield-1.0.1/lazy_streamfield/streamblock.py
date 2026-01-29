from typing import Any

from wagtail.blocks import StreamBlock

from .datatypes import StreamBlockDefinition


class LazyStreamBlock(StreamBlock):
    """
    A custom StreamBlock that defers block instantiation to prevent circular imports.

    Standard Wagtail StreamBlock requires block instances at definition time:

        StreamBlock([
            ("card", CardBlock()),      # ← CardBlock must be importable here
            ("resource", ResourceBlock()),
        ])

    This causes circular import errors when blocks reference each other across apps.

    LazyStreamBlock accepts a StreamBlockDefinition with string references:

        StreamBlock(StreamBlockDefinition(
            ("card", "myapp.blocks.CardBlock"),
            ("resource", "myapp.blocks.ResourceBlock"),
        ))

    Blocks are only imported and instantiated when child_blocks is first accessed,
    which happens at runtime rather than import time.
    """

    def __init__(
        self,
        stream_block_definition: StreamBlockDefinition,
        **kwargs: Any,
    ) -> None:
        """
        Initialize with a StreamBlockDefinition containing string references.

        Args:
            stream_block_definition: Definition containing (name, path) tuples
            **kwargs: Standard StreamBlock options (label, help_text, min_num, etc.)

        Raises:
            TypeError: If stream_block_definition is not a StreamBlockDefinition

        """
        if not isinstance(stream_block_definition, StreamBlockDefinition):
            raise TypeError(
                "stream_block_definition must be a StreamBlockDefinition instance."
            )

        self._stream_block_definition = stream_block_definition
        self._blocks_instantiated = False
        self._child_blocks: dict[str, Any] = {}

        # Initialize parent with empty blocks - we'll populate lazily
        super().__init__([], **kwargs)

    @property
    def child_blocks(self) -> dict[str, Any]:
        """
        Return child blocks, instantiating them lazily on first access.

        This is the key to avoiding circular imports: blocks are only imported
        when this property is first accessed (at form render time or validation),
        not when the containing block class is defined.
        """
        if not self._blocks_instantiated:
            # Mark as instantiated BEFORE importing to prevent infinite recursion
            # if blocks reference each other
            self._blocks_instantiated = True

            # Now safe to import and instantiate blocks - this triggers the
            # actual import of block classes via StreamBlockDefinition.instantiate()
            local_blocks = self._stream_block_definition.instantiate()

            for name, block in local_blocks:
                # Wagtail requires blocks to know their name for form field generation
                # and template rendering. set_name() is called by StreamBlock normally,
                # but since we bypass the normal init path, we must call it ourselves.
                block.set_name(name)
                self._child_blocks[name] = block

        return self._child_blocks

    @child_blocks.setter
    def child_blocks(self, value: dict[str, Any]) -> None:
        """
        Allow parent class to set child_blocks during init.

        Wagtail's StreamBlock.__init__ sets self.child_blocks = {},
        so we need this setter to accept that assignment.
        """
        self._child_blocks = value
