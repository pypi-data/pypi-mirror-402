# dotfiles-cli

CLI tool to sync and manage dotfiles across machines. Works with [dotbot](https://github.com/anishathalye/dotbot).

## Installation

```bash
# with uv (recommended)
uvx dotfiles-cli

# or install globally
uv tool install dotfiles-cli

# or with pip
pip install dotfiles-cli
```

## Usage

```bash
# first time setup - clone and install dotfiles
dotfiles install

# sync: pull latest and run dotbot
dotfiles sync

# check status
dotfiles status

# update submodules only
dotfiles update
dotfiles update --remote  # fetch latest from remotes

# push changes (handles submodules)
dotfiles push                    # push main repo
dotfiles push kickstart.nvim     # push submodule first

# open in editor
dotfiles edit
```

## Configuration

By default, dotfiles-cli expects your dotfiles at `~/repos/.dotfiles`.

Override with environment variable:

```bash
export DOTFILES_DIR=~/my-dotfiles
```

## Commands

| Command | Description |
|---------|-------------|
| `install` | Clone and setup dotfiles from scratch |
| `sync` | Pull latest changes and run dotbot |
| `status` | Show git status and submodule versions |
| `update` | Update submodules |
| `push` | Commit and push changes |
| `edit` | Open dotfiles in $EDITOR |

## Platform Support

- **Windows**: Uses `install-windows.conf.yaml`
- **Linux/Mac**: Uses `install.conf.yaml`

## License

MIT
