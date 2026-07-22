from __future__ import annotations

import json
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class RepositoryFoundationTests(unittest.TestCase):
    def test_required_foundation_files_exist(self) -> None:
        required_files = (
            ".editorconfig",
            ".env.example",
            ".github/workflows/ci.yml",
            ".gitignore",
            "README.md",
            "backend/pyproject.toml",
            "compose.yaml",
            "frontend/package.json",
            "frontend/tsconfig.json",
            "package.json",
        )

        missing = [path for path in required_files if not (ROOT / path).is_file()]

        self.assertEqual([], missing, f"Missing foundation files: {missing}")

    def test_compose_defines_postgres_and_redis_healthchecks(self) -> None:
        compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")

        self.assertIn("postgres:", compose)
        self.assertIn("redis:", compose)
        self.assertGreaterEqual(compose.count("healthcheck:"), 2)
        self.assertIn("${POSTGRES_PASSWORD:", compose)
        self.assertIn("${POSTGRES_PORT:", compose)
        self.assertIn("${REDIS_PORT:", compose)

    def test_example_environment_covers_local_service_contract(self) -> None:
        env_lines = (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
        env_keys = {
            line.split("=", maxsplit=1)[0]
            for line in env_lines
            if line and not line.startswith("#") and "=" in line
        }

        self.assertTrue(
            {
                "BACKEND_PORT",
                "DATABASE_URL",
                "FRONTEND_ORIGIN",
                "FRONTEND_PORT",
                "INSTRUMENT_SEARCH_LIMIT",
                "POSTGRES_DB",
                "POSTGRES_PASSWORD",
                "POSTGRES_PORT",
                "POSTGRES_USER",
                "REDIS_PORT",
                "REDIS_URL",
            }.issubset(env_keys)
        )

    def test_root_workspace_exposes_quality_commands(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

        self.assertEqual(["frontend"], package["workspaces"])
        for command in ("build", "format:check", "lint", "test", "typecheck"):
            self.assertIn(command, package["scripts"])

    def test_backend_tooling_configures_format_lint_types_and_tests(self) -> None:
        with (ROOT / "backend/pyproject.toml").open("rb") as pyproject_file:
            pyproject = tomllib.load(pyproject_file)

        development_dependencies = pyproject["project"]["optional-dependencies"]["dev"]
        for dependency in ("build", "mypy", "pytest", "ruff"):
            self.assertTrue(
                any(
                    item == dependency or item.startswith(f"{dependency}>")
                    for item in development_dependencies
                ),
                f"Missing backend development dependency: {dependency}",
            )

        self.assertIn("ruff", pyproject["tool"])
        self.assertIn("mypy", pyproject["tool"])
        self.assertIn("pytest", pyproject["tool"])


if __name__ == "__main__":
    unittest.main()
