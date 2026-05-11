"""Cross-platform task runner.

Same target names as the Makefile. Works on macOS, Linux, and native Windows
(no make / no bash required). Used as the underlying implementation by the
Makefile too, so behaviour is identical across surfaces.

Usage:
    uv run python tasks.py <target> [args]
    python tasks.py <target> [args]

Targets:
    crawl, cluster, topics, index, validate, build, test,
    cc-install, cc-uninstall, chat-bundle, project-bundle,
    fresh, clean, help
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL_NAME = "qlik-talend"
SKILL_SRC = ROOT / "skill-output" / SKILL_NAME
DIST_DIR = ROOT / "dist"
CHAT_BUNDLE_DIR = DIST_DIR / "qlik-talend-chat"
CHAT_BUNDLE_ZIP = DIST_DIR / "qlik-talend-chat.zip"
PROJECT_BUNDLE_DIR = DIST_DIR / "qlik-talend-project"
TOPIC_MAP = ROOT / "topic_map.yaml"

IS_WINDOWS = platform.system() == "Windows"


def claude_skills_dir() -> Path:
    """Locate the user-scoped Claude Code skills directory across OSes.

    Claude Code stores user skills under `<config-home>/.claude/skills/` on
    every platform we target. On Windows that's the user's profile root
    (`%USERPROFILE%\\.claude\\skills`), which `Path.home()` resolves to.
    """
    return Path.home() / ".claude" / "skills"


def skill_dst() -> Path:
    return claude_skills_dir() / SKILL_NAME


# ---------------------------------------------------------------------------
# Command execution
# ---------------------------------------------------------------------------


def run(*cmd: str, check: bool = True) -> int:
    """Run a subprocess, streaming output to the current terminal."""
    print(f"  $ {' '.join(cmd)}")
    env = {**os.environ, "PYTHONUTF8": "1"}
    proc = subprocess.run(cmd, cwd=ROOT, check=check, env=env)
    return proc.returncode


def uv_python(*module_args: str) -> int:
    """Invoke `uv run python -m <module>`."""
    return run("uv", "run", "python", "-m", *module_args)


# ---------------------------------------------------------------------------
# Build pipeline
# ---------------------------------------------------------------------------


def cmd_crawl(_args) -> int:
    return run("uv", "run", "python", "-m", "crawler.run", "--delay", "0.5")


def cmd_cluster(_args) -> int:
    return uv_python("distill.cluster")


def cmd_topics(_args) -> int:
    return uv_python("distill.build_topics")


def cmd_index(_args) -> int:
    return uv_python("package.build_index")


def cmd_validate(_args) -> int:
    rc1 = uv_python("crawler.validate")
    rc2 = uv_python("distill.validate_citations")
    return rc1 or rc2


def cmd_build(_args) -> int:
    for step in (cmd_cluster, cmd_topics, cmd_index, cmd_validate):
        rc = step(None)
        if rc:
            return rc
    return 0


def cmd_test(_args) -> int:
    return run("uv", "run", "pytest", "-v")


# ---------------------------------------------------------------------------
# Distribution
# ---------------------------------------------------------------------------


def cmd_chat_bundle(_args) -> int:
    rc = uv_python("package.build_chat_bundle")
    if rc == 0:
        print()
        print("Upload to claude.ai:")
        print(f"  Settings -> Skills -> upload {CHAT_BUNDLE_ZIP}")
        print("  Then invoke in chat with: /qlik-talend")
    return rc


def cmd_project_bundle(_args) -> int:
    return uv_python("package.build_project_bundle")


def cmd_cc_install(_args) -> int:
    """Link the local build into the user's Claude Code skills directory.

    - macOS / Linux: symbolic link (`os.symlink`).
    - Windows: directory junction via `mklink /J`, which behaves like a
      symlink for filesystem traversal but doesn't require Developer Mode
      or admin privileges.
    """
    if not SKILL_SRC.exists():
        print(
            f"build artefact not found at {SKILL_SRC} — run `tasks.py build` first",
            file=sys.stderr,
        )
        return 1

    dst = skill_dst()
    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.exists() or dst.is_symlink():
        print(f"  removing existing {dst}")
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            # On Windows a junction reports as a directory; rmdir handles it.
            try:
                dst.rmdir()
            except OSError:
                shutil.rmtree(dst)

    if IS_WINDOWS:
        # Use directory junction — no admin rights needed.
        rc = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(dst), str(SKILL_SRC)],
            cwd=ROOT,
        ).returncode
        if rc != 0:
            print(
                "  junction creation failed; falling back to os.symlink "
                "(may require Developer Mode or admin)",
                file=sys.stderr,
            )
            os.symlink(SKILL_SRC, dst, target_is_directory=True)
    else:
        os.symlink(SKILL_SRC, dst)

    print(f"  linked {dst} -> {SKILL_SRC}")
    return 0


def cmd_cc_uninstall(_args) -> int:
    dst = skill_dst()
    if not (dst.exists() or dst.is_symlink()):
        print(f"  no skill installed at {dst}")
        return 0
    if dst.is_symlink() or dst.is_file():
        dst.unlink()
    else:
        try:
            dst.rmdir()
        except OSError:
            shutil.rmtree(dst)
    print(f"  removed {dst}")
    return 0


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


def cmd_clean(_args) -> int:
    for target in (
        SKILL_SRC / "topics",
        SKILL_SRC / "index",
        SKILL_SRC / "index.md",
        CHAT_BUNDLE_DIR,
        CHAT_BUNDLE_ZIP,
        PROJECT_BUNDLE_DIR,
    ):
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            print(f"  removed {target.relative_to(ROOT)}")
    if TOPIC_MAP.exists():
        TOPIC_MAP.unlink()
        print(f"  removed {TOPIC_MAP.relative_to(ROOT)}")
    return 0


def cmd_fresh(_args) -> int:
    # Remove generated artefacts but preserve source-controlled files (SKILL.md).
    cmd_clean(None)
    for crawl_dir in (SKILL_SRC / "raw", SKILL_SRC / "meta"):
        if crawl_dir.exists():
            shutil.rmtree(crawl_dir)
            print(f"  removed {crawl_dir.relative_to(ROOT)}")
    for step in (cmd_crawl, cmd_build, cmd_cc_install):
        rc = step(None)
        if rc:
            return rc
    return 0


def cmd_help(_args) -> int:
    print(__doc__)
    print("Detected OS:", platform.system())
    print("Skill destination:", skill_dst())
    return 0


# ---------------------------------------------------------------------------
# CLI plumbing
# ---------------------------------------------------------------------------

COMMANDS = {
    "crawl": cmd_crawl,
    "cluster": cmd_cluster,
    "topics": cmd_topics,
    "index": cmd_index,
    "validate": cmd_validate,
    "build": cmd_build,
    "test": cmd_test,
    "cc-install": cmd_cc_install,
    "cc-uninstall": cmd_cc_uninstall,
    "chat-bundle": cmd_chat_bundle,
    "project-bundle": cmd_project_bundle,
    "fresh": cmd_fresh,
    "clean": cmd_clean,
    "help": cmd_help,
}


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="tasks.py",
        description="Cross-platform task runner (mirror of the Makefile).",
    )
    parser.add_argument(
        "target",
        choices=sorted(COMMANDS),
        nargs="?",
        default="help",
    )
    args, rest = parser.parse_known_args()
    return COMMANDS[args.target](rest)


if __name__ == "__main__":
    sys.exit(main())
