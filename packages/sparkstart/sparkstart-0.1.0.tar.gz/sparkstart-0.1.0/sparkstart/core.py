"""
core.py – all the heavy lifting for projinit
    • folder scaffold          (src/, README, .gitignore, etc.)
    • local virtual-env        (.venv) for Python
    • git repo + first commit
    • optional --github push   (per-project token in .projinit.env or $GITHUB_TOKEN)

Requires: requests, python-dotenv
    pip install requests python-dotenv
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import textwrap
import venv
import webbrowser
from typing import List

import requests
from dotenv import dotenv_values

# ----------------------------------------------------------------------------- #
# Constants                                                                     #
# ----------------------------------------------------------------------------- #

README_TEXT = "# {name}\n\nProject initialized by `projinit`."

# Language-specific gitignore patterns
GITIGNORE_PYTHON = textwrap.dedent("""
    __pycache__/
    .venv/
    *.pyc
    .DS_Store
    .projinit.env
""").strip()

GITIGNORE_RUST = textwrap.dedent("""
    /target
    .DS_Store
    .projinit.env
""").strip()

GITIGNORE_JAVASCRIPT = textwrap.dedent("""
    node_modules/
    .DS_Store
    .projinit.env
""").strip()

NEW_TOKEN_URL = (
    "https://github.com/settings/tokens/new?description=projinit:{name}&scopes=repo,delete_repo,user"
)


# ----------------------------------------------------------------------------- #
# Helper functions                                                              #
# ----------------------------------------------------------------------------- #


def _sh(cmd: List[str], cwd: pathlib.Path) -> None:
    """Run *cmd* in *cwd*; raise RuntimeError on non-zero exit."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"$ {' '.join(cmd)}\n{result.stderr.strip() or 'command failed'}"
        )


# ---------- per-project token helpers ---------------------------------------- #


def _project_token(project_root: pathlib.Path) -> str | None:
    """Return token from .projinit.env or '' if file missing/empty."""
    return dotenv_values(project_root / ".projinit.env").get("GITHUB_TOKEN", "")


def _save_project_token(project_root: pathlib.Path, token: str | None) -> None:
    """Persist token to .projinit.env and ensure it's git-ignored."""
    (project_root / ".projinit.env").write_text(f"GITHUB_TOKEN={token}\n")

    gi = project_root / ".gitignore"
    lines: list[str] = gi.read_text().splitlines() if gi.exists() else []
    if ".projinit.env" not in lines:
        lines.append(".projinit.env")
        gi.write_text("\n".join(lines) + "\n")


# ---------- GitHub API ------------------------------------------------------- #


def _github_user(token: str) -> str:
    """Get the authenticated GitHub username."""
    r = requests.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=10,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"GitHub API error {r.status_code}: {r.text.strip()}")
    return r.json()["login"]


def _create_github_repo(repo_name: str, token: str | None = None) -> str:
    """
    Create repo under authenticated user; return clone URL.
    *token* optional – falls back to $GITHUB_TOKEN.
    """
    token = token or os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError(
            "GitHub token not provided.\n"
            "Save one in .projinit.env, set $GITHUB_TOKEN, or pass --github without a token to be prompted."
        )

    r = requests.post(
        "https://api.github.com/user/repos",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        },
        json={"name": repo_name, "private": False},
        timeout=10,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"GitHub API error {r.status_code}: {r.text.strip()}")
    return r.json()["clone_url"]  # e.g. https://github.com/user/repo.git


def _delete_github_repo(owner: str, repo_name: str, token: str) -> None:
    """Delete a GitHub repository."""
    r = requests.delete(
        f"https://api.github.com/repos/{owner}/{repo_name}",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=10,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"GitHub API error {r.status_code}: {r.text.strip()}")


# ----------------------------------------------------------------------------- #
# Language-specific scaffolding                                                 #
# ----------------------------------------------------------------------------- #


def _scaffold_python(path: pathlib.Path) -> None:
    """Create Python project structure with Hello World."""
    (path / "src").mkdir()
    (path / "src" / "__init__.py").touch()
    (path / "src" / "main.py").write_text('print("Hello, world!")\n')
    (path / ".gitignore").write_text(GITIGNORE_PYTHON + "\n")
    (path / "requirements.txt").touch()
    
    # Create pyproject.toml
    pyproject = textwrap.dedent(f'''
        [project]
        name = "{path.name}"
        version = "0.1.0"
        description = ""
        requires-python = ">=3.8"
        dependencies = []
    ''').strip()
    (path / "pyproject.toml").write_text(pyproject + "\n")
    
    # Create virtual environment
    venv.create(path / ".venv", with_pip=True)


def _scaffold_rust(path: pathlib.Path) -> None:
    """Create Rust project structure with Hello World."""
    (path / "src").mkdir()
    (path / "src" / "main.rs").write_text('fn main() {\n    println!("Hello, world!");\n}\n')
    (path / ".gitignore").write_text(GITIGNORE_RUST + "\n")
    
    # Create Cargo.toml
    cargo_toml = textwrap.dedent(f'''
        [package]
        name = "{path.name}"
        version = "0.1.0"
        edition = "2021"

        [dependencies]
    ''').strip()
    (path / "Cargo.toml").write_text(cargo_toml + "\n")


def _scaffold_javascript(path: pathlib.Path) -> None:
    """Create JavaScript project structure with Hello World."""
    (path / "index.js").write_text('console.log("Hello, world!");\n')
    (path / ".gitignore").write_text(GITIGNORE_JAVASCRIPT + "\n")
    
    # Create package.json
    package_json = textwrap.dedent(f'''
        {{
          "name": "{path.name}",
          "version": "0.1.0",
          "description": "",
          "main": "index.js",
          "scripts": {{
            "start": "node index.js"
          }}
        }}
    ''').strip()
    (path / "package.json").write_text(package_json + "\n")


# ----------------------------------------------------------------------------- #
# Public API                                                                    #
# ----------------------------------------------------------------------------- #


def create_project(path: pathlib.Path, github: bool = False, lang: str = "python") -> None:
    """
    Make a fully-initialised project directory.

    Parameters
    ----------
    path   : pathlib.Path  target directory (must not already exist)
    github : bool          if True, also create & push remote repo
    lang   : str           language: "python", "rust", or "javascript"
    """
    # Create project folder
    path.mkdir(parents=False, exist_ok=False)
    
    # Add README
    (path / "README.md").write_text(README_TEXT.format(name=path.name))

    # Language-specific scaffolding
    if lang == "python":
        _scaffold_python(path)
    elif lang == "rust":
        _scaffold_rust(path)
    elif lang == "javascript":
        _scaffold_javascript(path)
    else:
        raise ValueError(f"Unknown language: {lang}. Choose: python, rust, javascript")

    # git repository
    if shutil.which("git") is None:
        raise RuntimeError("`git` executable not found in PATH")

    # GitHub remote + push (optional)
    token: str | None = None
    if github:
        # token preference: .projinit.env  >  $GITHUB_TOKEN  >  prompt user
        token = _project_token(path) or os.getenv("GITHUB_TOKEN", "")
        if not token:
            import typer  # lazy import to avoid hard dependency in library mode

            typer.secho("Opening GitHub to generate a token...", fg=typer.colors.YELLOW)
            webbrowser.open(NEW_TOKEN_URL.format(name=path.name))
            token = typer.prompt(
                "Paste your new GitHub token here (saved to .projinit.env, never committed)"
            )
            _save_project_token(path, token)

    _sh(["git", "init", "-b", "main"], cwd=path)
    _sh(["git", "add", "."], cwd=path)
    _sh(["git", "commit", "-m", "Initial commit"], cwd=path)

    if github:
        repo_url = _create_github_repo(path.name, token)
        # inject token into HTTPS URL for authentication: https://TOKEN@github.com/...
        auth_repo_url = repo_url.replace("https://", f"https://{token}@", 1)

        _sh(["git", "remote", "add", "origin", auth_repo_url], cwd=path)
        _sh(["git", "push", "-u", "origin", "main"], cwd=path)


def delete_project(path: pathlib.Path, github: bool = False) -> None:
    """
    Delete *path* directory; optionally delete its remote GitHub repo.

    Token resolution order:
        1.  .projinit.env inside the project
        2.  $GITHUB_TOKEN
        3.  raise RuntimeError if --github but no token found
    """
    if not path.exists():
        raise RuntimeError(f"{path} does not exist")

    # remove remote first (so local folder still has .projinit.env if needed)
    if github:
        token = _project_token(path) or os.getenv("GITHUB_TOKEN")
        if not token:
            raise RuntimeError(
                "No GitHub token found in .projinit.env or $GITHUB_TOKEN"
            )
        owner = _github_user(token)
        _delete_github_repo(owner, path.name, token)

    # finally delete local directory
    shutil.rmtree(path)
