# Nawat CLI

Python command-line tool for the Nawat platform, built with [Click](https://click.palletsprojects.com/) and [Requests](https://requests.readthedocs.io/).

## Development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
nawat --help
```

## Building the .deb package

Packaging uses [dh-virtualenv](https://dh-virtualenv.readthedocs.io/), which bundles a private
virtualenv (with `click` and `requests` installed) inside the package, so the target machine
needs no system Python packages beyond `python3` itself.

Debian packaging (`dpkg-buildpackage`) only runs on Linux, so on Windows the build is delegated to WSL.

```bat
build_deb.bat
```

This runs `build_deb.sh` inside WSL, which installs the required build dependencies and produces a `nawat-cli_0.1.0-1_<arch>.deb` file in the parent directory.

On Linux/WSL directly, you can instead run:

```bash
./build_deb.sh
```

## Installing the package

```bash
sudo apt install ./nawat-cli_0.1.0-1_<arch>.deb
```

Once installed, the `nawat` command (symlinked from the bundled virtualenv) is available system-wide.
