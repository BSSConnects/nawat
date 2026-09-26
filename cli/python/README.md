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

This runs `build_deb.sh` inside WSL, which installs the required build dependencies and produces a `nawat-cli_0.2.5-1_<arch>.deb` file in the parent directory.

On Linux/WSL directly, you can instead run:

```bash
./build_deb.sh
```

## Installing the package

```bash
sudo apt install ./nawat-cli_0.2.5-1_<arch>.deb
```

Once installed, the `nawat` command (symlinked from the bundled virtualenv) is available system-wide.

## Access token

Log in to the platform with `nawat auth login --email you@example.com`. The command
prompts for the password without echoing it, calls the platform login API, and stores the
access and refresh tokens as JSON in `~/.nawat/config`. On Linux, the directory is
restricted to mode 0700 and the file to mode 0600. The default server is
`https://roaming.bssconnects.io`; set `NAWAT_BASE_URL` or use
`nawat auth --base-url https://your-server.example login` to change it (HTTPS only).

Use `nawat auth status` to check for a local token, `nawat auth refresh` to request a new
access token, `nawat auth me` to see your profile, `nawat auth change-password` to update
your password, and `nawat auth logout` to invalidate and remove local tokens. To save an
existing access token without logging in, use `nawat auth set-token`; it cannot be refreshed.

## Users

After logging in, run `nawat users list` to show usernames and email addresses from the
admin users API. Use `--search`, `--role`, `--status`, `--page`, and `--page-size` to filter
and page through results (empty search, role, and status by default; page 1, 20 users
per page). For example:

```bash
nawat users list --search admin --role ADMIN --status ACTIVE --page 1 --page-size 20
```

Like `auth`, `users` accepts `--base-url` before `list` or reads `NAWAT_BASE_URL`.
