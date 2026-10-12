#!/usr/bin/env python3
"""Bring up the sandbox-level self-hosted Supabase stack.

Idempotent: detects a healthy running stack and re-emits ``credentials.env``
without rotating secrets. Use ``--force`` to regenerate keys + restart.

Reproduces the upstream ``docker/utils/generate-keys.sh`` byte-for-byte using
only the Python standard library (no PyJWT — HS256 = HMAC-SHA256).

Usage::

    python skills/supabase-init/scripts/init.py
    python skills/supabase-init/scripts/init.py --force
    python skills/supabase-init/scripts/init.py --sandbox-root /path/to/sandbox
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import re
import secrets
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# ---------------------------------------------------------------------------- #
# Paths / constants
# ---------------------------------------------------------------------------- #

DEFAULT_SANDBOX_ROOT = Path(__file__).resolve().parents[3]
SUPABASE_REPO = "https://github.com/supabase/supabase.git"
SUPABASE_REF = "master"

# Keys we mutate in docker/.env. Mirrors generate-keys.sh's sed list.
SECRET_KEYS_TO_ROTATE = [
    "JWT_SECRET",
    "ANON_KEY",
    "SERVICE_ROLE_KEY",
    "SECRET_KEY_BASE",
    "VAULT_ENC_KEY",
    "PG_META_CRYPTO_KEY",
    "LOGFLARE_PUBLIC_ACCESS_TOKEN",
    "LOGFLARE_PRIVATE_ACCESS_TOKEN",
    "S3_PROTOCOL_ACCESS_KEY_ID",
    "S3_PROTOCOL_ACCESS_KEY_SECRET",
    "MINIO_ROOT_PASSWORD",
    "POSTGRES_PASSWORD",
    "DASHBOARD_PASSWORD",
]

HEALTH_TIMEOUT_S = 300       # 5 min after up -d
HEALTH_POLL_INTERVAL_S = 5

# ---------------------------------------------------------------------------- #
# Pretty printing
# ---------------------------------------------------------------------------- #


class C:
    R = "\033[31m"
    G = "\033[32m"
    Y = "\033[33m"
    B = "\033[34m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    OFF = "\033[0m"


def info(msg: str) -> None:
    print(f"{C.B}→{C.OFF} {msg}", flush=True)


def ok(msg: str) -> None:
    print(f"{C.G}✓{C.OFF} {msg}", flush=True)


def warn(msg: str) -> None:
    print(f"{C.Y}!{C.OFF} {msg}", flush=True)


def err(msg: str) -> None:
    print(f"{C.R}✗{C.OFF} {msg}", file=sys.stderr, flush=True)


def hdr(msg: str) -> None:
    print(f"\n{C.BOLD}{msg}{C.OFF}", flush=True)


# ---------------------------------------------------------------------------- #
# Subprocess helpers
# ---------------------------------------------------------------------------- #


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    capture: bool = False,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Thin wrapper. Echoes the command, surfaces real errors."""
    info(f"$ {' '.join(cmd)}{f'   ({cwd})' if cwd else ''}")
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=check,
        text=True,
        capture_output=capture,
        env={**__import__('os').environ, **(env_extra or {})} if env_extra else None,
    )


# ---------------------------------------------------------------------------- #
# Secret generation (mirrors generate-keys.sh)
# ---------------------------------------------------------------------------- #


def rand_hex(nbytes: int) -> str:
    """Equivalent to ``openssl rand -hex <nbytes>`` — emits 2*nbytes hex chars."""
    return secrets.token_hex(nbytes)


def rand_b64(nbytes: int) -> str:
    """Equivalent to ``openssl rand -base64 <nbytes>`` — standard alphabet, padded."""
    return base64.standard_b64encode(secrets.token_bytes(nbytes)).decode("ascii")


def b64url(data: bytes) -> str:
    """JWT-style base64url, no padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def mint_hs256_jwt(role: str, *, secret: str, iat: int, exp: int) -> str:
    """Build an HS256 JWT with payload ``{role,iss,iat,exp}`` (matches upstream)."""
    header = b'{"alg":"HS256","typ":"JWT"}'
    payload = json.dumps(
        {"role": role, "iss": "supabase", "iat": iat, "exp": exp},
        separators=(",", ":"),  # compact, matches upstream's printf %s
    ).encode("ascii")

    signing_input = b64url(header) + "." + b64url(payload)
    sig = hmac.new(secret.encode("ascii"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return signing_input + "." + b64url(sig)


def fresh_secrets() -> dict[str, str]:
    """Generate the full set of secrets the official script writes."""
    iat = int(time.time())
    exp = iat + 5 * 365 * 24 * 3600  # 5 years

    jwt_secret = rand_b64(30).rstrip()  # openssl prints with trailing newline; strip
    return {
        "JWT_SECRET": jwt_secret,
        "ANON_KEY": mint_hs256_jwt("anon", secret=jwt_secret, iat=iat, exp=exp),
        "SERVICE_ROLE_KEY": mint_hs256_jwt(
            "service_role", secret=jwt_secret, iat=iat, exp=exp
        ),
        "SECRET_KEY_BASE": rand_b64(48),
        "VAULT_ENC_KEY": rand_hex(16),
        "PG_META_CRYPTO_KEY": rand_b64(24),
        "LOGFLARE_PUBLIC_ACCESS_TOKEN": rand_b64(24),
        "LOGFLARE_PRIVATE_ACCESS_TOKEN": rand_b64(24),
        "S3_PROTOCOL_ACCESS_KEY_ID": rand_hex(16),
        "S3_PROTOCOL_ACCESS_KEY_SECRET": rand_hex(32),
        "MINIO_ROOT_PASSWORD": rand_hex(16),
        "POSTGRES_PASSWORD": rand_hex(16),
        "DASHBOARD_PASSWORD": rand_hex(16),
    }


# ---------------------------------------------------------------------------- #
# .env file munging
# ---------------------------------------------------------------------------- #


def patch_env_file(env_path: Path, replacements: dict[str, str]) -> None:
    """Replace ``KEY=...`` lines in-place; preserves comments and ordering."""
    text = env_path.read_text()
    for key, value in replacements.items():
        pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
        if not pattern.search(text):
            warn(f"{env_path.name}: key '{key}' not found, appending")
            text += f"\n{key}={value}\n"
        else:
            text = pattern.sub(f"{key}={value}", text)
    env_path.write_text(text)


def parse_env_file(env_path: Path) -> dict[str, str]:
    """Bare-bones .env parser. No quoting / interpolation / multi-line."""
    out: dict[str, str] = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


# ---------------------------------------------------------------------------- #
# Prerequisite checks
# ---------------------------------------------------------------------------- #


def check_prereqs() -> None:
    missing: list[str] = []
    for cmd in ("docker", "git"):
        if shutil.which(cmd) is None:
            missing.append(cmd)
    if missing:
        err(f"missing tools: {', '.join(missing)}")
        sys.exit(1)

    # docker compose v2 is `docker compose ...`; v1 is `docker-compose`.
    try:
        run(["docker", "compose", "version"], capture=True, check=True)
    except subprocess.CalledProcessError:
        err("docker compose v2 plugin not detected (`docker compose version` failed)")
        sys.exit(1)

    ok("prerequisites OK (docker, docker compose, git)")


def warn_port_conflicts(env_path: Path) -> None:
    """Best-effort: check 8000 and 5432 are free. Don't block — just warn."""
    env = parse_env_file(env_path)
    for label, port in [
        ("Kong / API", int(env.get("KONG_HTTP_PORT", "8000"))),
        ("Postgres",   int(env.get("POSTGRES_PORT",   "5432"))),
    ]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                warn(f"port {port} ({label}) already in use — boot may fail")


# ---------------------------------------------------------------------------- #
# Stack lifecycle
# ---------------------------------------------------------------------------- #


def stack_is_healthy(docker_dir: Path) -> bool:
    """All compose services in healthy state? Empty stack → False."""
    try:
        proc = run(
            ["docker", "compose", "ps", "--format", "json"],
            cwd=docker_dir,
            capture=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return False

    rows = []
    for raw in proc.stdout.strip().splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(row, list):
            rows.extend(row)
        else:
            rows.append(row)

    if not rows:
        return False

    # A service is "healthy" if Health == 'healthy' or it has no healthcheck
    # but State == 'running'. We accept either; we mostly care that the gateway
    # is reachable, which the HTTP probe below verifies.
    bad = [r for r in rows if r.get("State") not in ("running", "exited") or
                              (r.get("Health") not in ("", "healthy", None))]
    return len(rows) > 0 and not bad


def fetch_supabase_docker(stack_dir: Path) -> None:
    """Sparse-clone supabase/supabase docker/ subtree into stack_dir/docker."""
    if (stack_dir / "docker").exists():
        warn(f"{stack_dir / 'docker'} already exists — skipping clone")
        return

    stack_dir.mkdir(parents=True, exist_ok=True)
    tmp = stack_dir / "_supabase-tmp"
    if tmp.exists():
        shutil.rmtree(tmp)

    run(
        ["git", "clone", "--filter=blob:none", "--no-checkout",
         "--depth=1", "--branch", SUPABASE_REF, SUPABASE_REPO, str(tmp)],
        cwd=stack_dir,
    )
    run(["git", "sparse-checkout", "set", "--cone", "docker"], cwd=tmp)
    run(["git", "checkout", SUPABASE_REF], cwd=tmp)

    src = tmp / "docker"
    if not src.exists():
        err(f"sparse clone produced no {src}")
        sys.exit(1)

    shutil.move(str(src), str(stack_dir / "docker"))
    shutil.rmtree(tmp)
    ok(f"docker/ subtree placed at {stack_dir / 'docker'}")


def materialise_env(docker_dir: Path) -> Path:
    """Ensure docker/.env exists (copy from .env.example), return its path."""
    env = docker_dir / ".env"
    example = docker_dir / ".env.example"
    if env.exists():
        info(f".env already present at {env} — leaving as-is")
        return env
    if not example.exists():
        err(f"{example} not found; clone may be corrupted")
        sys.exit(1)
    shutil.copy(example, env)
    ok(f"copied .env.example → .env at {env}")
    return env


def rotate_secrets(env_path: Path) -> dict[str, str]:
    """Generate fresh secrets, write them to docker/.env, return them."""
    secrets_map = fresh_secrets()
    patch_env_file(env_path, secrets_map)
    ok(f"rotated {len(secrets_map)} secrets in {env_path}")
    return secrets_map


def docker_compose_up(docker_dir: Path) -> None:
    run(["docker", "compose", "pull"], cwd=docker_dir)
    run(["docker", "compose", "up", "-d"], cwd=docker_dir)


def wait_for_rest(api_url: str, anon_key: str) -> None:
    """Poll Kong's /rest/v1/ until 200, or fail after HEALTH_TIMEOUT_S."""
    info(f"waiting for {api_url}/rest/v1/ to respond (≤{HEALTH_TIMEOUT_S}s)")
    deadline = time.time() + HEALTH_TIMEOUT_S
    last_err: str = ""
    while time.time() < deadline:
        req = urllib.request.Request(
            f"{api_url}/rest/v1/",
            headers={"apikey": anon_key, "Authorization": f"Bearer {anon_key}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                if 200 <= resp.status < 400:
                    ok(f"PostgREST responded {resp.status}")
                    return
                last_err = f"HTTP {resp.status}"
        except urllib.error.HTTPError as e:
            if 200 <= e.code < 400:
                ok(f"PostgREST responded {e.code}")
                return
            last_err = f"HTTP {e.code}"
        except Exception as exc:  # noqa: BLE001 — we want to keep retrying
            last_err = type(exc).__name__
        time.sleep(HEALTH_POLL_INTERVAL_S)

    err(f"timed out waiting for PostgREST (last: {last_err})")
    sys.exit(1)


# ---------------------------------------------------------------------------- #
# credentials.env emission
# ---------------------------------------------------------------------------- #


def emit_credentials(stack_dir: Path, env_path: Path) -> Path:
    env = parse_env_file(env_path)
    api_port = env.get("KONG_HTTP_PORT", "8000")
    db_port = env.get("POSTGRES_PORT", "5432")

    api_url = f"http://127.0.0.1:{api_port}"
    db_url = (
        f"postgres://postgres:{env['POSTGRES_PASSWORD']}@127.0.0.1:{db_port}/postgres"
    )

    creds_path = stack_dir / "credentials.env"
    creds_path.write_text(
        "# Generated by skills/supabase-init/scripts/init.py — do not edit by hand.\n"
        "# Source this file from per-project .env files, or read it directly.\n"
        "\n"
        f"SUPABASE_URL={api_url}\n"
        f"SUPABASE_ANON_KEY={env['ANON_KEY']}\n"
        f"SUPABASE_SERVICE_ROLE_KEY={env['SERVICE_ROLE_KEY']}\n"
        f"SUPABASE_JWT_SECRET={env['JWT_SECRET']}\n"
        f"SUPABASE_DB_URL={db_url}\n"
        f"SUPABASE_STUDIO_URL={api_url}\n"
        f"SUPABASE_DASHBOARD_USERNAME={env.get('DASHBOARD_USERNAME', 'supabase')}\n"
        f"SUPABASE_DASHBOARD_PASSWORD={env['DASHBOARD_PASSWORD']}\n"
    )
    ok(f"wrote {creds_path}")
    return creds_path


# ---------------------------------------------------------------------------- #
# Entry point
# ---------------------------------------------------------------------------- #


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--sandbox-root",
        type=Path,
        default=DEFAULT_SANDBOX_ROOT,
        help=f"sandbox root (default: {DEFAULT_SANDBOX_ROOT})",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="rotate secrets and bring the stack down/up even if it's already running "
             "(EXISTING DATA will become unreachable with the new keys)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    sandbox_root: Path = args.sandbox_root.resolve()
    stack_dir = sandbox_root / ".supabase"
    docker_dir = stack_dir / "docker"

    hdr(f"supabase-init  →  sandbox: {sandbox_root}")

    check_prereqs()

    already_up = docker_dir.exists() and stack_is_healthy(docker_dir)

    if already_up and not args.force:
        ok("stack already running — re-emitting credentials.env without changes")
        emit_credentials(stack_dir, docker_dir / ".env")
        print_next_steps(stack_dir)
        return

    if already_up and args.force:
        warn("--force: tearing the stack down before regenerating secrets")
        run(["docker", "compose", "down"], cwd=docker_dir, check=False)

    fetch_supabase_docker(stack_dir)
    env_path = materialise_env(docker_dir)
    warn_port_conflicts(env_path)

    rotate = args.force or not _secrets_already_rotated(env_path)
    if rotate:
        rotate_secrets(env_path)
    else:
        info(".env already has rotated secrets — keeping them")

    docker_compose_up(docker_dir)

    env = parse_env_file(env_path)
    api_url = f"http://127.0.0.1:{env.get('KONG_HTTP_PORT', '8000')}"
    wait_for_rest(api_url, env["ANON_KEY"])

    emit_credentials(stack_dir, env_path)
    print_next_steps(stack_dir)


def _secrets_already_rotated(env_path: Path) -> bool:
    """Heuristic: the upstream defaults for these are static placeholders.

    If POSTGRES_PASSWORD and JWT_SECRET still match either upstream default,
    we assume init has never rotated them.
    """
    env = parse_env_file(env_path)
    placeholders = {
        "POSTGRES_PASSWORD": "your-super-secret-and-long-postgres-password",
        "JWT_SECRET":        "your-super-secret-jwt-token-with-at-least-32-characters-long",
    }
    return all(env.get(k, "") and env[k] != v for k, v in placeholders.items())


def print_next_steps(stack_dir: Path) -> None:
    creds = stack_dir / "credentials.env"
    docker_dir = stack_dir / "docker"
    hdr("Next steps")
    print(
        f"""
  • Credentials are in:   {creds}
  • Stack root:           {docker_dir}
  • API base URL:         see SUPABASE_URL inside credentials.env
  • Studio (Dashboard):   open SUPABASE_STUDIO_URL in a browser

  Backend (<cwd>/apps/backend/.env, dotenv file — copy values, `source` does not work)::

      BE_DB_PROVIDER=supabase
      BE_SUPABASE_DB_URL=<SUPABASE_DB_URL>
      BE_SUPABASE_JWT_SECRET=<SUPABASE_JWT_SECRET>   # only with BE_AUTH_PROVIDER=supabase

  Shell-sourced project envs (<cwd>/apps/agents/<role>/.env, etc.)::

      source $(realpath {creds})

  Common operations::

      python skills/supabase-init/scripts/teardown.py            # stop, keep data
      python skills/supabase-init/scripts/teardown.py --wipe     # stop + drop volumes
      python skills/supabase-init/scripts/print_env.py           # re-emit credentials.env
"""
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        err("interrupted")
        sys.exit(130)
