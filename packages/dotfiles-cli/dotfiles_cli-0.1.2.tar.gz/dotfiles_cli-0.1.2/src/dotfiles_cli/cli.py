"""dotfiles-cli: sync and manage dotfiles across machines."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()

# default paths
DEFAULT_DOTFILES_REPO = "https://github.com/FlynnOConnell/.dotfiles.git"
DEFAULT_DOTFILES_DIR = Path.home() / "repos" / ".dotfiles"


def get_dotfiles_dir() -> Path:
    """get dotfiles directory from env or default."""
    env_path = os.environ.get("DOTFILES_DIR")
    if env_path:
        return Path(env_path)
    return DEFAULT_DOTFILES_DIR


def run_cmd(
    cmd: list[str],
    cwd: Path | None = None,
    check: bool = True,
    quiet: bool = False,
) -> subprocess.CompletedProcess:
    """run a shell command with output."""
    if not quiet:
        console.print(f"[dim]$ {' '.join(cmd)}[/dim]")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.stdout and not quiet:
        console.print(result.stdout.strip())
    if result.stderr and result.returncode != 0 and not quiet:
        console.print(f"[red]{result.stderr.strip()}[/red]")
    if check and result.returncode != 0:
        raise click.ClickException(f"command failed: {' '.join(cmd)}")
    return result


def is_windows() -> bool:
    """check if running on windows."""
    return platform.system() == "Windows"


def get_config_file() -> str:
    """get the appropriate dotbot config file."""
    if is_windows():
        return "install-windows.conf.yaml"
    return "install.conf.yaml"


@click.group(invoke_without_command=True)
@click.option("-V", "--version", is_flag=True, help="show version")
@click.pass_context
def main(ctx: click.Context, version: bool) -> None:
    """
    dotfiles-cli: sync and manage dotfiles across machines.

    \b
    usage:
      dotfiles sync      pull latest and run dotbot
      dotfiles status    show current status
      dotfiles install   clone and setup dotfiles
      dotfiles update    update submodules only
    """
    if version:
        from dotfiles_cli import __version__
        console.print(f"dotfiles-cli v{__version__}")
        ctx.exit(0)

    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


@main.command()
@click.option("--force", "-f", is_flag=True, help="force relink even if unchanged")
@click.option("--no-pull", is_flag=True, help="skip git pull")
def sync(force: bool, no_pull: bool) -> None:
    """
    sync dotfiles: pull latest changes and run dotbot.

    \b
    examples:
      dotfiles sync
      dotfiles sync --force
      dotfiles sync --no-pull
    """
    dotfiles_dir = get_dotfiles_dir()

    if not dotfiles_dir.exists():
        console.print(f"[red]dotfiles not found at {dotfiles_dir}[/red]")
        console.print("run 'dotfiles install' first")
        raise click.Abort()

    console.print(f"[bold blue]syncing dotfiles[/bold blue] from {dotfiles_dir}\n")

    # pull latest
    if not no_pull:
        console.print("[cyan]pulling latest changes...[/cyan]")
        run_cmd(["git", "pull", "--rebase"], cwd=dotfiles_dir)

    # update submodules
    console.print("\n[cyan]updating submodules...[/cyan]")
    run_cmd(["git", "submodule", "update", "--init", "--recursive"], cwd=dotfiles_dir)

    # run dotbot
    console.print("\n[cyan]running dotbot...[/cyan]")
    config_file = get_config_file()
    dotbot_cmd = [
        sys.executable,
        str(dotfiles_dir / "dotbot" / "bin" / "dotbot"),
        "-c",
        config_file,
    ]
    if force:
        dotbot_cmd.append("--force")

    run_cmd(dotbot_cmd, cwd=dotfiles_dir)

    console.print("\n[bold green]dotfiles synced successfully[/bold green]")


@main.command()
def status() -> None:
    """
    show dotfiles status: git status, submodule versions.

    \b
    examples:
      dotfiles status
    """
    dotfiles_dir = get_dotfiles_dir()

    if not dotfiles_dir.exists():
        console.print(f"[red]dotfiles not found at {dotfiles_dir}[/red]")
        console.print("run 'dotfiles install' first")
        raise click.Abort()

    console.print(f"[bold blue]dotfiles status[/bold blue] ({dotfiles_dir})\n")

    # git status
    result = run_cmd(["git", "status", "--short"], cwd=dotfiles_dir, check=False, quiet=True)
    if result.stdout.strip():
        console.print("[cyan]uncommitted changes:[/cyan]")
        console.print(result.stdout.strip())
    else:
        console.print("[green]working tree clean[/green]")

    # current branch
    result = run_cmd(["git", "branch", "--show-current"], cwd=dotfiles_dir, check=False, quiet=True)
    branch = result.stdout.strip() if result.stdout else "unknown"

    # check if up to date with remote
    run_cmd(["git", "fetch", "--quiet"], cwd=dotfiles_dir, check=False, quiet=True)
    result = run_cmd(
        ["git", "rev-list", "--count", f"{branch}..origin/{branch}"],
        cwd=dotfiles_dir,
        check=False,
        quiet=True,
    )
    behind = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0

    if behind > 0:
        console.print(f"[yellow]branch {branch} is {behind} commit(s) behind origin[/yellow]")
    else:
        console.print(f"[green]branch {branch} is up to date with origin[/green]")

    # submodule status - parse .gitmodules directly
    console.print("\n[cyan]submodules:[/cyan]")
    gitmodules = dotfiles_dir / ".gitmodules"

    table = Table(show_header=True, header_style="bold")
    table.add_column("submodule")
    table.add_column("commit")
    table.add_column("branch")
    table.add_column("status")

    if gitmodules.exists():
        # get submodule paths from .gitmodules
        result = run_cmd(
            ["git", "config", "--file", ".gitmodules", "--get-regexp", "path"],
            cwd=dotfiles_dir,
            check=False,
            quiet=True,
        )
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2:
                submodule_path = parts[1]
                submodule_dir = dotfiles_dir / submodule_path

                if submodule_dir.exists():
                    # get commit
                    commit_result = run_cmd(
                        ["git", "rev-parse", "--short", "HEAD"],
                        cwd=submodule_dir,
                        check=False,
                        quiet=True,
                    )
                    commit = commit_result.stdout.strip()[:8] if commit_result.stdout else "n/a"

                    # get branch
                    branch_result = run_cmd(
                        ["git", "branch", "--show-current"],
                        cwd=submodule_dir,
                        check=False,
                        quiet=True,
                    )
                    sub_branch = branch_result.stdout.strip() if branch_result.stdout.strip() else "detached"

                    # check for uncommitted changes
                    status_result = run_cmd(
                        ["git", "status", "--porcelain"],
                        cwd=submodule_dir,
                        check=False,
                        quiet=True,
                    )
                    if status_result.stdout.strip():
                        status_text = "[yellow]modified[/yellow]"
                    else:
                        status_text = "[green]ok[/green]"

                    table.add_row(submodule_path, commit, sub_branch, status_text)
                else:
                    table.add_row(submodule_path, "n/a", "n/a", "[red]not initialized[/red]")

    console.print(table)


@main.command()
@click.option("--repo", "-r", default=DEFAULT_DOTFILES_REPO, help="dotfiles repo url")
@click.option("--dir", "-d", "directory", default=None, help="install directory")
def install(repo: str, directory: str | None) -> None:
    """
    clone and setup dotfiles from scratch.

    \b
    examples:
      dotfiles install
      dotfiles install --repo https://github.com/user/dotfiles.git
      dotfiles install --dir ~/my-dotfiles
    """
    dotfiles_dir = Path(directory) if directory else get_dotfiles_dir()

    if dotfiles_dir.exists():
        console.print(f"[yellow]dotfiles already exist at {dotfiles_dir}[/yellow]")
        if not click.confirm("remove and reinstall?"):
            raise click.Abort()
        import shutil
        shutil.rmtree(dotfiles_dir)

    console.print(f"[bold blue]installing dotfiles[/bold blue] to {dotfiles_dir}\n")

    # clone with submodules
    console.print("[cyan]cloning repository...[/cyan]")
    dotfiles_dir.parent.mkdir(parents=True, exist_ok=True)
    run_cmd(["git", "clone", "--recursive", repo, str(dotfiles_dir)])

    # run dotbot
    console.print("\n[cyan]running dotbot...[/cyan]")
    config_file = get_config_file()
    dotbot_cmd = [
        sys.executable,
        str(dotfiles_dir / "dotbot" / "bin" / "dotbot"),
        "-c",
        config_file,
    ]
    run_cmd(dotbot_cmd, cwd=dotfiles_dir)

    console.print("\n[bold green]dotfiles installed successfully[/bold green]")
    console.print(f"\nset DOTFILES_DIR={dotfiles_dir} to use a custom location")


@main.command()
@click.option("--remote", is_flag=True, help="fetch latest from remote repos")
def update(remote: bool) -> None:
    """
    update submodules to latest commits.

    \b
    examples:
      dotfiles update
      dotfiles update --remote
    """
    dotfiles_dir = get_dotfiles_dir()

    if not dotfiles_dir.exists():
        console.print(f"[red]dotfiles not found at {dotfiles_dir}[/red]")
        raise click.Abort()

    console.print(f"[bold blue]updating submodules[/bold blue] in {dotfiles_dir}\n")

    if remote:
        console.print("[cyan]fetching latest from remotes...[/cyan]")
        run_cmd(["git", "submodule", "update", "--init", "--recursive", "--remote"], cwd=dotfiles_dir)
    else:
        run_cmd(["git", "submodule", "update", "--init", "--recursive"], cwd=dotfiles_dir)

    console.print("\n[bold green]submodules updated[/bold green]")


@main.command()
@click.argument("submodule", required=False)
def push(submodule: str | None) -> None:
    """
    commit and push changes in dotfiles or a submodule.

    \b
    examples:
      dotfiles push                    # push main dotfiles repo
      dotfiles push kickstart.nvim     # push nvim submodule first
    """
    dotfiles_dir = get_dotfiles_dir()

    if not dotfiles_dir.exists():
        console.print(f"[red]dotfiles not found at {dotfiles_dir}[/red]")
        raise click.Abort()

    if submodule:
        # push submodule first
        submodule_dir = dotfiles_dir / submodule
        if not submodule_dir.exists():
            console.print(f"[red]submodule {submodule} not found[/red]")
            raise click.Abort()

        console.print(f"[cyan]pushing submodule {submodule}...[/cyan]")

        # check for changes
        result = run_cmd(["git", "status", "--porcelain"], cwd=submodule_dir, check=False)
        if result.stdout.strip():
            console.print("[yellow]uncommitted changes in submodule[/yellow]")
            if click.confirm("commit all changes?"):
                msg = click.prompt("commit message", default="update config")
                run_cmd(["git", "add", "-A"], cwd=submodule_dir)
                run_cmd(["git", "commit", "-m", msg], cwd=submodule_dir)

        run_cmd(["git", "push"], cwd=submodule_dir)

        # update parent reference
        console.print("\n[cyan]updating parent repo reference...[/cyan]")
        run_cmd(["git", "add", submodule], cwd=dotfiles_dir)
        run_cmd(["git", "commit", "-m", f"update {submodule} submodule"], cwd=dotfiles_dir, check=False)

    # push main repo
    console.print("\n[cyan]pushing dotfiles...[/cyan]")
    run_cmd(["git", "push"], cwd=dotfiles_dir)

    console.print("\n[bold green]pushed successfully[/bold green]")


@main.command()
def edit() -> None:
    """
    open dotfiles directory in default editor.

    \b
    uses $EDITOR or falls back to:
      - nvim (if available)
      - vim
      - code (VS Code)
    """
    dotfiles_dir = get_dotfiles_dir()

    if not dotfiles_dir.exists():
        console.print(f"[red]dotfiles not found at {dotfiles_dir}[/red]")
        raise click.Abort()

    editor = os.environ.get("EDITOR")
    if not editor:
        for candidate in ["nvim", "vim", "code"]:
            if subprocess.run(["which", candidate], capture_output=True).returncode == 0:
                editor = candidate
                break
        else:
            editor = "notepad" if is_windows() else "vi"

    console.print(f"[cyan]opening {dotfiles_dir} in {editor}...[/cyan]")
    subprocess.run([editor, str(dotfiles_dir)])


if __name__ == "__main__":
    main()
