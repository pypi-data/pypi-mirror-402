import pytest
from wagtail.blocks import CharBlock, TextBlock

from lazy_streamfield import LazyStreamBlock, StreamBlockDefinition


class TestLazyStreamBlock:
    """Tests for LazyStreamBlock."""

    def test_init_with_definition(self) -> None:
        """Test initialization with StreamBlockDefinition."""
        definition = StreamBlockDefinition(
            ("text", "wagtail.blocks.TextBlock"),
        )
        block = LazyStreamBlock(definition)
        assert block._blocks_instantiated is False

    def test_init_with_invalid_type_raises(self) -> None:
        """Test that passing invalid type raises TypeError."""
        with pytest.raises(TypeError, match="must be a StreamBlockDefinition"):
            LazyStreamBlock([("text", "wagtail.blocks.TextBlock")])

    def test_child_blocks_lazy_loading(self) -> None:
        """Test that child_blocks are loaded lazily."""
        definition = StreamBlockDefinition(
            ("text", "wagtail.blocks.TextBlock"),
            ("char", "wagtail.blocks.CharBlock"),
        )
        block = LazyStreamBlock(definition)

        # Before accessing child_blocks
        assert block._blocks_instantiated is False

        # Access child_blocks
        children = block.child_blocks

        # After accessing child_blocks
        assert block._blocks_instantiated is True
        assert "text" in children
        assert "char" in children
        assert isinstance(children["text"], TextBlock)
        assert isinstance(children["char"], CharBlock)

    def test_child_blocks_names_set(self) -> None:
        """Test that block names are properly set via set_name()."""
        definition = StreamBlockDefinition(
            ("my_text", "wagtail.blocks.TextBlock"),
        )
        block = LazyStreamBlock(definition)
        children = block.child_blocks

        assert children["my_text"].name == "my_text"

    def test_child_blocks_cached(self) -> None:
        """Test that child_blocks are cached after first access."""
        definition = StreamBlockDefinition(
            ("text", "wagtail.blocks.TextBlock"),
        )
        block = LazyStreamBlock(definition)

        # Access twice
        children1 = block.child_blocks
        children2 = block.child_blocks

        # Should be the same object
        assert children1 is children2

    def test_child_blocks_setter(self) -> None:
        """Test that child_blocks setter works (used by parent __init__)."""
        definition = StreamBlockDefinition(
            ("text", "wagtail.blocks.TextBlock"),
        )
        block = LazyStreamBlock(definition)

        # This mimics what StreamBlock.__init__ does
        block.child_blocks = {"custom": TextBlock()}
        assert "custom" in block._child_blocks
