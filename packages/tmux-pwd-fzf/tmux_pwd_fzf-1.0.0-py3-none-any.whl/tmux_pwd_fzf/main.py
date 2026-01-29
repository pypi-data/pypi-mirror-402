#!/usr/bin/env python3
"""
tmux-pwd-fzf: Select a tmux window based on its name and directory using fzf.

Usage:
    tmux-pwd-fzf             # select with fzf
    tmux-pwd-fzf --list      # just list, no selection
    tmux-pwd-fzf --json      # output as JSON

Requires: tmux, fzf
"""

import subprocess
import json
import sys
import os
import argparse


def run_cmd(cmd: list[str]) -> str | None:
    """Run command and return stdout, or None on failure."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_tmux_panes() -> list[dict]:
    """Get all tmux panes with their info."""
    format_str = "#{session_name}:#{window_index}.#{pane_index}|#{window_name}|#{pane_current_path}|#{pane_active}|#{window_active}|#{session_attached}"
    
    output = run_cmd(["tmux", "list-panes", "-a", "-F", format_str])
    if not output:
        return []
    
    panes = []
    for line in output.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|")
        if len(parts) != 6:
            continue
        
        target, window_name, pwd, pane_active, window_active, session_attached = parts
        
        if pwd.startswith(os.path.expanduser("~")):
            pwd = "~" + pwd[len(os.path.expanduser("~")):]
        
        panes.append({
            "target": target,
            "window_name": window_name,
            "pwd": pwd,
            "is_active": pane_active == "1" and window_active == "1",
            "session_attached": session_attached == "1",
        })
    
    return panes


def format_pane(pane: dict, max_name_len: int = 20, max_pwd_len: int = 50) -> str:
    """Format a pane for display."""
    marker = "→ " if pane["is_active"] else "  "
    attached = "*" if pane["session_attached"] else " "
    name = pane["window_name"][:max_name_len].ljust(max_name_len)
    pwd = pane["pwd"]
    if len(pwd) > max_pwd_len:
        pwd = "..." + pwd[-(max_pwd_len - 3):]
    
    return f"{marker}{pane['target']:15} {attached} {name}  {pwd}"


def select_with_fzf(panes: list[dict]) -> dict | None:
    """Use fzf to select a pane."""
    lines = [format_pane(p) for p in panes]
    input_text = "\n".join(lines)
    
    # fzf needs TTY for its UI
    with open("/dev/tty", "w") as tty:
        result = subprocess.run(
            ["fzf", "--ansi", "--prompt=Select pane: ", "--reverse"],
            input=input_text,
            stdout=subprocess.PIPE,
            stderr=tty,
            text=True,
        )
    
    if result.returncode != 0:
        return None
    
    selected_line = result.stdout.strip()
    
    # Extract target - first non-empty field (handles "→ " prefix being stripped)
    # Target format is session:window.pane (e.g., "0:1.0")
    parts = selected_line.split()
    if not parts:
        return None
    
    # First field should be the target like "0:1.0"
    selected_target = parts[0]
    
    for pane in panes:
        if pane["target"] == selected_target:
            return pane
    
    return None


def switch_to_pane(target: str):
    """Switch to a tmux pane."""
    session = target.split(":")[0]
    
    if os.environ.get("TMUX"):
        # Inside tmux
        # Get current session
        current_session = run_cmd(["tmux", "display-message", "-p", "#{session_name}"])
        
        if current_session != session:
            # Different session - need to switch client
            run_cmd(["tmux", "switch-client", "-t", session])
        
        # Now select window and pane
        run_cmd(["tmux", "select-window", "-t", target])
        run_cmd(["tmux", "select-pane", "-t", target])
    else:
        # Outside tmux - attach to session
        run_cmd(["tmux", "select-window", "-t", target])
        run_cmd(["tmux", "select-pane", "-t", target])
        os.execvp("tmux", ["tmux", "attach-session", "-t", session])


def main():
    parser = argparse.ArgumentParser(description="Select a tmux window based on its name and directory")
    parser.add_argument("--list", "-l", action="store_true", help="Just list, don't select")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    panes = get_tmux_panes()
    
    if not panes:
        print("No tmux panes found. Is tmux running?", file=sys.stderr)
        sys.exit(1)
    
    if args.json:
        print(json.dumps(panes, indent=2))
        return
    
    if args.list:
        for pane in panes:
            print(format_pane(pane))
        return
    
    selected = select_with_fzf(panes)
    if selected:
        switch_to_pane(selected["target"])


if __name__ == "__main__":
    main()