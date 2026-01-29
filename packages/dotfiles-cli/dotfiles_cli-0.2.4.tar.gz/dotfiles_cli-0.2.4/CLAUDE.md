# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development

```bash
# install dependencies (dev)
uv sync --dev

# run the cli locally
uv run dotfiles --help

# lint
uv run ruff check src/
uv run ruff format src/

# run tests (no tests exist yet)
uv run pytest
```

## Architecture

Single-file CLI tool (`src/dotfiles_cli/cli.py`) built with click and rich. Commands wrap git operations for managing dotfiles with dotbot.

**Key functions:**
- `get_dotfiles_dir()` - resolves dotfiles location from `DOTFILES_DIR` env or defaults to `~/repos/.dotfiles`
- `run_cmd()` - subprocess wrapper with rich output formatting
- `get_config_file()` - returns platform-specific dotbot config (windows vs linux/mac)

**Commands:** install, sync, status, update, push, edit

## Configuration

- Default dotfiles location: `~/repos/.dotfiles`
- Override via `DOTFILES_DIR` environment variable
- Platform detection chooses `install-windows.conf.yaml` vs `install.conf.yaml` for dotbot
