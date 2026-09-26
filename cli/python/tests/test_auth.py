import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from nawat_cli.auth import clear_token, config_path, load_refresh_token, load_token, save_token
from nawat_cli.main import cli


class AuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.home.cleanup)
        home_patch = patch("nawat_cli.auth.Path.home", return_value=Path(self.home.name))
        home_patch.start()
        self.addCleanup(home_patch.stop)

    def test_missing_token(self) -> None:
        self.assertIsNone(load_token())
        result = CliRunner().invoke(cli, ["auth", "status"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("No token configured", result.output)

    def test_save_and_load_token(self) -> None:
        save_token("secret-token")
        self.assertEqual(load_token(), "secret-token")
        self.assertIsNone(load_refresh_token())
        self.assertEqual(config_path(), Path(self.home.name) / ".nawat" / "config")
        if os.name != "nt":
            self.assertEqual(config_path().parent.stat().st_mode & 0o777, 0o700)
            self.assertEqual(config_path().stat().st_mode & 0o777, 0o600)
        save_token("replacement", "refresh-secret")
        self.assertEqual(load_token(), "replacement")
        self.assertEqual(load_refresh_token(), "refresh-secret")
        clear_token()
        self.assertIsNone(load_token())

    def test_cli_prompt_does_not_print_token(self) -> None:
        result = CliRunner().invoke(cli, ["auth", "set-token"], input="secret-token\n")
        self.assertEqual(result.exit_code, 0)
        self.assertNotIn("secret-token", result.output)
        self.assertEqual(load_token(), "secret-token")

    def test_invalid_config_is_reported(self) -> None:
        config_path().parent.mkdir()
        config_path().write_text("not json", encoding="utf-8")
        result = CliRunner().invoke(cli, ["auth", "status"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Invalid token", result.output)

    def test_login_and_refresh(self) -> None:
        response = Mock()
        response.json.return_value = {"access_token": "access-one", "refresh_token": "refresh-one"}
        with patch("nawat_cli.main.requests.request", return_value=response) as request:
            result = CliRunner().invoke(cli, ["auth", "login", "--email", "user@example.test"], input="password-secret\n")
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertNotIn("password-secret", result.output)
            self.assertNotIn("access-one", result.output)
            request.assert_called_once_with(
                "POST", "https://roaming.bssconnects.io/api/v1/auth/login",
                json={"email": "user@example.test", "password": "password-secret"}, headers=None, timeout=10,
            )
        self.assertEqual(load_token(), "access-one")
        self.assertEqual(load_refresh_token(), "refresh-one")

        response.json.return_value = {"access_token": "access-two"}
        with patch("nawat_cli.main.requests.request", return_value=response) as request:
            result = CliRunner().invoke(cli, ["auth", "refresh"])
            self.assertEqual(result.exit_code, 0, result.output)
            request.assert_called_once_with(
                "POST", "https://roaming.bssconnects.io/api/v1/auth/refresh",
                json={"refresh_token": "refresh-one"}, headers=None, timeout=10,
            )
        self.assertEqual(load_token(), "access-two")
        self.assertEqual(load_refresh_token(), "refresh-one")

    def test_profile_and_logout(self) -> None:
        save_token("access-one", "refresh-one")
        response = Mock()
        response.json.return_value = {"email": "user@example.test"}
        with patch("nawat_cli.main.requests.request", return_value=response) as request:
            result = CliRunner().invoke(cli, ["auth", "me"])
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("user@example.test", result.output)
            request.assert_called_once_with(
                "GET", "https://roaming.bssconnects.io/api/v1/auth/me",
                json=None, headers={"Authorization": "Bearer access-one"}, timeout=10,
            )
        with patch("nawat_cli.main.requests.request", return_value=response) as request:
            result = CliRunner().invoke(cli, ["auth", "logout"])
            self.assertEqual(result.exit_code, 0, result.output)
            request.assert_called_once_with(
                "POST", "https://roaming.bssconnects.io/api/v1/auth/logout",
                json=None, headers={"Authorization": "Bearer access-one"}, timeout=10,
            )
        self.assertIsNone(load_token())

    def test_change_password(self) -> None:
        save_token("access-one")
        with patch("nawat_cli.main.requests.request", return_value=Mock()) as request:
            result = CliRunner().invoke(cli, ["auth", "change-password"], input="old-secret\nnew-secret\nnew-secret\n")
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertNotIn("old-secret", result.output)
            self.assertNotIn("new-secret", result.output)
            request.assert_called_once_with(
                "POST", "https://roaming.bssconnects.io/api/v1/auth/change-password",
                json={"current_password": "old-secret", "new_password": "new-secret"},
                headers={"Authorization": "Bearer access-one"}, timeout=10,
            )

    def test_login_rejects_insecure_url_and_invalid_response(self) -> None:
        with patch("nawat_cli.main.requests.request") as request:
            result = CliRunner().invoke(cli, ["auth", "--base-url", "http://example.test", "login", "--email", "user@example.test"], input="secret\n")
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("HTTPS origin", result.output)
            request.assert_not_called()
        response = Mock()
        response.json.return_value = {"access_token": "access-only"}
        with patch("nawat_cli.main.requests.request", return_value=response):
            result = CliRunner().invoke(cli, ["auth", "login", "--email", "user@example.test"], input="secret\n")
            self.assertNotEqual(result.exit_code, 0)
            self.assertIsNone(load_token())

    def test_list_users_with_filters(self) -> None:
        save_token("access-one")
        response = Mock()
        response.headers = {"Content-Type": "application/json"}
        response.json.return_value = {"users": [
            {"username": "admin", "email": "admin@example.test"},
            {"username": "second-user", "email": "second@example.test"},
        ]}
        with patch("nawat_cli.main.requests.get", return_value=response) as request:
            result = CliRunner().invoke(cli, ["users", "list", "--search", "admin", "--role", "ADMIN",
                                               "--status", "ACTIVE", "--page", "2", "--page-size", "5"])
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("USERNAME     EMAIL", result.output)
            self.assertIn("admin        admin@example.test", result.output)
            self.assertIn("second-user  second@example.test", result.output)
            self.assertNotIn("access-one", result.output)
            request.assert_called_once_with(
                "https://roaming.bssconnects.io/api/v1/admin/users",
                params={"page": 2, "page_size": 5, "search": "admin", "role": "ADMIN", "status": "ACTIVE"},
                headers={"Authorization": "Bearer access-one"}, timeout=10,
            )

    def test_list_users_empty_page_and_defaults(self) -> None:
        save_token("access-one")
        response = Mock()
        response.headers = {"Content-Type": "application/json"}
        response.json.return_value = {"data": []}
        with patch("nawat_cli.main.requests.get", return_value=response) as request:
            result = CliRunner().invoke(cli, ["users", "list"])
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(result.output.strip(), "USERNAME  EMAIL")
            request.assert_called_once_with(
                "https://roaming.bssconnects.io/api/v1/admin/users",
                params={"search": "", "role": "", "status": "", "page": 1, "page_size": 20},
                headers={"Authorization": "Bearer access-one"}, timeout=10,
            )

    def test_list_users_rejects_missing_token_and_invalid_response(self) -> None:
        with patch("nawat_cli.main.requests.get") as request:
            result = CliRunner().invoke(cli, ["users", "list"])
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("nawat auth login", result.output)
            request.assert_not_called()

        save_token("access-one")
        response = Mock()
        response.headers = {"Content-Type": "application/json"}
        response.json.return_value = {"unexpected": []}
        with patch("nawat_cli.main.requests.get", return_value=response):
            result = CliRunner().invoke(cli, ["users", "list"])
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("Invalid users response", result.output)

        response.headers = {"Content-Type": "text/html"}
        with patch("nawat_cli.main.requests.get", return_value=response):
            result = CliRunner().invoke(cli, ["users", "list"])
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("text/html instead of JSON", result.output)

        with patch("nawat_cli.main.requests.get") as request:
            result = CliRunner().invoke(cli, ["users", "list", "--page", "0"])
            self.assertNotEqual(result.exit_code, 0)
            request.assert_not_called()


if __name__ == "__main__":
    unittest.main()