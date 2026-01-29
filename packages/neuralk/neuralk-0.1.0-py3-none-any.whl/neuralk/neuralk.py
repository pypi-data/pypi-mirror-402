"""CLI utilities for Neuralk SDK."""

import time

from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

console = Console()


def _animate_banner(color: str = "#45b69c", line_delay: float = 0.001) -> None:
    """Animate the Neuralk-AI banner character by character."""
    banner_lines = r"""
░███    ░██                                           ░██ ░██                  ░███    ░██████
░████   ░██                                           ░██ ░██                 ░██░██     ░██
░██░██  ░██  ░███████  ░██    ░██ ░██░████  ░██████   ░██ ░██    ░██         ░██  ░██    ░██
░██ ░██ ░██ ░██    ░██ ░██    ░██ ░███           ░██  ░██ ░██   ░██ ░██████ ░█████████   ░██
░██  ░██░██ ░█████████ ░██    ░██ ░██       ░███████  ░██ ░███████          ░██    ░██   ░██
░██   ░████ ░██        ░██   ░███ ░██      ░██   ░██  ░██ ░██   ░██         ░██    ░██   ░██
░██    ░███  ░███████   ░█████░██ ░██       ░█████░██ ░██ ░██    ░██        ░██    ░██ ░██████
""".strip("\n").splitlines()

    # Pad all lines to same length so centering aligns them properly
    max_len = max(len(line) for line in banner_lines)
    banner_lines = [line.ljust(max_len) for line in banner_lines]

    display_lines = [""] * len(banner_lines)
    target_lines = [" " * max_len] * len(banner_lines)  # Start with padded empty lines
    with Live(refresh_per_second=180, console=console) as live:
        for i, line in enumerate(banner_lines):
            for char in line:
                display_lines[i] += char
                # Pad current line to max_len during animation
                padded_lines = [
                    dl.ljust(max_len) if idx <= i else target_lines[idx]
                    for idx, dl in enumerate(display_lines)
                ]
                text = Text("\n".join(padded_lines), style=color, no_wrap=True, overflow="crop")
                centered = Align.center(text)
                panel = Panel(centered, border_style=color, padding=(1, 2), expand=True)
                live.update(panel)
                time.sleep(line_delay)


def get_access_token() -> None:
    """
    Display the Neuralk-AI banner and instructions to get an API key.

    This function animates the Neuralk-AI logo and provides a link
    for users to create an account and obtain their API key.
    """
    _animate_banner()

    console.print()
    console.print(
        "[bold]Welcome to Neuralk-AI![/bold]",
        justify="center",
    )
    console.print()
    console.print(
        "To use the Neuralk SDK, you need an API key.",
        justify="center",
    )
    console.print()
    console.print(
        "[bold cyan]Create your account and get your API key at:[/bold cyan]",
        justify="center",
    )
    console.print()
    console.print(
        "[bold link=https://prediction.neuralk-ai.com/register]prediction.neuralk-ai.com/register[/bold link]",
        style="#45b69c",
        justify="center",
    )
    console.print()
    console.print(
        "Once you have your API key, set it as an environment variable:",
        justify="center",
    )
    console.print()
    console.print(
        "[dim]export NEURALK_API_KEY=nk_live_your_api_key[/dim]",
        justify="center",
    )
    console.print()
    console.print(
        "Or pass it directly to the Classifier:",
        justify="center",
    )
    console.print()
    console.print(
        '[dim]from neuralk import Classifier\nclf = Classifier(api_key="nk_live_your_api_key")[/dim]',
        justify="center",
    )
    console.print()
    console.print(
        "[bold cyan]Documentation:[/bold cyan]",
        justify="center",
    )
    console.print()
    console.print(
        "[bold link=https://docs.neuralk-ai.com/docs/intro]https://docs.neuralk-ai.com/docs/intro[/bold link]",
        style="#45b69c",
        justify="center",
    )
    console.print()
