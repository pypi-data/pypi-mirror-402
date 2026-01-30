"""
core.py – all the heavy lifting for sparkstart
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

# C++ with CMake + Conan
GITIGNORE_CPP = textwrap.dedent("""
    # Build output
    build/
    
    # CMake generated files
    CMakeCache.txt
    CMakeFiles/
    cmake_install.cmake
    Makefile
    
    # Conan
    conan_output/
    
    # IDE
    .vscode/
    .idea/
    
    # General
    .DS_Store
    .projinit.env
""").strip()

NEW_TOKEN_URL = (
    "https://github.com/settings/tokens/new?description=projinit:{name}&scopes=repo,delete_repo,user"
)

DEVCONTAINER_JSON = textwrap.dedent("""
    {
      "name": "C++",
      "image": "mcr.microsoft.com/devcontainers/cpp:1-debian-12",
      "features": {
        "ghcr.io/devcontainers/features/common-utils:2": {
          "installZsh": true,
          "configureZshAsDefaultShell": true,
          "installOhMyZsh": true,
          "upgradePackages": true
        }
      },
      "postCreateCommand": "sudo apt-get update && sudo apt-get install -y neovim",
      "customizations": {
        "vscode": {
          "extensions": [
            "ms-vscode.cpptools",
            "ms-vscode.cmake-tools",
            "waderyan.gitblame",
            "asvetliakov.vscode-neovim"
          ]
        }
      }
    }
""").strip()

BUILD_SH = textwrap.dedent("""
    #!/bin/bash
    set -e
    
    # ==============================================================================
    # Build Script - a shortcut for the CMake workflow
    # ==============================================================================
    
    echo "🚀 Building {name}..."
    
    # 1. Create build directory
    mkdir -p build
    
    # 2. Dependency Management (Optional)
    # If you use Conan, uncomment the following line:
    # conan install . --output-folder=build --build=missing
    
    # 3. Configure (CMake)
    cd build
    cmake ..
    
    # 4. Build (Compile)
    cmake --build .
    
    echo "✅ Build complete! Run with: ./build/{name}"
""").strip()

README_CPP = textwrap.dedent("""
    # {name}
    
    A C++ project initialized by `sparkstart`.
    
    ## 🚀 Quick Start
    
    ### Prerequisites
    - **C++ Compiler** (g++, clang++, or MSVC)
    - **CMake** (3.15+)
    - **Conan** (Optional, for dependencies)
    
    ### Build & Run
    We use an **out-of-source** build workflow to keep your source directory clean.
    
    ```bash
    # 1. Configure (Generate Build Files)
    cd build
    cmake ..
    
    # 2. Build (Compile)
    cmake --build .
    
    # 3. Run
    ./{name}
    ```
    
    ## 📂 Project Structure
    - `src/`             - Your C++ source files (Start with main.cpp)
    - `build/`           - Build artifacts (Makefiles, binaries) - keep this clean!
    - `CMakeLists.txt`   - The "Recipe" for CMake to build your project
    - `conanfile.txt`    - List of libraries you want to install
    
    ## 📚 "How-To" Mini-Guides
    
    ### How to add a new Source Folder?
    1. Create the folder (e.g. `src/utils/`)
    2. Add a `CMakeLists.txt` inside strictly identifying its library name.
    3. In the main `CMakeLists.txt`, add: `add_subdirectory(src/utils)`
    *(See comments in CMakeLists.txt for examples)*
    
    ### How to add a Dependency (Library)?
    1. Search for it on [Conan Center](https://conan.io/center) (e.g. `fmt`).
    2. Add it to `conanfile.txt` under `[requires]`.
    3. Run: `conan install . --output-folder=build --build=missing`
    4. Uncomment the Conan lines in `CMakeLists.txt` to link it.
""").strip()


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


def _scaffold_devcontainer(path: pathlib.Path, lang: str) -> None:
    """Create .devcontainer configuration."""
    if lang != "cpp":
        # Only C++ supported for now (can expand later)
        return

    (path / ".devcontainer").mkdir()
    (path / ".devcontainer" / "devcontainer.json").write_text(DEVCONTAINER_JSON + "\n")


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


def _scaffold_cpp(path: pathlib.Path) -> None:
    """Create C++ project structure with CMake + Conan and Hello World."""
    # Check for C++ compiler
    if shutil.which("g++") is None:
        raise RuntimeError(
            "g++ not found. Install a C++ compiler:\n"
            "  Ubuntu/Debian:  sudo apt install g++\n"
            "  Fedora:         sudo dnf install gcc-c++\n"
            "  Arch:           sudo pacman -S gcc\n"
            "  macOS:          xcode-select --install"
        )
    
    # Check for CMake (Required for our project structure)
    if shutil.which("cmake") is None:
        raise RuntimeError(
            "cmake not found. Install CMake to build the project:\n"
            "  Ubuntu/Debian:  sudo apt install cmake\n"
            "  Fedora:         sudo dnf install cmake\n"
            "  Mac:            brew install cmake"
        )

    # Check for Conan (Optional / Warning)
    if shutil.which("conan") is None:
        import typer
        typer.secho(
            "WARNING: 'conan' not found. You will need it later to manage dependencies.\n"
            "  Install: pip install conan",
            fg=typer.colors.YELLOW
        )
    (path / "src").mkdir()
    (path / "build").mkdir()  # Convention: out-of-source builds
    
    # Hello World main.cpp
    main_cpp = textwrap.dedent('''
        #include <iostream>
        
        int main() {
            std::cout << "Hello, world!" << std::endl;
            return 0;
        }
    ''').strip()
    (path / "src" / "main.cpp").write_text(main_cpp + "\n")
    
    (path / ".gitignore").write_text(GITIGNORE_CPP + "\n")
    
    # CMakeLists.txt with comments explaining each section
    cmake_content = textwrap.dedent(f'''
        # ==============================================================================
        # CMakeLists.txt — The "build recipe" for your C++ project
        # ==============================================================================
        # CMake reads this file and generates platform-specific build files
        # (Makefiles on Linux/Mac, Visual Studio projects on Windows, etc.)
        #
        # To build this project:
        #   1. cd build
        #   2. cmake ..          # Generate build files from this recipe
        #   3. cmake --build .   # Actually compile the code
        # ==============================================================================
        
        cmake_minimum_required(VERSION 3.15)
        
        # Project name and version — CMake uses this to name outputs
        project({path.name} VERSION 0.1.0 LANGUAGES CXX)
        
        # Use C++17 standard (modern C++ features)
        set(CMAKE_CXX_STANDARD 17)
        set(CMAKE_CXX_STANDARD_REQUIRED ON)
        
        # ------------------------------------------------------------------------------
        # CONAN INTEGRATION (optional — uncomment when you add dependencies)
        # ------------------------------------------------------------------------------
        # After running `conan install . --output-folder=build --build=missing`
        # this line tells CMake where Conan put the dependency info:
        #
        # include(${{CMAKE_BINARY_DIR}}/conan_toolchain.cmake)
        # ------------------------------------------------------------------------------
        
        # Create an executable named after your project
        # This tells CMake: "compile src/main.cpp into an executable"
        add_executable(${{PROJECT_NAME}} src/main.cpp)
        
        # ------------------------------------------------------------------------------
        # ADDING MORE SOURCE FILES
        # ------------------------------------------------------------------------------
        # As your project grows, list all .cpp files:
        #
        # add_executable(${{PROJECT_NAME}}
        #     src/main.cpp
        #     src/utils.cpp
        #     src/game.cpp
        # )
        # ------------------------------------------------------------------------------

        # ------------------------------------------------------------------------------
        # ADDING SUBDIRECTORIES (Tutorial)
        # ------------------------------------------------------------------------------
        # To organize code into folders (e.g. src/engine/), create a CMakeLists.txt inside
        # that folder and use:
        #
        # add_subdirectory(src/engine)
        # ------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------
        # LINKING CONAN DEPENDENCIES (uncomment when you add libraries)
        # ------------------------------------------------------------------------------
        # Example: if you added "fmt" in conanfile.txt:
        #
        # find_package(fmt REQUIRED)
        # target_link_libraries(${{PROJECT_NAME}} fmt::fmt)
        # ------------------------------------------------------------------------------
    ''').strip()
    (path / "CMakeLists.txt").write_text(cmake_content + "\n")
    
    # conanfile.txt — simple dependency list format
    conan_content = textwrap.dedent('''
        # ==============================================================================
        # conanfile.txt — Your C++ dependency list
        # ==============================================================================
        # Conan is a package manager for C++ (like pip for Python or npm for JS).
        # This file lists what libraries you want and how to integrate them.
        #
        # To install dependencies:
        #   conan install . --output-folder=build --build=missing
        #
        # This downloads libraries and generates files that CMake can use.
        # ==============================================================================
        
        [requires]
        # Add dependencies here, one per line. Examples:
        # fmt/10.2.1          # Modern formatting library
        # spdlog/1.13.0       # Fast logging library  
        # nlohmann_json/3.11.3  # JSON parsing
        
        [generators]
        # CMakeToolchain — generates conan_toolchain.cmake for CMake integration
        # CMakeDeps — generates find_package() config for each dependency
        CMakeToolchain
        CMakeDeps
        
        [layout]
        cmake_layout
    ''').strip()
    (path / "conanfile.txt").write_text(conan_content + "\n")

    # Build script
    build_sh = path / "build.sh"
    build_sh.write_text(BUILD_SH.format(name=path.name) + "\n")
    # Make executable (chmod +x)
    build_sh.chmod(build_sh.stat().st_mode | 0o111)


# ----------------------------------------------------------------------------- #
# Public API                                                                    #
# ----------------------------------------------------------------------------- #


def create_project(path: pathlib.Path, github: bool = False, lang: str = "python", devcontainer: bool = False) -> None:
    """
    Make a fully-initialised project directory.

    Parameters
    ----------
    path   : pathlib.Path  target directory (must not already exist)
    github : bool          if True, also create & push remote repo
    lang   : str           language: "python", "rust", "javascript", or "cpp"
    devcontainer : bool    if True, generate .devcontainer config
    """
    # Create project folder
    path.mkdir(parents=False, exist_ok=False)
    
    # Add README
    if lang == "cpp":
        (path / "README.md").write_text(README_CPP.format(name=path.name))
    else:
        (path / "README.md").write_text(README_TEXT.format(name=path.name))

    # Language-specific scaffolding
    if lang == "python":
        _scaffold_python(path)
    elif lang == "rust":
        _scaffold_rust(path)
    elif lang == "javascript":
        _scaffold_javascript(path)
    elif lang == "cpp":
        _scaffold_cpp(path)
    else:
        raise ValueError(f"Unknown language: {lang}. Choose: python, rust, javascript, cpp")

    # Dev Container
    if devcontainer:
        if shutil.which("docker") is None:
            import typer
            typer.secho(
                "WARNING: Docker not found. You need Docker to use Dev Containers.",
                fg=typer.colors.YELLOW
            )
        _scaffold_devcontainer(path, lang)

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
