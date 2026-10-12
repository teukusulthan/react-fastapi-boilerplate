#!/usr/bin/env python3
"""Tear down the sandbox-level self-hosted Supabase stack.

Default: ``docker compose down`` — containers stop, volumes and bind-mounted
data preserved. Use ``--wipe`` to drop the named volumes AND the bind-mounted
PG datadir under ``volumes/db/data``. Use ``--remove-stack`` to additionally
delete the entire ``<sandbox>/.supabase/`` directory.

Usage::

    python skills/supabase-init/scripts/teardown.py
    python skills/supabase-init/scripts/teardown.py --wipe
    python skills/supabase-init/scripts/teardown.py --remove-stack
    python skills/supabase-init/scripts/teardown.py --sandbox-root /path
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_SANDBOX_ROOT = Path(__file__).resolve().parents[3]


class C:
    R = "\033[31m"
    G = "\033[32m"
    Y = "\033[33m"
    B = "\033[34m"
    OFF = "\033[0m"


def info(m: str) -> None:  print(f"{C.B}→{C.OFF} {m}", flush=True)
def ok(m: str) -> None:    print(f"{C.G}✓{C.OFF} {m}", flush=True)
def warn(m: str) -> None:  print(f"{C.Y}!{C.OFF} {m}", flush=True)
def err(m: str) -> None:   print(f"{C.R}✗{C.OFF} {m}", file=sys.stderr, flush=True)


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    info(f"$ {' '.join(cmd)}{f'   ({cwd})' if cwd else ''}")
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=check, text=True)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sandbox-root", type=Path, default=DEFAULT_SANDBOX_ROOT,
                   help=f"sandbox root (default: {DEFAULT_SANDBOX_ROOT})")
    p.add_argument("--wipe", action="store_true",
                   help="also drop named volumes and remove volumes/db/data + volumes/storage "
                        "(DESTRUCTIVE — Postgres rows + Storage objects are erased)")
    p.add_argument("--remove-stack", action="store_true",
                   help="also rm -rf the entire <sandbox>/.supabase/ directory")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    sandbox_root: Path = args.sandbox_root.resolve()
    stack_dir = sandbox_root / ".supabase"
    docker_dir = stack_dir / ".supabase".rstrip(".") if False else stack_dir / "docker"

    if not docker_dir.exists():
        warn(f"no stack found at {stack_dir} — nothing to do")
        if args.remove_stack and stack_dir.exists():
            info(f"--remove-stack: rm -rf {stack_dir}")
            shutil.rmtree(stack_dir)
            ok(f"removed {stack_dir}")
        return

    # docker compose down [-v]
    cmd = ["docker", "compose", "down"]
    if args.wipe:
        cmd.append("-v")
    try:
        run(cmd, cwd=docker_dir)
    except subprocess.CalledProcessError as e:
        err(f"docker compose down failed (exit {e.returncode}) — proceeding with file cleanup")

    if args.wipe:
        for sub in ("volumes/db/data", "volumes/storage"):
            target = docker_dir / sub
            if not target.exists():
                continue
            info(f"removing {target}")
            try:
                shutil.rmtree(target)
                ok(f"wiped {target}")
            except PermissionError:
                # Files written by the postgres container run as a different uid
                # (root inside the container) and are unreadable from the host.
                # Standard Docker idiom: use a throwaway container to do the rm.
                warn(
                    f"host-side rm denied on {target} (root-owned by container) — "
                    "falling back to a throwaway docker container"
                )
                try:
                    run(
                        [
                            "docker", "run", "--rm", "-v",
                            f"{target.resolve()}:/wipe", "alpine:3",
                            "sh", "-c", "rm -rf /wipe/* /wipe/.[!.]* 2>/dev/null; true",
                        ],
                        check=True,
                    )
                    # The directory itself is host-owned and now empty.
                    target.rmdir()
                    ok(f"wiped {target} (via docker)")
                except subprocess.CalledProcessError as e:
                    err(
                        f"docker fallback also failed on {target} (exit {e.returncode}). "
                        "Wipe it manually with: "
                        f"sudo rm -rf {target}"
                    )

        # The credentials are tied to the now-deleted Postgres state — drop them.
        creds = stack_dir / "credentials.env"
        if creds.exists():
            creds.unlink()
            ok(f"removed stale {creds}")

    if args.remove_stack:
        info(f"--remove-stack: rm -rf {stack_dir}")
        shutil.rmtree(stack_dir)
        ok(f"removed {stack_dir}")
        return

    if args.wipe:
        ok("stack stopped and data wiped")
    else:
        ok("stack stopped (volumes preserved — re-run init.py to bring it back up)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        err("interrupted")
        sys.exit(130)
