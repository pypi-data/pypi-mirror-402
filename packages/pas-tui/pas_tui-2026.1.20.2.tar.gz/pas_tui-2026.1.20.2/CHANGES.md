# Changelog

All notable changes to the `pas-tui` library will be documented in this file.

## [2026.01.20.2] - 2026-01-20

### Added
- **`Menu` class**: A high-level declarative API for building interactive CLI loops.
    - Support for direct function callbacks.
    - Automatic `rich.Panel` header management.
    - Built-in navigation items (`add_back_item`, `add_quit_item`).
    - Automatic state management for menu items.

### Changed
- Improved `__init__.py` exports to include all core TUI primitives.

## [Earlier Versions]
- Initial internal releases as part of the PAS toolkit.
- Core primitives: `prompt_toolkit_menu`, `format_menu_choices`, `prompt_yes_no`, `copy_to_clipboard`.
