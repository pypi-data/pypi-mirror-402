import pytest

from lazy_streamfield import LazyStreamField, StreamBlockDefinition


class TestLazyStreamField:
    """Tests for LazyStreamField."""

    def test_init_with_definition(self) -> None:
        """Test initialization with StreamBlockDefinition."""
        definition = StreamBlockDefinition(
            ("text", "wagtail.blocks.TextBlock"),
        )
        field = LazyStreamField(definition, blank=True)
        assert field.blank is True

    def test_init_with_none(self) -> None:
        """Test initialization with None (migration scenario)."""
        field = LazyStreamField(None, blank=True)
        assert field.blank is True

    def test_init_with_invalid_type_raises(self) -> None:
        """Test that passing invalid type raises TypeError."""
        with pytest.raises(TypeError, match="must be a StreamBlockDefinition"):
            LazyStreamField([("text", "wagtail.blocks.TextBlock")])

    def test_form_classname_applied(self) -> None:
        """Test that form_classname is applied to stream block meta."""
        definition = StreamBlockDefinition(
            ("text", "wagtail.blocks.TextBlock"),
        )
        field = LazyStreamField(definition, form_classname="my-custom-class")
        assert field.stream_block.meta.form_classname == "my-custom-class"

    def test_deconstruct_excludes_block_types(self) -> None:
        """Test that deconstruct() excludes block-related kwargs."""
        definition = StreamBlockDefinition(
            ("text", "wagtail.blocks.TextBlock"),
        )
        field = LazyStreamField(definition, blank=True)
        _name, _path, args, kwargs = field.deconstruct()

        assert args == []
        assert "block_types" not in kwargs
        assert "block_lookup" not in kwargs
        assert "use_json_field" not in kwargs
        assert kwargs.get("blank") is True

    def test_skip_parameter(self) -> None:
        """Test that skip parameter excludes specified block."""
        definition = StreamBlockDefinition(
            ("text", "wagtail.blocks.TextBlock"),
            ("char", "wagtail.blocks.CharBlock"),
        )
        field = LazyStreamField(definition, skip="text")
        # The field should have only 'char' block
        child_blocks = field.stream_block.child_blocks
        assert "text" not in child_blocks
        assert "char" in child_blocks
