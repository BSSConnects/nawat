"""Local access-token storage for the CLI."""

import json
import os
import tempfile
from pathlib import Path


def config_path() -> Path:
    return Path.home() / ".nawat" / "config"


def _load_config() -> dict | None:
    try:
        with config_path().open(encoding="utf-8") as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as error:
        raise ValueError("Invalid token in ~/.nawat/config") from error
    if not isinstance(config, dict) or not isinstance(config.get("token"), str) or not config["token"]:
        raise ValueError("Invalid token in ~/.nawat/config")
    return config


def load_token() -> str | None:
    config = _load_config()
    return config["token"] if config else None


def load_refresh_token() -> str | None:
    config = _load_config()
    if config is None:
        return None
    refresh_token = config.get("refresh_token")
    if refresh_token is not None and (not isinstance(refresh_token, str) or not refresh_token):
        raise ValueError("Invalid refresh token in ~/.nawat/config")
    return refresh_token


def save_token(token: str, refresh_token: str | None = None) -> None:
    if not token.strip():
        raise ValueError("Token cannot be empty")
    if refresh_token is not None and not refresh_token.strip():
        raise ValueError("Refresh token cannot be empty")

    path = config_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    descriptor, temporary_path = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as config_file:
            config = {"token": token}
            if refresh_token is not None:
                config["refresh_token"] = refresh_token
            json.dump(config, config_file)
            config_file.write("\n")
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def clear_token() -> None:
    config_path().unlink(missing_ok=True)