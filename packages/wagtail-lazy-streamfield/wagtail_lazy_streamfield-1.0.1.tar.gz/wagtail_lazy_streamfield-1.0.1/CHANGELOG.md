# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.1] - 2026-01-19

### Fixed
- Fixed type annotations in `StreamBlockDefinition` to use `Block` instead of `BaseBlock` (which is a metaclass).

### Added
- Added `ty` type checker to CI and `runtests.sh`.
- Added pre-commit configuration with ruff, ty, and standard hooks.
- Added `[dependency-groups]` for dev tools.

### Changed
- Consolidated CI lint checks into single step using project dependencies.
- Cleaned up ruff configuration, removed unnecessary ignore rules.
- PyPI description now includes both README and CHANGELOG via `hatch-fancy-pypi-readme`.

## [1.0.0] - 2026-01-17

### Added
- Initial release of `wagtail-lazy-streamfield`.
- `LazyStreamField` for deferring block instantiation in Page models.
- `LazyStreamBlock` for lazy loading within nested blocks (e.g., `StructBlock`).
- `StreamBlockDefinition` helper for defining block import paths.
- Prevention of circular imports via runtime importing.
- Exclusion of block definitions from Django migrations to reduce bloat.
- Comprehensive test suite and type hints.
