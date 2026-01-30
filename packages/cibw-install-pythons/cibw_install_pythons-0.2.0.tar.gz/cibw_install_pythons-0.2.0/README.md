# cibw-install-pythons

This is an *unofficial* script for installing the Python versions used by
[`cibuildwheel`](https://cibuildwheel.pypa.io/). Currently, only macOS is
supported.

**This script is intended for use in CI environments only.** It installs CPython
versions system-wide, and there is no easy way to change that behavior because
the CPython `pkg` files used by `cibuildwheel` cannot be relocated upon
installation. If you run this script on your development machine, **you will
likely break something.**

## Installation

```zsh
python -m pip install cibw-install-pythons
```

## Usage

```zsh
CI=1 python -m cibw-install-pythons macos
```

If the `CI=1` variable is not provided, `cibuildwheel` aborts by default to
avoid damaging systems not in CI environments.

CPython is always installed system-wide. PyPy and GraalPy are installed by
default in a cache under your `$HOME` directory. To change where these Python
versions are installed, use the `CIBW_CACHE_PATH` environment variable.

For example, to install in a system-wide cache,

```bash
CI=1 CIBW_CACHE_PATH=/Library/Caches/cibuildwheel python \
                                                  -m cibw-install-pythons macos
```