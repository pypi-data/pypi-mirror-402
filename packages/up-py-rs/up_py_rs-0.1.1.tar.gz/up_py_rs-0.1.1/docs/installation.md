# Installation

## Requirements

- Python 3.8 or higher
- pip (Python package installer)

## Install from PyPI

The easiest way to install `up-py-rs` is via pip:

```bash
pip install up-py-rs
```

This will download and install the latest stable version from [PyPI](https://pypi.org/project/up-py-rs/).

## Install a Specific Version

To install a specific version:

```bash
pip install up-py-rs==0.0.5
```

## Upgrade to Latest Version

To upgrade to the latest version:

```bash
pip install --upgrade up-py-rs
```

## Verify Installation

After installation, you can verify it works by checking the version:

```python
import up_py_rs
print(up_py_rs.__version__)
```

## Development Installation

If you want to contribute to the project or build from source:

### Prerequisites

- Python 3.8+
- Rust (latest stable)
- Maturin (`pip install maturin`)

### Build from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/sachinkum0009/up-py-rs.git
   cd up-py-rs
   ```

2. Install in development mode:
   ```bash
   maturin develop
   ```

This will compile the Rust code and install the package in editable mode.

## Troubleshooting

### Import Errors

If you encounter import errors, ensure that:
- Python version is 3.8 or higher
- The package was installed successfully (check with `pip list | grep up-py-rs`)

### Platform-Specific Issues

The package provides pre-built wheels for common platforms. If a wheel is not available for your platform, pip will attempt to build from source, which requires:
- Rust toolchain installed
- Appropriate C compiler for your platform
