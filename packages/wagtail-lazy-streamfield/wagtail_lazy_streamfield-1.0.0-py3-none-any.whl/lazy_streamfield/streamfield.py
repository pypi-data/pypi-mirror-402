from typing import Any

from wagtail.fields import StreamField as StreamField

from .datatypes import StreamBlockDefinition


class LazyStreamField(StreamField):
    """
    A custom StreamField variant that defers block instantiation to prevent circular
    import errors and optimizes Django migrations by excluding block-related data.

    Features:
        - Accepts StreamBlockDefinition with string references to block classes
        - Excludes block definitions from migrations to reduce bloat
        - Supports `form_classname` for custom admin styling

    Example:
        >>> from lazy_streamfield import StreamField
        >>> from lazy_streamfield import StreamBlockDefinition
        >>>
        >>> BLOCKS = StreamBlockDefinition(
        ...     ("text", "myapp.blocks.TextBlock"),
        ...     ("image", "myapp.blocks.ImageBlock"),
        ... )
        >>>
        >>> class MyPage(Page):
        ...     content = StreamField(BLOCKS, blank=True)
        ...
        ...     # With custom admin styling:
        ...     items = StreamField(
        ...         BLOCKS,
        ...         blank=True,
        ...         collapsed=True,
        ...         form_classname="compact-stream",
        ...     )

    The `form_classname` is applied to the StreamBlock's container in the admin,
    allowing custom CSS to target specific StreamFields. Add styles via the
    `insert_global_admin_css` hook or in `static/src/wagtail/index.css`.
    """

    def __init__(
        self,
        stream_block_definition: StreamBlockDefinition | None = None,
        *,
        skip: str | None = None,
        form_classname: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Accept a StreamBlocks instance containing string references to block classes
        instead of instantiated block_types. This defers block instantiation until
        needed, preventing circular import errors.

        Args:
            stream_block_definition: The block definition to use
            skip: Optional block name to exclude (useful for avoiding circular imports)
            form_classname: CSS class to add to the StreamBlock form in the admin
            **kwargs: Standard StreamField options

        """
        self._form_classname = form_classname

        # Migrations will not store or pass stream_block_definition, and will
        # pass None here. We don't need to process those during migrations.
        if stream_block_definition is None:
            block_types = []

        # Single StreamBlockDefinition
        elif isinstance(stream_block_definition, StreamBlockDefinition):
            block_types = stream_block_definition.instantiate(skip=skip)

        else:
            raise TypeError(
                "stream_block_definition must be a StreamBlockDefinition instance."
            )

        super().__init__(block_types, **kwargs)

        # Apply form_classname directly to the stream block's meta
        if self._form_classname:
            self.stream_block.meta.form_classname = self._form_classname

    def deconstruct(self) -> tuple:
        """
        Exclude block_types and block_lookup from serialization. This prevents Django
        from storing the complete block structure and relationships in migrations,
        which would otherwise make them excessively large and slow to generate and
        apply.

        StreamField is backed by a `JSONField`, there's no actual database schema
        impact from the block definitions. The reason Wagtail stores all blocks in
        migrations is more about Django's migration philosophy than technical necessity:

        ## Why Wagtail does this by default:

        1. Django's migration completeness principle: Django's philosophy is that
           migrations should be a complete, self-contained historical record of your
           models. If you check out an old commit and run migrations, they should work
           without needing the current codebase.

        2. Block definition changes: If you change a block's structure (add/remove
           fields, change validators, etc.), Django wants to detect that as a "change"
           and potentially generate a new migration. By storing the full block
           structure, Django can diff between states.

        3. Data migration safety: If you're writing data migrations that interact
           with StreamField content, having the block definitions frozen in the
           migration theoretically lets you safely manipulate old data structures.

        ## Why this is often overkill:

        - **No schema impact**: The JSON blob in the database doesn't care about the
          block definitions

        - **Runtime validation**: Block validation happens at runtime when
          rendering/saving, not at the database level

        - **Codebase dependency**: In practice, migrations almost always require your
        current codebase anyway (for custom fields, validators, methods, etc.)

        - **Migration bloat**: Storing complex block structures makes migrations huge
          and hard to read

        https://github.com/wagtail/wagtail/issues/4298
        https://docs.wagtail.org/en/stable/advanced_topics/customization/streamfield_blocks.html#handling-block-definitions-within-migrations
        """
        name, path, _args, kwargs = super().deconstruct()

        # Remove the expanded block_types and block_lookup from serialization
        kwargs.pop("block_types", None)
        kwargs.pop("block_lookup", None)
        kwargs.pop("use_json_field", None)  # This is set by default in __init__

        # Return empty args since blocks are reconstructed in __init__
        return name, path, [], kwargs
