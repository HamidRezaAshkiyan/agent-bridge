"""Zero-dependency interactive terminal UI helpers (ANSI + raw-key menus with fallback)."""

from __future__ import annotations

import getpass
import os
import shutil
import sys
from typing import Iterable, Sequence

# Detect ANSI color support
NO_COLOR = os.environ.get("NO_COLOR") is not None or not sys.stdout.isatty()


class C:
    """ANSI color palette."""

    RESET = "" if NO_COLOR else "\033[0m"
    BOLD = "" if NO_COLOR else "\033[1m"
    DIM = "" if NO_COLOR else "\033[2m"
    ITALIC = "" if NO_COLOR else "\033[3m"
    CYAN = "" if NO_COLOR else "\033[38;5;81m"
    BLUE = "" if NO_COLOR else "\033[38;5;75m"
    PURPLE = "" if NO_COLOR else "\033[38;5;141m"
    GREEN = "" if NO_COLOR else "\033[38;5;114m"
    YELLOW = "" if NO_COLOR else "\033[38;5;221m"
    RED = "" if NO_COLOR else "\033[38;5;203m"
    GRAY = "" if NO_COLOR else "\033[38;5;245m"
    WHITE = "" if NO_COLOR else "\033[97m"
    BG_SELECT = "" if NO_COLOR else "\033[48;5;236m"


def is_interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def term_width() -> int:
    try:
        return max(60, min(100, shutil.get_terminal_size((88, 24)).columns))
    except Exception:
        return 88


def print_banner(title: str, subtitle: str = "") -> None:
    width = min(76, term_width())
    line = "─" * (width - 2)
    print()
    print(f"{C.CYAN}╭{line}╮{C.RESET}")
    pad_title = f"  ⚡ {title}"
    print(f"{C.CYAN}│{C.RESET}{C.BOLD}{C.WHITE}{pad_title:<{width - 3}}{C.RESET}{C.CYAN}│{C.RESET}")
    if subtitle:
        pad_sub = f"  {subtitle}"
        print(f"{C.CYAN}│{C.RESET}{C.GRAY}{pad_sub:<{width - 2}}{C.RESET}{C.CYAN}│{C.RESET}")
    print(f"{C.CYAN}╰{line}╯{C.RESET}")
    print()


def section(title: str) -> None:
    print(f"\n{C.BOLD}{C.PURPLE}▸ {title}{C.RESET}")
    print(f"{C.DIM}{'─' * min(64, term_width())}{C.RESET}")


def info(msg: str) -> None:
    print(f"  {C.CYAN}ℹ{C.RESET}  {msg}")


def success(msg: str) -> None:
    print(f"  {C.GREEN}✓{C.RESET}  {msg}")


def warn(msg: str) -> None:
    print(f"  {C.YELLOW}⚠{C.RESET}  {msg}")


def error(msg: str) -> None:
    print(f"  {C.RED}✗{C.RESET}  {msg}", file=sys.stderr)


def step(num: int, total: int, title: str) -> None:
    print(f"\n{C.BOLD}{C.CYAN}[{num}/{total}]{C.RESET} {C.BOLD}{C.WHITE}{title}{C.RESET}")


def mask_secret(secret: str) -> str:
    if not secret:
        return "(empty)"
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}{'•' * min(12, len(secret) - 8)}{secret[-4:]}"


def _read_key() -> str:
    """Read a single keypress from stdin (supports arrow keys, space, enter, q)."""
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            seq = sys.stdin.read(2)
            if seq == "[A":
                return "UP"
            if seq == "[B":
                return "DOWN"
            if seq == "[C":
                return "RIGHT"
            if seq == "[D":
                return "LEFT"
            return "ESC"
        if ch in ("\r", "\n"):
            return "ENTER"
        if ch == " ":
            return "SPACE"
        if ch == "\x03":
            raise KeyboardInterrupt
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def select_one(
    prompt: str,
    items: Sequence[tuple[str, str, str]],
    default_index: int = 0,
) -> str:
    """Interactive single-select menu.

    items: sequence of (key, label, description).
    Returns the chosen key.
    """
    if not items:
        raise ValueError("select_one requires at least one item")

    if not is_interactive():
        return _select_one_fallback(prompt, items, default_index)

    try:
        import termios  # noqa: F401
    except ImportError:
        return _select_one_fallback(prompt, items, default_index)

    idx = max(0, min(default_index, len(items) - 1))
    print(f"\n{C.BOLD}{C.WHITE}{prompt}{C.RESET}")
    print(f"{C.GRAY}  Use ↑/↓ (or j/k) to move, Enter to select, q to cancel{C.RESET}\n")

    lines_drawn = 0

    def render() -> int:
        nonlocal lines_drawn
        if lines_drawn > 0:
            sys.stdout.write(f"\033[{lines_drawn}A")
        count = 0
        for i, (_key, label, desc) in enumerate(items):
            sys.stdout.write("\033[2K")
            if i == idx:
                line = f"  {C.BG_SELECT}{C.CYAN}❯ {C.BOLD}{C.WHITE}{label}{C.RESET}"
                if desc:
                    line += f"{C.BG_SELECT}  {C.GRAY}{desc}{C.RESET}"
            else:
                line = f"    {label}"
                if desc:
                    line += f"  {C.DIM}{desc}{C.RESET}"
            sys.stdout.write(line + "\n")
            count += 1
        sys.stdout.flush()
        lines_drawn = count
        return count

    render()
    while True:
        key = _read_key()
        if key in ("UP", "k"):
            idx = (idx - 1) % len(items)
            render()
        elif key in ("DOWN", "j"):
            idx = (idx + 1) % len(items)
            render()
        elif key == "ENTER":
            chosen_key, chosen_label, _ = items[idx]
            print(f"\n  {C.GREEN}✓{C.RESET} Selected: {C.BOLD}{chosen_label}{C.RESET}")
            return chosen_key
        elif key in ("q", "ESC"):
            raise KeyboardInterrupt


def _select_one_fallback(
    prompt: str,
    items: Sequence[tuple[str, str, str]],
    default_index: int = 0,
) -> str:
    print(f"\n{C.BOLD}{prompt}{C.RESET}")
    for i, (_key, label, desc) in enumerate(items, 1):
        marker = "*" if (i - 1) == default_index else " "
        desc_part = f" — {desc}" if desc else ""
        print(f"  {marker} [{i}] {label}{desc_part}")
    while True:
        raw = input(f"Enter number [1-{len(items)}] (default {default_index + 1}): ").strip()
        if not raw:
            return items[default_index][0]
        if raw.isdigit() and 1 <= int(raw) <= len(items):
            return items[int(raw) - 1][0]
        warn(f"Please enter a number between 1 and {len(items)}.")


def select_many(
    prompt: str,
    items: Sequence[tuple[str, str, str]],
    preselected: Iterable[str] = (),
) -> list[str]:
    """Interactive multi-select checkbox menu.

    items: sequence of (key, label, description).
    Returns list of selected keys in original order.
    """
    if not items:
        return []

    selected: set[str] = set(preselected)

    if not is_interactive():
        return _select_many_fallback(prompt, items, selected)

    try:
        import termios  # noqa: F401
    except ImportError:
        return _select_many_fallback(prompt, items, selected)

    idx = 0
    print(f"\n{C.BOLD}{C.WHITE}{prompt}{C.RESET}")
    print(
        f"{C.GRAY}  ↑/↓ move • Space toggle • a toggle all • Enter confirm • q cancel{C.RESET}\n"
    )

    lines_drawn = 0

    def render() -> None:
        nonlocal lines_drawn
        if lines_drawn > 0:
            sys.stdout.write(f"\033[{lines_drawn}A")
        count = 0
        for i, (key, label, desc) in enumerate(items):
            sys.stdout.write("\033[2K")
            checked = key in selected
            box = f"{C.GREEN}◉{C.RESET}" if checked else f"{C.GRAY}◯{C.RESET}"
            if i == idx:
                line = f"  {C.BG_SELECT}{C.CYAN}❯{C.RESET}{C.BG_SELECT} {box} {C.BOLD}{C.WHITE}{label}{C.RESET}"
                if desc:
                    line += f"{C.BG_SELECT}  {C.GRAY}{desc}{C.RESET}"
            else:
                line = f"    {box} {label}"
                if desc:
                    line += f"  {C.DIM}{desc}{C.RESET}"
            sys.stdout.write(line + "\n")
            count += 1
        sys.stdout.write("\033[2K")
        sys.stdout.write(f"\n  {C.DIM}Selected: {len(selected)}/{len(items)}{C.RESET}\n")
        count += 2
        sys.stdout.flush()
        lines_drawn = count

    render()
    while True:
        key = _read_key()
        if key in ("UP", "k"):
            idx = (idx - 1) % len(items)
            render()
        elif key in ("DOWN", "j"):
            idx = (idx + 1) % len(items)
            render()
        elif key == "SPACE":
            item_key = items[idx][0]
            if item_key in selected:
                selected.remove(item_key)
            else:
                selected.add(item_key)
            render()
        elif key == "a":
            if len(selected) == len(items):
                selected.clear()
            else:
                selected = {k for k, _, _ in items}
            render()
        elif key == "ENTER":
            chosen = [k for k, _, _ in items if k in selected]
            if not chosen:
                warn("Select at least one item (press Space to toggle).")
                lines_drawn = 0
                render()
                continue
            return chosen
        elif key in ("q", "ESC"):
            raise KeyboardInterrupt


def _select_many_fallback(
    prompt: str,
    items: Sequence[tuple[str, str, str]],
    preselected: set[str],
) -> list[str]:
    print(f"\n{C.BOLD}{prompt}{C.RESET}")
    for i, (key, label, desc) in enumerate(items, 1):
        mark = "x" if key in preselected else " "
        desc_part = f" — {desc}" if desc else ""
        print(f"  [{i:2d}] [{mark}] {label}{desc_part}")
    raw = input("Enter comma-separated numbers (or 'all'): ").strip()
    if raw.lower() == "all":
        return [k for k, _, _ in items]
    if not raw and preselected:
        return [k for k, _, _ in items if k in preselected]
    chosen: list[str] = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit() and 1 <= int(part) <= len(items):
            key = items[int(part) - 1][0]
            if key not in chosen:
                chosen.append(key)
    return chosen


def prompt_text(label: str, default: str = "", required: bool = False) -> str:
    suffix = f" {C.GRAY}[{default}]{C.RESET}" if default else ""
    while True:
        val = input(f"  {C.CYAN}?{C.RESET} {label}{suffix}: ").strip()
        if not val and default:
            return default
        if val or not required:
            return val
        warn("This field is required.")


def prompt_secret(label: str, default: str = "", allow_empty: bool = False) -> str:
    hint = f" {C.GRAY}[press Enter to keep {mask_secret(default)}]{C.RESET}" if default else ""
    while True:
        if is_interactive():
            val = getpass.getpass(f"  {C.CYAN}?{C.RESET} {label}{hint}: ").strip()
        else:
            val = input(f"  {C.CYAN}?{C.RESET} {label}{hint}: ").strip()
        if not val and default:
            return default
        if val or allow_empty:
            return val
        warn("API key cannot be empty (or pass --allow-empty-key for local models).")


def confirm(label: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    raw = input(f"  {C.CYAN}?{C.RESET} {label} {C.GRAY}[{hint}]{C.RESET}: ").strip().lower()
    if not raw:
        return default
    return raw in ("y", "yes")
