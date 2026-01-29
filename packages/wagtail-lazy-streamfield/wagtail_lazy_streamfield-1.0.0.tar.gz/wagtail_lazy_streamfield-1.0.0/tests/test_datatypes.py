import pytest
from wagtail.blocks import CharBlock, TextBlock

from lazy_streamfield import StreamBlockDefinition


class TestStreamBlockDefinition:
    """Tests for StreamBlockDefinition."""

    def test_init_with_items(self) -> None:
        """Test initialization with block items."""
        definition = StreamBlockDefinition(
            ("text", "wagtail.blocks.TextBlock"),
            ("char", "wagtail.blocks.CharBlock"),
        )
        assert len(definition.items) == 2
        assert definition.items[0] == ("text", "wagtail.blocks.TextBlock")
        assert definition.items[1] == ("char", "wagtail.blocks.CharBlock")

    def test_init_empty(self) -> None:
        """Test initialization with no items."""
        definition = StreamBlockDefinition()
        assert definition.items == ()

    def test_or_operator_combines_definitions(self) -> None:
        """Test that | operator combines two definitions."""
        def1 = StreamBlockDefinition(
            ("a", "wagtail.blocks.CharBlock"),
            ("b", "wagtail.blocks.TextBlock"),
        )
        def2 = StreamBlockDefinition(
            ("c", "wagtail.blocks.RichTextBlock"),
        )
        combined = def1 | def2
        assert len(combined.items) == 3

    def test_or_operator_deduplicates_by_name(self) -> None:
        """Test that | operator removes duplicates by name."""
        def1 = StreamBlockDefinition(
            ("text", "wagtail.blocks.CharBlock"),
        )
        def2 = StreamBlockDefinition(
            ("text", "wagtail.blocks.TextBlock"),  # Same name, different path
        )
        combined = def1 | def2
        # Should only have one 'text' entry (last one wins due to dict behavior)
        assert len(combined.items) == 1

    def test_instantiate_returns_block_instances(self) -> None:
        """Test that instantiate() returns actual block instances."""
        definition = StreamBlockDefinition(
            ("text", "wagtail.blocks.TextBlock"),
            ("char", "wagtail.blocks.CharBlock"),
        )
        blocks = definition.instantiate()
        assert len(blocks) == 2
        assert blocks[0][0] == "text"
        assert isinstance(blocks[0][1], TextBlock)
        assert blocks[1][0] == "char"
        assert isinstance(blocks[1][1], CharBlock)

    def test_instantiate_with_skip(self) -> None:
        """Test that instantiate() skips specified block."""
        definition = StreamBlockDefinition(
            ("text", "wagtail.blocks.TextBlock"),
            ("char", "wagtail.blocks.CharBlock"),
        )
        blocks = definition.instantiate(skip="text")
        assert len(blocks) == 1
        assert blocks[0][0] == "char"

    def test_instantiate_skip_nonexistent(self) -> None:
        """Test that skip with nonexistent name doesn't error."""
        definition = StreamBlockDefinition(
            ("text", "wagtail.blocks.TextBlock"),
        )
        blocks = definition.instantiate(skip="nonexistent")
        assert len(blocks) == 1

    def test_import_invalid_path_raises(self) -> None:
        """Test that invalid import path raises ImportError."""
        definition = StreamBlockDefinition(
            ("bad", "nonexistent.module.Block"),
        )
        with pytest.raises(ModuleNotFoundError):
            definition.instantiate()

    def test_import_invalid_class_raises(self) -> None:
        """Test that invalid class name raises AttributeError."""
        definition = StreamBlockDefinition(
            ("bad", "wagtail.blocks.NonexistentBlock"),
        )
        with pytest.raises(AttributeError):
            definition.instantiate()
