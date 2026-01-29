# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-17

### Added
- Initial release of `wagtail-lazy-streamfield`.
- `LazyStreamField` for deferring block instantiation in Page models.
- `LazyStreamBlock` for lazy loading within nested blocks (e.g., `StructBlock`).
- `StreamBlockDefinition` helper for defining block import paths.
- Prevention of circular imports via runtime importing.
- Exclusion of block definitions from Django migrations to reduce bloat.
- Comprehensive test suite and type hints.
