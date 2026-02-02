# UV Package Manager - Tutorial & Commands

UV is a blazingly fast Python package and project manager written in Rust. It's designed as a drop-in replacement for pip, pip-tools, and virtualenv, but 10-100x faster.

## Why UV?

- **Speed**: 10-100x faster than pip
- **Unified tool**: Replaces pip, pip-tools, virtualenv, and more
- **Reliable**: Built in Rust with proper dependency resolution
- **Compatible**: Works with existing Python projects and PyPI

## Installation

### Install UV

```bash
# Using pip
pip install uv

# Using curl (recommended for system-wide install)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Using homebrew (macOS)
brew install uv
```

### Verify Installation

```bash
uv --version
```

---

## Quick Start Guide

### 1. Creating a New Project

```bash
# Create a new Python project
uv init my-project
cd my-project
```

This creates:

- `pyproject.toml` - Project configuration
- `.python-version` - Python version specification
- Basic project structure

### 2. Installing Packages

```bash
# Install a package
uv pip install requests

# Install specific version
uv pip install requests==2.31.0

# Install multiple packages
uv pip install requests pandas numpy

# Install from requirements.txt
uv pip install -r requirements.txt
```

### 3. Virtual Environments

```bash
# Create a virtual environment
uv venv

# Create with specific Python version
uv venv --python 3.11

# Activate the environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\\Scripts\\activate
```

---

## Essential Commands

### Package Management

#### Installing Packages

```bash
# Install package
uv pip install <package>

# Install with extras
uv pip install "fastapi[all]"

# Install editable package (development mode)
uv pip install -e .

# Install from git
uv pip install git+https://github.com/user/repo.git

# Install specific commit/branch/tag
uv pip install git+https://github.com/user/repo.git@main
uv pip install git+https://github.com/user/repo.git@v1.0.0
```

#### Uninstalling Packages

```bash
# Uninstall a package
uv pip uninstall requests

# Uninstall multiple packages
uv pip uninstall requests pandas numpy
```

#### Listing Packages

```bash
# List installed packages
uv pip list

# List in freeze format
uv pip freeze

# Show package details
uv pip show requests
```

#### Upgrading Packages

```bash
# Upgrade a package
uv pip install --upgrade requests

# Upgrade all packages
uv pip install --upgrade -r requirements.txt
```

### Virtual Environment Commands

```bash
# Create virtual environment
uv venv

# Create with name
uv venv myenv

# Create with specific Python version
uv venv --python 3.11
uv venv --python 3.10.5

# Create without pip
uv venv --no-pip

# Use system site packages
uv venv --system-site-packages
```

### Dependency Management

#### Generate Requirements

```bash
# Generate requirements.txt from current environment
uv pip freeze > requirements.txt

# Compile requirements with locked versions
uv pip compile requirements.in -o requirements.txt

# Update locked requirements
uv pip compile requirements.in -o requirements.txt --upgrade
```

#### Sync Environment

```bash
# Sync environment to match requirements.txt exactly
uv pip sync requirements.txt

# This uninstalls packages not in requirements.txt
```

---

## Advanced Usage

### Working with pyproject.toml

UV natively understands `pyproject.toml` for modern Python projects:

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "requests>=2.31.0",
    "pandas>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "black>=23.0",
    "ruff>=0.1.0",
]
```

Install project dependencies:

```bash
# Install project dependencies
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"
```

### Compiling Requirements

[**requirements.in**](http://requirements.in) (high-level dependencies):

```
requests
pandas>=2.0
flask
```

Compile to lock all transitive dependencies:

```bash
# Compile requirements.in to requirements.txt
uv pip compile requirements.in -o requirements.txt

# Upgrade packages during compilation
uv pip compile requirements.in -o requirements.txt --upgrade

# Compile for specific Python version
uv pip compile requirements.in -o requirements.txt --python-version 3.11
```

### Cache Management

```bash
# Show cache directory
uv cache dir

# Clean cache
uv cache clean

# Show cache size
du -sh $(uv cache dir)
```

---

## Command Reference

### Global Commands

| Command | Description |
| --- | --- |
| `uv --version` | Show UV version |
| `uv --help` | Show help message |
| `uv self update` | Update UV to latest version |

### pip Commands

| Command | Description |
| --- | --- |
| `uv pip install <pkg>` | Install package |
| `uv pip uninstall <pkg>` | Uninstall package |
| `uv pip list` | List installed packages |
| `uv pip freeze` | Output installed packages in requirements format |
| `uv pip show <pkg>` | Show package information |
| `uv pip check` | Verify installed packages have compatible dependencies |
| `uv pip compile <file>` | Compile requirements file with locked versions |
| `uv pip sync <file>` | Sync environment to requirements file |

### venv Commands

| Command | Description |
| --- | --- |
| `uv venv` | Create virtual environment |
| `uv venv <name>` | Create named virtual environment |
| `uv venv --python <version>` | Create with specific Python version |

### cache Commands

| Command | Description |
| --- | --- |
| `uv cache dir` | Show cache directory |
| `uv cache clean` | Clean cache |

---

## Common Workflows

### Starting a New Project

```bash
# 1. Create project directory
mkdir my-project && cd my-project

# 2. Initialize project (optional)
uv init

# 3. Create virtual environment
uv venv

# 4. Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\\Scripts\\activate  # Windows

# 5. Install dependencies
uv pip install requests pandas numpy

# 6. Freeze requirements
uv pip freeze > requirements.txt
```

### Cloning an Existing Project

```bash
# 1. Clone repository
git clone https://github.com/user/project.git
cd project

# 2. Create virtual environment
uv venv

# 3. Activate environment
source .venv/bin/activate

# 4. Install dependencies
uv pip install -r requirements.txt

# 5. Install project in editable mode (if setup.py/pyproject.toml exists)
uv pip install -e .
```

### Managing Dependencies with Compile + Sync

```bash
# 1. Create requirements.in with high-level dependencies
echo "requests\npandas>=2.0\nflask" > requirements.in

# 2. Compile to lock versions
uv pip compile requirements.in -o requirements.txt

# 3. Sync environment
uv pip sync requirements.txt

# 4. To update dependencies later
uv pip compile requirements.in -o requirements.txt --upgrade
uv pip sync requirements.txt
```

### Development vs Production Dependencies

[**requirements.in**](http://requirements.in):

```
requests
flask
```

[**requirements-dev.in**](http://requirements-dev.in):

```
-c requirements.txt
pytest
black
ruff
```

Compile both:

```bash
uv pip compile requirements.in -o requirements.txt
uv pip compile requirements-dev.in -o requirements-dev.txt
```

---

## Tips & Best Practices

### Speed Optimization

✅ **UV is already optimized**, but you can:

- Use `uv pip sync` instead of `uv pip install -r` when possible (faster)
- Leverage the cache - UV caches downloads automatically
- Use `--no-deps` flag to skip dependency resolution if you know dependencies are satisfied

### Compatibility with pip

✅ **Drop-in replacement**: Most `pip` commands work with `uv pip`

```bash
# These are equivalent:
pip install requests
uv pip install requests
```

### Environment Variables

```bash
# Disable cache
export UV_NO_CACHE=1

# Custom cache directory
export UV_CACHE_DIR=/path/to/cache

# Set index URL
export UV_INDEX_URL=https://custom-pypi.example.com/simple
```

### Using with Docker

```docker
FROM python:3.11-slim

# Install UV
RUN pip install uv

# Copy requirements
COPY requirements.txt .

# Install dependencies with UV (much faster!)
RUN uv pip install --system -r requirements.txt

# Copy application
COPY . .

CMD ["python", "app.py"]
```

### Migration from pip

**Before (pip)**:

```bash
pip install -r requirements.txt
pip freeze > requirements.txt
pip list
```

**After (UV)**:

```bash
uv pip install -r requirements.txt
uv pip freeze > requirements.txt
uv pip list
```

Just add `uv` before `pip`!

---

## Comparison with Other Tools

| Feature | pip | pip-tools | poetry | UV |
| --- | --- | --- | --- | --- |
| Speed | Slow | Slow | Medium | **Very Fast** |
| Dependency resolution | Basic | Good | Excellent | Excellent |
| Lock files | ❌ | ✅ | ✅ | ✅ |
| Virtual env management | ❌ | ❌ | ✅ | ✅ |
| Project scaffolding | ❌ | ❌ | ✅ | ✅ |
| PyPI compatible | ✅ | ✅ | ✅ | ✅ |

---

## Troubleshooting

### Issue: Command not found

```bash
# Ensure UV is in PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Or reinstall
pip install --upgrade uv
```

### Issue: Dependency conflicts

```bash
# Check for conflicts
uv pip check

# Use compile to see dependency tree
uv pip compile requirements.in --verbose
```

### Issue: Slow downloads

```bash
# Use a mirror
uv pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple requests

# Or set permanently
export UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## Resources

- **Official docs**: [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv)
- **PyPI page**: [https://pypi.org/project/uv/](https://pypi.org/project/uv/)
- **Astral (creators)**: [https://astral.sh/](https://astral.sh/)

---

## Quick Reference Card

```bash
# Installation
pip install uv

# Virtual environment
uv venv                          # Create
source .venv/bin/activate       # Activate (Unix)
.venv\\Scripts\\activate          # Activate (Windows)

# Install packages
uv pip install <package>         # Install
uv pip install -r requirements.txt  # From file
uv pip install -e .              # Editable mode

# Manage dependencies
uv pip list                      # List packages
uv pip freeze > requirements.txt # Save requirements
uv pip compile requirements.in   # Lock dependencies
uv pip sync requirements.txt     # Sync environment

# Update
uv pip install --upgrade <pkg>   # Upgrade package
uv self update                   # Update UV itself

# Cache
uv cache clean                   # Clear cache
uv cache dir                     # Show cache location
```