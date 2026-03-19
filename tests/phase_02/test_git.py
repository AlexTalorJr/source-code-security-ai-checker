"""Tests for git clone and cleanup module."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scanner.core.exceptions import GitCloneError
from scanner.core.git import cleanup_clone, clone_repo


def _make_mock_process(returncode: int = 0, stdout: bytes = b"", stderr: bytes = b""):
    """Create a mock process with async communicate."""
    proc = AsyncMock()
    proc.communicate.return_value = (stdout, stderr)
    proc.returncode = returncode
    return proc


@pytest.mark.asyncio
@patch("scanner.core.git.asyncio.create_subprocess_exec")
async def test_clone_repo_builds_shallow_command(mock_exec):
    """Shallow clone includes --depth 1 --branch --single-branch."""
    mock_exec.return_value = _make_mock_process()

    with patch("scanner.core.git.tempfile.mkdtemp", return_value="/tmp/scanner-clone-test"):
        result = await clone_repo("https://github.com/test/repo.git", "main", shallow=True)

    call_args = mock_exec.call_args
    cmd = call_args[0]
    assert "--depth" in cmd
    assert "1" in cmd
    assert "--branch" in cmd
    assert "main" in cmd
    assert "--single-branch" in cmd
    assert result == "/tmp/scanner-clone-test"


@pytest.mark.asyncio
@patch("scanner.core.git.asyncio.create_subprocess_exec")
async def test_clone_repo_builds_full_command(mock_exec):
    """Full clone (shallow=False) does NOT include --depth."""
    mock_exec.return_value = _make_mock_process()

    with patch("scanner.core.git.tempfile.mkdtemp", return_value="/tmp/scanner-clone-test"):
        await clone_repo("https://github.com/test/repo.git", "main", shallow=False)

    call_args = mock_exec.call_args
    cmd = call_args[0]
    assert "--depth" not in cmd
    assert "--branch" in cmd
    assert "--single-branch" in cmd


@pytest.mark.asyncio
@patch("scanner.core.git.asyncio.create_subprocess_exec")
async def test_clone_repo_https_token_sets_askpass(mock_exec):
    """When git_token is provided with HTTPS URL, GIT_ASKPASS is set."""
    mock_exec.return_value = _make_mock_process()

    with patch("scanner.core.git.tempfile.mkdtemp", return_value="/tmp/scanner-clone-test"):
        # We need to mock open and chmod since /tmp/scanner-clone-test doesn't exist
        with patch("builtins.open", MagicMock()):
            with patch("scanner.core.git.os.chmod"):
                await clone_repo(
                    "https://github.com/test/repo.git",
                    "main",
                    git_token="mytoken",
                )

    call_kwargs = mock_exec.call_args[1]
    assert "env" in call_kwargs
    assert "GIT_ASKPASS" in call_kwargs["env"]


@pytest.mark.asyncio
@patch("scanner.core.git.asyncio.create_subprocess_exec")
async def test_clone_repo_raises_on_failure(mock_exec):
    """Non-zero returncode raises GitCloneError."""
    mock_exec.return_value = _make_mock_process(
        returncode=128, stderr=b"fatal: repository not found"
    )

    with patch("scanner.core.git.tempfile.mkdtemp", return_value="/tmp/scanner-clone-test"):
        with patch("scanner.core.git.shutil.rmtree"):
            with pytest.raises(GitCloneError, match="git clone failed"):
                await clone_repo("https://github.com/test/repo.git", "main")


def test_cleanup_clone_removes_directory():
    """cleanup_clone removes the directory."""
    tmpdir = tempfile.mkdtemp(prefix="scanner-clone-test-")
    assert os.path.isdir(tmpdir)
    cleanup_clone(tmpdir)
    assert not os.path.exists(tmpdir)
