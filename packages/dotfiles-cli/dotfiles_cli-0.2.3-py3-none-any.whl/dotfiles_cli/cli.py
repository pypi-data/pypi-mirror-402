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
DEFAULT_NOTES_REPO = "https://github.com/FlynnOConnell/docs.git"
DEFAULT_NOTES_DIR = Path.home() / "repos" / "docs"


def get_dotfiles_dir() -> Path:
    """get dotfiles directory from env or default."""
    env_path = os.environ.get("DOTFILES_DIR")
    if env_path:
        return Path(env_path)
    return DEFAULT_DOTFILES_DIR


def get_notes_dir() -> Path:
    """get notes directory from env or default."""
    env_path = os.environ.get("NOTES_DIR")
    if env_path:
        return Path(env_path)
    return DEFAULT_NOTES_DIR


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


# =============================================================================
# NOTES COMMANDS
# =============================================================================


@click.group("notes")
def notes_cli() -> None:
    """
    sync notes/docs repository across machines.

    \b
    uses GitHub as source of truth.
    set NOTES_DIR env var to customize location (default: ~/repos/docs)
    """
    pass


@notes_cli.command("status")
def notes_status() -> None:
    """show notes repository status."""
    notes_dir = get_notes_dir()

    if not notes_dir.exists():
        console.print(f"[red]notes not found at {notes_dir}[/red]")
        console.print("run 'dotfiles notes clone' first")
        raise click.Abort()

    console.print(f"[bold blue]notes status[/bold blue] ({notes_dir})\n")

    # git status
    result = run_cmd(["git", "status", "--short"], cwd=notes_dir, check=False, quiet=True)
    if result.stdout.strip():
        console.print("[cyan]local changes:[/cyan]")
        for line in result.stdout.strip().split("\n")[:20]:
            console.print(f"  {line}")
        total = len(result.stdout.strip().split("\n"))
        if total > 20:
            console.print(f"  ... and {total - 20} more")
    else:
        console.print("[green]working tree clean[/green]")

    # branch info
    result = run_cmd(["git", "branch", "--show-current"], cwd=notes_dir, check=False, quiet=True)
    branch = result.stdout.strip() if result.stdout else "unknown"

    # check remote status
    run_cmd(["git", "fetch", "--quiet"], cwd=notes_dir, check=False, quiet=True)

    # commits behind
    result = run_cmd(
        ["git", "rev-list", "--count", f"{branch}..origin/{branch}"],
        cwd=notes_dir,
        check=False,
        quiet=True,
    )
    behind = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0

    # commits ahead
    result = run_cmd(
        ["git", "rev-list", "--count", f"origin/{branch}..{branch}"],
        cwd=notes_dir,
        check=False,
        quiet=True,
    )
    ahead = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0

    if behind > 0 and ahead > 0:
        console.print(f"[yellow]branch {branch}: {ahead} ahead, {behind} behind origin[/yellow]")
    elif behind > 0:
        console.print(f"[yellow]branch {branch}: {behind} commit(s) behind origin[/yellow]")
    elif ahead > 0:
        console.print(f"[cyan]branch {branch}: {ahead} commit(s) ahead of origin[/cyan]")
    else:
        console.print(f"[green]branch {branch} is up to date with origin[/green]")


@notes_cli.command("pull")
@click.option("--hard", is_flag=True, help="hard reset to origin (discards local changes)")
def notes_pull(hard: bool) -> None:
    """
    pull latest notes from GitHub.

    \b
    examples:
      dotfiles notes pull          # merge remote changes
      dotfiles notes pull --hard   # reset to origin (discard local)
    """
    notes_dir = get_notes_dir()

    if not notes_dir.exists():
        console.print(f"[red]notes not found at {notes_dir}[/red]")
        raise click.Abort()

    console.print(f"[bold blue]pulling notes[/bold blue] from {notes_dir}\n")

    if hard:
        console.print("[yellow]hard reset: discarding local changes...[/yellow]")
        run_cmd(["git", "fetch", "origin"], cwd=notes_dir)
        result = run_cmd(["git", "branch", "--show-current"], cwd=notes_dir, check=False, quiet=True)
        branch = result.stdout.strip() if result.stdout else "master"
        run_cmd(["git", "reset", "--hard", f"origin/{branch}"], cwd=notes_dir)
        # clean untracked files too
        run_cmd(["git", "clean", "-fd"], cwd=notes_dir)
        console.print("[green]reset to origin complete[/green]")
    else:
        console.print("[cyan]pulling with rebase...[/cyan]")
        result = run_cmd(["git", "pull", "--rebase"], cwd=notes_dir, check=False)
        if result.returncode != 0:
            console.print("[red]pull failed - you may have conflicts[/red]")
            console.print("resolve conflicts manually or use --hard to reset")
            raise click.Abort()

    console.print("\n[bold green]notes pulled successfully[/bold green]")


@notes_cli.command("push")
@click.option("-m", "--message", default=None, help="commit message")
@click.option("--all", "-a", "add_all", is_flag=True, help="add all changes before committing")
def notes_push(message: str | None, add_all: bool) -> None:
    """
    commit and push notes to GitHub.

    \b
    examples:
      dotfiles notes push                    # push existing commits
      dotfiles notes push -a -m "updates"    # add all, commit, push
    """
    notes_dir = get_notes_dir()

    if not notes_dir.exists():
        console.print(f"[red]notes not found at {notes_dir}[/red]")
        raise click.Abort()

    console.print(f"[bold blue]pushing notes[/bold blue] from {notes_dir}\n")

    # check for uncommitted changes
    result = run_cmd(["git", "status", "--porcelain"], cwd=notes_dir, check=False, quiet=True)
    has_changes = bool(result.stdout.strip())

    if has_changes:
        if add_all:
            console.print("[cyan]staging all changes...[/cyan]")
            run_cmd(["git", "add", "-A"], cwd=notes_dir)

            if not message:
                message = click.prompt("commit message", default="update notes")

            run_cmd(["git", "commit", "-m", message], cwd=notes_dir)
        else:
            console.print("[yellow]uncommitted changes detected[/yellow]")
            console.print("use --all to add and commit, or commit manually first")
            raise click.Abort()

    # push
    console.print("[cyan]pushing to origin...[/cyan]")
    run_cmd(["git", "push"], cwd=notes_dir)

    console.print("\n[bold green]notes pushed successfully[/bold green]")


@notes_cli.command("sync")
@click.option("-m", "--message", default=None, help="commit message for local changes")
def notes_sync(message: str | None) -> None:
    """
    two-way sync: commit local changes, pull remote, push.

    \b
    this is the recommended way to sync notes across machines.
    GitHub is treated as the source of truth for conflicts.

    \b
    workflow:
      1. stash local uncommitted changes
      2. pull and rebase on origin
      3. apply stashed changes
      4. commit and push

    \b
    examples:
      dotfiles notes sync
      dotfiles notes sync -m "work updates"
    """
    notes_dir = get_notes_dir()

    if not notes_dir.exists():
        console.print(f"[red]notes not found at {notes_dir}[/red]")
        raise click.Abort()

    console.print(f"[bold blue]syncing notes[/bold blue] ({notes_dir})\n")

    # check for uncommitted changes
    result = run_cmd(["git", "status", "--porcelain"], cwd=notes_dir, check=False, quiet=True)
    has_uncommitted = bool(result.stdout.strip())

    # stash if needed
    if has_uncommitted:
        console.print("[cyan]stashing local changes...[/cyan]")
        run_cmd(["git", "stash", "push", "-m", "dotfiles-cli auto-stash"], cwd=notes_dir)

    # pull with rebase
    console.print("[cyan]pulling from origin...[/cyan]")
    result = run_cmd(["git", "pull", "--rebase"], cwd=notes_dir, check=False)

    if result.returncode != 0:
        console.print("[red]pull failed - conflicts detected[/red]")
        if has_uncommitted:
            console.print("[yellow]your changes are in git stash[/yellow]")
        raise click.Abort()

    # pop stash if we stashed
    if has_uncommitted:
        console.print("[cyan]restoring local changes...[/cyan]")
        result = run_cmd(["git", "stash", "pop"], cwd=notes_dir, check=False)

        if result.returncode != 0:
            console.print("[yellow]stash pop had conflicts - resolve manually[/yellow]")
            raise click.Abort()

        # commit the changes
        if not message:
            message = "sync notes"

        console.print(f"[cyan]committing: {message}[/cyan]")
        run_cmd(["git", "add", "-A"], cwd=notes_dir)
        run_cmd(["git", "commit", "-m", message], cwd=notes_dir, check=False)

    # push
    console.print("[cyan]pushing to origin...[/cyan]")
    run_cmd(["git", "push"], cwd=notes_dir)

    console.print("\n[bold green]notes synced successfully[/bold green]")


@notes_cli.command("clone")
@click.option("--repo", "-r", default=DEFAULT_NOTES_REPO, help="notes repo url")
@click.option("--dir", "-d", "directory", default=None, help="install directory")
def notes_clone(repo: str, directory: str | None) -> None:
    """
    clone notes repository.

    \b
    examples:
      dotfiles notes clone
      dotfiles notes clone --dir ~/notes
    """
    notes_dir = Path(directory) if directory else get_notes_dir()

    if notes_dir.exists():
        console.print(f"[yellow]notes already exist at {notes_dir}[/yellow]")
        raise click.Abort()

    console.print(f"[bold blue]cloning notes[/bold blue] to {notes_dir}\n")

    notes_dir.parent.mkdir(parents=True, exist_ok=True)
    run_cmd(["git", "clone", repo, str(notes_dir)])

    console.print("\n[bold green]notes cloned successfully[/bold green]")


@notes_cli.command("watch")
@click.option("--interval", "-i", default=300, help="poll interval in seconds (default: 300)")
@click.option("--once", is_flag=True, help="check once and exit (don't loop)")
@click.option("--notify", is_flag=True, help="show desktop notifications")
@click.option("--auto-commit", is_flag=True, help="auto-commit local changes before pulling")
@click.option("--auto-push", is_flag=True, help="auto-commit and push local changes (full two-way sync)")
@click.option("--on-conflict", type=click.Choice(["stash", "backup", "skip"]), default="stash",
              help="how to handle local changes: stash (default), backup to file, or skip pull")
def notes_watch(interval: int, once: bool, notify: bool, auto_commit: bool, auto_push: bool, on_conflict: str) -> None:
    """
    watch for remote changes and auto-pull.

    \b
    runs in a loop, checking GitHub for updates and pulling when behind.
    with --auto-push, also commits and pushes local changes (full two-way sync).

    \b
    conflict strategies:
      stash   - stash local changes, pull, pop stash (default)
      backup  - backup changed files to .backup/, reset to origin
      skip    - skip pull if local changes exist

    \b
    examples:
      dotfiles notes watch                    # check every 5 min, pull only
      dotfiles notes watch --auto-push        # full two-way sync
      dotfiles notes watch -i 60              # check every minute
      dotfiles notes watch --notify           # show desktop notifications
      dotfiles notes watch --on-conflict=skip # don't pull if local changes
    """
    import time
    from datetime import datetime

    notes_dir = get_notes_dir()

    if not notes_dir.exists():
        console.print(f"[red]notes not found at {notes_dir}[/red]")
        raise click.Abort()

    def send_notification(title: str, message: str) -> None:
        """send desktop notification if enabled."""
        if not notify:
            return
        try:
            if is_windows():
                # use powershell for windows toast
                ps_cmd = f'''
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                $template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
                $xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
                $xml.GetElementsByTagName("text")[0].AppendChild($xml.CreateTextNode("{title}")) | Out-Null
                $xml.GetElementsByTagName("text")[1].AppendChild($xml.CreateTextNode("{message}")) | Out-Null
                $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("dotfiles-cli").Show($toast)
                '''
                subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
            else:
                # use notify-send on linux
                subprocess.run(["notify-send", title, message], capture_output=True)
        except Exception:
            pass  # notifications are best-effort

    def get_status() -> tuple[int, int, bool]:
        """return (commits_behind, commits_ahead, has_local_changes)."""
        run_cmd(["git", "fetch", "--quiet"], cwd=notes_dir, check=False, quiet=True)

        result = run_cmd(["git", "branch", "--show-current"], cwd=notes_dir, check=False, quiet=True)
        branch = result.stdout.strip() if result.stdout else "master"

        result = run_cmd(
            ["git", "rev-list", "--count", f"{branch}..origin/{branch}"],
            cwd=notes_dir, check=False, quiet=True
        )
        behind = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0

        result = run_cmd(
            ["git", "rev-list", "--count", f"origin/{branch}..{branch}"],
            cwd=notes_dir, check=False, quiet=True
        )
        ahead = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0

        result = run_cmd(["git", "status", "--porcelain"], cwd=notes_dir, check=False, quiet=True)
        has_changes = bool(result.stdout.strip())

        return behind, ahead, has_changes

    def backup_local_changes() -> list[str]:
        """backup modified files to .backup/ directory."""
        backup_dir = notes_dir / ".backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)

        result = run_cmd(["git", "status", "--porcelain"], cwd=notes_dir, check=False, quiet=True)
        backed_up = []

        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            # status is first 2 chars, filename after
            status = line[:2]
            filepath = line[3:].strip().strip('"')

            if status.strip() in ["M", "MM", "A", "AM", "??"]:
                src = notes_dir / filepath
                if src.exists():
                    dst = backup_dir / filepath
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    import shutil
                    shutil.copy2(src, dst)
                    backed_up.append(filepath)

        return backed_up

    def do_pull() -> bool:
        """attempt to pull, return True if successful."""
        result = run_cmd(["git", "pull", "--rebase"], cwd=notes_dir, check=False, quiet=True)
        return result.returncode == 0

    def check_and_sync() -> None:
        """main check logic with optional auto-push."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # step 1: if auto_push, commit and push local changes first
        if auto_push:
            result = run_cmd(["git", "status", "--porcelain"], cwd=notes_dir, check=False, quiet=True)
            if result.stdout.strip():
                console.print(f"[dim]{timestamp}[/dim] [cyan]auto-push: committing local changes...[/cyan]")
                run_cmd(["git", "add", "-A"], cwd=notes_dir, check=False, quiet=True)

                # get hostname for commit message
                import socket
                hostname = socket.gethostname()
                commit_msg = f"auto-sync from {hostname}"

                result = run_cmd(["git", "commit", "-m", commit_msg], cwd=notes_dir, check=False, quiet=True)
                if result.returncode == 0:
                    console.print(f"[dim]{timestamp}[/dim] [cyan]auto-push: pushing...[/cyan]")
                    push_result = run_cmd(["git", "push"], cwd=notes_dir, check=False, quiet=True)
                    if push_result.returncode == 0:
                        console.print(f"[dim]{timestamp}[/dim] [green]pushed local changes[/green]")
                        send_notification("Notes Pushed", f"Auto-pushed changes from {hostname}")
                    else:
                        # push failed, probably need to pull first
                        console.print(f"[dim]{timestamp}[/dim] [yellow]push failed, will pull and retry[/yellow]")

        # step 2: check remote and pull if behind
        behind, ahead, has_changes = get_status()

        if behind == 0 and ahead == 0 and not has_changes:
            console.print(f"[dim]{timestamp}[/dim] [green]up to date[/green]")
            return

        if behind == 0 and ahead > 0:
            # we're ahead, just need to push
            if auto_push:
                console.print(f"[dim]{timestamp}[/dim] [cyan]pushing {ahead} commit(s)...[/cyan]")
                result = run_cmd(["git", "push"], cwd=notes_dir, check=False, quiet=True)
                if result.returncode == 0:
                    console.print(f"[dim]{timestamp}[/dim] [green]pushed {ahead} commit(s)[/green]")
                    send_notification("Notes Pushed", f"Pushed {ahead} commit(s)")
                else:
                    console.print(f"[dim]{timestamp}[/dim] [red]push failed[/red]")
            else:
                console.print(f"[dim]{timestamp}[/dim] [cyan]{ahead} commit(s) ahead (use --auto-push to push)[/cyan]")
            return

        if behind == 0:
            console.print(f"[dim]{timestamp}[/dim] [green]up to date[/green]")
            return

        console.print(f"[dim]{timestamp}[/dim] [yellow]{behind} commit(s) behind origin[/yellow]")

        if not has_changes:
            # clean working tree, just pull
            console.print(f"[dim]{timestamp}[/dim] [cyan]pulling...[/cyan]")
            if do_pull():
                console.print(f"[dim]{timestamp}[/dim] [green]pulled {behind} commit(s)[/green]")
                send_notification("Notes Updated", f"Pulled {behind} commit(s) from GitHub")

                # if auto_push and we have local commits, push them
                if auto_push:
                    _, new_ahead, _ = get_status()
                    if new_ahead > 0:
                        console.print(f"[dim]{timestamp}[/dim] [cyan]pushing {new_ahead} local commit(s)...[/cyan]")
                        run_cmd(["git", "push"], cwd=notes_dir, check=False, quiet=True)
            else:
                console.print(f"[dim]{timestamp}[/dim] [red]pull failed[/red]")
                send_notification("Notes Pull Failed", "Check for conflicts")
            return

        # has local changes - handle according to strategy
        console.print(f"[dim]{timestamp}[/dim] [yellow]local changes detected[/yellow]")

        if on_conflict == "skip":
            console.print(f"[dim]{timestamp}[/dim] [yellow]skipping pull (--on-conflict=skip)[/yellow]")
            return

        if on_conflict == "backup":
            console.print(f"[dim]{timestamp}[/dim] [cyan]backing up local changes...[/cyan]")
            backed_up = backup_local_changes()
            if backed_up:
                console.print(f"[dim]{timestamp}[/dim] backed up {len(backed_up)} file(s)")

            # reset to origin
            result = run_cmd(["git", "branch", "--show-current"], cwd=notes_dir, check=False, quiet=True)
            branch = result.stdout.strip() if result.stdout else "master"
            run_cmd(["git", "reset", "--hard", f"origin/{branch}"], cwd=notes_dir, quiet=True)
            run_cmd(["git", "clean", "-fd"], cwd=notes_dir, quiet=True)
            console.print(f"[dim]{timestamp}[/dim] [green]reset to origin, pulled {behind} commit(s)[/green]")
            send_notification("Notes Updated", f"Pulled {behind} commit(s), local changes backed up")
            return

        if on_conflict == "stash":
            if auto_commit or auto_push:
                console.print(f"[dim]{timestamp}[/dim] [cyan]auto-committing local changes...[/cyan]")
                run_cmd(["git", "add", "-A"], cwd=notes_dir, check=False, quiet=True)

                import socket
                hostname = socket.gethostname()
                run_cmd(["git", "commit", "-m", f"auto-sync from {hostname}"], cwd=notes_dir, check=False, quiet=True)
                has_changes = False

            if has_changes:
                console.print(f"[dim]{timestamp}[/dim] [cyan]stashing local changes...[/cyan]")
                run_cmd(["git", "stash", "push", "-m", "dotfiles-watch auto-stash"], cwd=notes_dir, quiet=True)

            console.print(f"[dim]{timestamp}[/dim] [cyan]pulling...[/cyan]")
            pull_ok = do_pull()

            if has_changes:
                console.print(f"[dim]{timestamp}[/dim] [cyan]restoring stash...[/cyan]")
                result = run_cmd(["git", "stash", "pop"], cwd=notes_dir, check=False, quiet=True)
                if result.returncode != 0:
                    console.print(f"[dim]{timestamp}[/dim] [red]stash pop conflict - resolve manually[/red]")
                    console.print(f"[dim]{timestamp}[/dim] [yellow]your changes are in: git stash list[/yellow]")
                    send_notification("Notes Conflict", "Stash pop failed - resolve manually")
                    return

            if pull_ok:
                console.print(f"[dim]{timestamp}[/dim] [green]pulled {behind} commit(s)[/green]")
                send_notification("Notes Updated", f"Pulled {behind} commit(s) from GitHub")

                # push if auto_push enabled
                if auto_push:
                    console.print(f"[dim]{timestamp}[/dim] [cyan]pushing...[/cyan]")
                    push_result = run_cmd(["git", "push"], cwd=notes_dir, check=False, quiet=True)
                    if push_result.returncode == 0:
                        console.print(f"[dim]{timestamp}[/dim] [green]pushed[/green]")
                    else:
                        console.print(f"[dim]{timestamp}[/dim] [yellow]push failed[/yellow]")
            else:
                console.print(f"[dim]{timestamp}[/dim] [red]pull failed[/red]")
                send_notification("Notes Pull Failed", "Check for conflicts")

    # main loop
    console.print(f"[bold blue]watching notes[/bold blue] ({notes_dir})")
    mode = "two-way sync" if auto_push else "pull only"
    console.print(f"interval: {interval}s | mode: {mode} | conflict: {on_conflict} | notify: {notify}")
    console.print("[dim]press Ctrl+C to stop[/dim]\n")

    try:
        while True:
            check_and_sync()
            if once:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[yellow]watch stopped[/yellow]")


# register notes subgroup
main.add_command(notes_cli)


if __name__ == "__main__":
    main()
