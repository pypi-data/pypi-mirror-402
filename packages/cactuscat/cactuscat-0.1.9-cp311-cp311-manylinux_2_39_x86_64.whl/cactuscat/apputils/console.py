from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)
from rich.rule import Rule
from rich.console import Console
from rich.theme import Theme
import subprocess
import sys
import os
import datetime

# Export Rule so commands can use it directly
__all__ = [
    "console",
    "log",
    "get_progress",
    "print_rule",
    "run_command_with_output",
    "Rule",
    "set_log_file",
]

# Centralized Theme Definition
custom_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "dim": "dim white",
    }
)

console = Console(theme=custom_theme)
_log_file = None


def set_log_file(path: str | None):
    """Sets the file path for logging."""
    global _log_file
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    _log_file = path


def log(
    msg: str, style: str = "info", title: str = "CactusCat", markup: bool = True
) -> None:
    """Helper to print messages with style and log to file."""
    try:
        console.print(f"[bold][{title}][/bold] ", style=style, end="")
        console.print(msg, style=style, markup=markup)
    except Exception:
        print(f"[{title}] {msg}")

    if _log_file:
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(_log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [{title}] [{style.upper()}] {msg}\n")
        except Exception:
            pass


def get_progress() -> Progress:
    """Returns a configured Progress instance for consistent look."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )


def print_rule(title: str, style: str = "bold cyan") -> None:
    console.print(Rule(f"[{style}]{title}"))


def run_command_with_output(
    cmd, env=None, cwd=None, style="dim", title=None, shell=False
):
    """Runs a command and streams output to the console."""
    try:
        if title:
            log(title, style="info")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd,
            env=env,
            bufsize=1,
            shell=shell,
        )

        for line in process.stdout:
            stripped = line.rstrip()
            if stripped:
                console.print(stripped, style=style, markup=False)
                if _log_file:
                    try:
                        with open(_log_file, "a", encoding="utf-8") as f:
                            f.write(f"  {stripped}\n")
                    except Exception:
                        pass

        process.wait()
        return process.returncode
    except Exception as e:
        console.print("Error running command:", style="error", end=" ")
        console.print(str(e), style="error", markup=False)
        return 1
