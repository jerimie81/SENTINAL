#!/usr/bin/env python3
"""
build_sentinal.py – One-button build & install script for Sentinal
Automates:
  - venv creation
  - dependency install
  - wheel build
  - local install
  - initial SQLite index
  - smoke test
Usage:
  ./build_sentinal.py           # interactive, uses venv
  ./build_sentinal.py --user    # install --user (no venv)
  ./build_sentinal.py --rebuild # wipe old build/ dist/ and re-install
"""

import os
import sys
import shutil
import subprocess
import venv
import argparse
import sqlite3
import pathlib
import tempfile
from typing import List, Tuple


# ----------- colour helpers -----------
def colour(text: str, code: int) -> str:
    return f"\033[{code}m{text}\033[0m"


RED = 31
GREEN = 32
YELLOW = 33
BLUE = 34


def error(msg: str) -> None:
    print(colour("❌  " + msg, RED))
    sys.exit(1)


def success(msg: str) -> None:
    print(colour("✅  " + msg, GREEN))


def info(msg: str) -> None:
    print(colour("ℹ️  " + msg, BLUE))


def warn(msg: str) -> None:
    print(colour("⚠️  " + msg, YELLOW))


# ----------- util -----------
def run(cmd: List[str], cwd: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run command and return CompletedProcess; prints command."""
    info("Running: " + " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, check=check, text=True)


def yes_no(question: str) -> bool:
    """Simple yes/no prompt."""
    ans = input(colour(question + " [y/N] ", YELLOW)).strip().lower()
    return ans == "y"


# ----------- dependency checks -----------
def check_python() -> None:
    if sys.version_info < (3, 9):
        error("Python 3.9+ required")


def check_build_deps() -> None:
    needed = ["pip", "wheel", "build"]
    for tool in needed:
        try:
            run([sys.executable, "-m", tool, "--version"], check=True)
        except subprocess.CalledProcessError:
            error(f"'{tool}' not found; install via pip or your package manager")


# ----------- venv helpers -----------
VENV_DIR = pathlib.Path(".venv-sentinal")


def make_venv() -> pathlib.Path:
    """Create venv if missing; return python exec path."""
    if VENV_DIR.exists():
        if not yes_no(f"Remove old venv {VENV_DIR}?"):
            error("Aborted by user")
        shutil.rmtree(VENV_DIR)
    info("Creating virtual environment...")
    venv.create(VENV_DIR, with_pip=True)
    python = VENV_DIR / "bin" / "python"
    if not python.exists():
        python = VENV_DIR / "Scripts" / "python.exe"  # Windows
    return python


# ----------- main build logic -----------
def build_wheel(proj_dir: pathlib.Path, python: str) -> pathlib.Path:
    """Build wheel; return path to .whl file."""
    run([python, "-m", "build", "--wheel"], cwd=proj_dir)
    wheel_dir = proj_dir / "dist"
    wheels = list(wheel_dir.glob("*.whl"))
    if not wheels:
        error("No wheel produced")
    return wheels[0]


def install_wheel(wheel: pathlib.Path, python: str, user: bool) -> None:
    """Install wheel."""
    cmd = [python, "-m", "pip", "install", "--upgrade"]
    if user:
        cmd.append("--user")
    cmd.append(str(wheel))
    run(cmd)


def index_initial_dirs(python: str) -> None:
    """Index $HOME and $HOME/Downloads into SQLite."""
    info("Indexing HOME and Downloads into SQLite...")
    script = f"""
import sys
sys.path.insert(0, '.')
from sentry_admin.core import index_tree
from pathlib import Path
for p in [str(Path.home()), str(Path.home() / "Downloads")]:
    try:
        count = index_tree(p)
        print(f"[INFO] Indexed {count} entries under {p}")
    except Exception as e:
        print(f"[WARN] Index failed for {p}: {e}")
"""
    run([python, "-c", script], cwd=pathlib.Path.cwd())


def smoke_test(python: str) -> None:
    """Quick sanity check."""
    info("Running smoke test...")
    proc = run([python, "-m", "sentry_admin.cli", "health"], check=False)
    if proc.returncode == 0:
        success("Smoke test passed")
    else:
        warn("Smoke test returned non-zero (check logs above)")


def spawn_demo_terminal(python: str) -> None:
    """Offer to open a new terminal running an interactive demo."""
    if not yes_no("Launch interactive demo in a new terminal?"):
        return
    term = shutil.which("xfce4-terminal") or shutil.which("konsole") or shutil.which("xterm")
    if not term:
        warn("No supported terminal emulator found.")
        return
    demo_cmd = f"{python} -m sentry_admin.cli --ask-local 'Why is my CPU high?' && echo 'Demo finished. Press Enter to close.' && read"
    subprocess.Popen([term, "-e", f"bash -c '{demo_cmd}'"])
    info("Demo terminal launched. Return here anytime.")


# ----------- CLI ------------
def parse_args():
    parser = argparse.ArgumentParser(description="Build & install Sentinal locally")
    parser.add_argument("--user", action="store_true", help="Install with --user (no venv)")
    parser.add_argument("--rebuild", action="store_true", help="Wipe build/dist and reinstall")
    return parser.parse_args()


def main():
    args = parse_args()
    proj_dir = pathlib.Path(__file__).resolve().parent
    os.chdir(proj_dir)

    check_python()
    check_build_deps()

    if args.rebuild:
        for d in ["build", "dist", ".egg-info"]:
            if pathlib.Path(d).exists():
                if not yes_n
