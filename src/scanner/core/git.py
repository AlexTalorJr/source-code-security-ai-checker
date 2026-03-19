"""Git clone and cleanup utilities for repo-URL scan mode."""

import asyncio
import os
import shutil
import tempfile

from scanner.core.exceptions import GitCloneError


async def clone_repo(
    repo_url: str,
    branch: str,
    shallow: bool = True,
    git_token: str | None = None,
) -> str:
    """Clone a git repository to a temporary directory.

    Args:
        repo_url: Repository URL (HTTPS or SSH).
        branch: Branch name to clone.
        shallow: If True, performs a shallow clone (--depth 1).
        git_token: HTTPS token for authentication (optional).

    Returns:
        Path to the temporary directory containing the cloned repo.

    Raises:
        GitCloneError: If git clone exits with a non-zero return code.
    """
    tmpdir = tempfile.mkdtemp(prefix="scanner-clone-")

    env = os.environ.copy()
    if git_token and repo_url.startswith("https://"):
        # GIT_ASKPASS approach avoids leaking token in process args
        askpass_script = os.path.join(tmpdir, ".git-askpass")
        with open(askpass_script, "w") as f:
            f.write(f"#!/bin/sh\necho {git_token}\n")
        os.chmod(askpass_script, 0o700)
        env["GIT_ASKPASS"] = askpass_script

    cmd = ["git", "clone", "--branch", branch, "--single-branch"]
    if shallow:
        cmd.extend(["--depth", "1"])
    cmd.extend([repo_url, tmpdir])

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise GitCloneError(
            f"git clone failed (exit {proc.returncode}): {stderr.decode()}"
        )

    return tmpdir


def cleanup_clone(clone_path: str) -> None:
    """Remove a cloned repository directory.

    Intended to be called in finally blocks. Silently ignores errors
    (e.g. if the directory was already removed).

    Args:
        clone_path: Path to the cloned repository directory.
    """
    shutil.rmtree(clone_path, ignore_errors=True)
