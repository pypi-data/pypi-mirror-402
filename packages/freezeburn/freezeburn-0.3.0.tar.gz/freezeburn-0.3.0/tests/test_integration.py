"""Integration tests for freezeburn.

These tests create real virtual environments and install real packages.
They are slower but test the full workflow.
"""

import pytest


class TestBasicFunctionality:
    """Test basic import detection and package matching."""

    def test_single_package(self, venv_factory, project_factory):
        """Test detecting a single imported package."""
        venv = venv_factory()
        venv.install("requests")

        project = project_factory(files={
            "main.py": "import requests\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        assert len(lines) == 1
        assert lines[0].startswith("requests==")
        assert warnings == []

    def test_multiple_packages(self, venv_factory, project_factory):
        """Test detecting multiple imported packages."""
        venv = venv_factory()
        venv.install("requests", "click")

        project = project_factory(files={
            "main.py": "import requests\nimport click\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        assert len(lines) == 2
        packages = [line.split("==")[0] for line in lines]
        assert "requests" in packages
        assert "click" in packages

    def test_from_import(self, venv_factory, project_factory):
        """Test 'from x import y' style imports."""
        venv = venv_factory()
        venv.install("requests")

        project = project_factory(files={
            "main.py": "from requests import Session\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        assert len(lines) == 1
        assert lines[0].startswith("requests==")

    def test_submodule_import(self, venv_factory, project_factory):
        """Test 'import x.y.z' extracts top-level only."""
        venv = venv_factory()
        venv.install("requests")

        project = project_factory(files={
            "main.py": "import requests.auth\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        assert len(lines) == 1
        assert lines[0].startswith("requests==")


class TestStdlibFiltering:
    """Test that standard library imports are filtered out."""

    def test_stdlib_ignored(self, venv_factory, project_factory):
        """Test that stdlib imports don't appear in output."""
        venv = venv_factory()
        venv.install("requests")

        project = project_factory(files={
            "main.py": "import os\nimport sys\nimport json\nimport requests\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        assert len(lines) == 1
        assert lines[0].startswith("requests==")
        # No stdlib in output
        packages = [line.split("==")[0] for line in lines]
        assert "os" not in packages
        assert "sys" not in packages
        assert "json" not in packages


class TestMissingPackages:
    """Test handling of imports for packages not installed."""

    def test_warning_for_missing(self, venv_factory, project_factory):
        """Test that missing packages generate warnings."""
        venv = venv_factory()
        # Don't install anything

        project = project_factory(files={
            "main.py": "import nonexistent_package_xyz\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        assert lines == []
        assert len(warnings) == 1
        assert "nonexistent_package_xyz" in warnings[0]

    def test_partial_match(self, venv_factory, project_factory):
        """Test project with mix of installed and missing packages."""
        venv = venv_factory()
        venv.install("requests")

        project = project_factory(files={
            "main.py": "import requests\nimport missing_pkg\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        assert len(lines) == 1
        assert lines[0].startswith("requests==")
        assert len(warnings) == 1
        assert "missing_pkg" in warnings[0]


class TestIgnorePatterns:
    """Test .gitignore and .reqignore support."""

    def test_gitignore_respected(self, venv_factory, project_factory):
        """Test that .gitignore patterns are respected."""
        venv = venv_factory()
        venv.install("requests", "click")

        project = project_factory(files={
            "main.py": "import requests\n",
            "ignored/script.py": "import click\n",
            ".gitignore": "ignored/\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        # Only requests should be found, click is in ignored dir
        packages = [line.split("==")[0] for line in lines]
        assert "requests" in packages
        assert "click" not in packages

    def test_reqignore_respected(self, venv_factory, project_factory):
        """Test that .reqignore patterns are respected."""
        venv = venv_factory()
        venv.install("requests", "click")

        project = project_factory(files={
            "main.py": "import requests\n",
            "tests/test_main.py": "import click\n",
            ".reqignore": "tests/\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        packages = [line.split("==")[0] for line in lines]
        assert "requests" in packages
        assert "click" not in packages

    def test_wildcard_pattern(self, venv_factory, project_factory):
        """Test wildcard patterns in ignore files."""
        venv = venv_factory()
        venv.install("requests", "click")

        project = project_factory(files={
            "main.py": "import requests\n",
            "test_something.py": "import click\n",
            ".reqignore": "test_*.py\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        packages = [line.split("==")[0] for line in lines]
        assert "requests" in packages
        assert "click" not in packages


class TestDifferentImportNames:
    """Test packages with different import names than package names."""

    def test_pillow_pil(self, venv_factory, project_factory):
        """Test Pillow package imported as PIL."""
        venv = venv_factory()
        venv.install("Pillow")

        project = project_factory(files={
            "main.py": "from PIL import Image\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        assert len(lines) == 1
        assert lines[0].startswith("pillow==")
        assert warnings == []

    def test_beautifulsoup(self, venv_factory, project_factory):
        """Test beautifulsoup4 package imported as bs4."""
        venv = venv_factory()
        venv.install("beautifulsoup4")

        project = project_factory(files={
            "main.py": "from bs4 import BeautifulSoup\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        assert len(lines) == 1
        assert lines[0].startswith("beautifulsoup4==")

    def test_pyyaml(self, venv_factory, project_factory):
        """Test PyYAML package imported as yaml."""
        venv = venv_factory()
        venv.install("PyYAML")

        project = project_factory(files={
            "main.py": "import yaml\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        assert len(lines) == 1
        assert lines[0].startswith("pyyaml==")

    def test_python_dateutil(self, venv_factory, project_factory):
        """Test python-dateutil package imported as dateutil."""
        venv = venv_factory()
        venv.install("python-dateutil")

        project = project_factory(files={
            "main.py": "from dateutil import parser\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        assert len(lines) == 1
        assert lines[0].startswith("python_dateutil==")

    def test_six_single_file(self, venv_factory, project_factory):
        """Test six package (single-file module)."""
        venv = venv_factory()
        venv.install("six")

        project = project_factory(files={
            "main.py": "import six\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        assert len(lines) == 1
        assert lines[0].startswith("six==")


class TestMultipleTopLevel:
    """Test packages that provide multiple importable modules."""

    def test_setuptools_pkg_resources(self, venv_factory, project_factory):
        """Test setuptools which provides both setuptools and pkg_resources."""
        venv = venv_factory()
        venv.install("setuptools")

        project = project_factory(files={
            "main.py": "import pkg_resources\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        packages = [line.split("==")[0] for line in lines]
        assert "setuptools" in packages


class TestNamespacePackages:
    """Test namespace package detection and suggestions."""

    def test_single_namespace_candidate(self, venv_factory, project_factory):
        """Test detection when only one namespace package installed."""
        venv = venv_factory()
        venv.install("google-auth")

        project = project_factory(files={
            "main.py": "from google.auth import credentials\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        # google-auth provides google/ so it should be detected
        packages = [line.split("==")[0] for line in lines]
        assert "google_auth" in packages

    def test_multiple_namespace_candidates(self, venv_factory, project_factory):
        """Test warning when multiple namespace packages installed."""
        venv = venv_factory()
        venv.install("google-auth", "google-api-core")

        project = project_factory(files={
            "main.py": "from google.auth import credentials\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        # Should NOT auto-detect (ambiguous - both claim 'google')
        packages = [line.split("==")[0] for line in lines]
        assert "google_auth" not in packages
        assert "google_api_core" not in packages
        # Should warn about ambiguity
        assert any("ambiguous" in w.lower() for w in warnings)


class TestMultipleFiles:
    """Test scanning multiple Python files."""

    def test_multiple_files(self, venv_factory, project_factory):
        """Test imports collected from multiple files."""
        venv = venv_factory()
        venv.install("requests", "click", "rich")

        project = project_factory(files={
            "main.py": "import requests\n",
            "cli.py": "import click\n",
            "utils/display.py": "import rich\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        packages = [line.split("==")[0] for line in lines]
        assert len(packages) == 3
        assert "requests" in packages
        assert "click" in packages
        assert "rich" in packages

    def test_duplicate_imports(self, venv_factory, project_factory):
        """Test that duplicate imports result in single entry."""
        venv = venv_factory()
        venv.install("requests")

        project = project_factory(files={
            "main.py": "import requests\n",
            "other.py": "import requests\n",
            "another.py": "from requests import Session\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        assert len(lines) == 1
        assert lines[0].startswith("requests==")


class TestOutputFormat:
    """Test output formatting."""

    def test_sorted_alphabetically(self, venv_factory, project_factory):
        """Test that output is sorted alphabetically."""
        venv = venv_factory()
        venv.install("requests", "click", "rich")

        project = project_factory(files={
            "main.py": "import requests\nimport click\nimport rich\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        packages = [line.split("==")[0] for line in lines]
        assert packages == sorted(packages)

    def test_exact_version_pinning(self, venv_factory, project_factory):
        """Test that versions are exactly pinned with ==."""
        venv = venv_factory()
        venv.install("requests==2.31.0")

        project = project_factory(files={
            "main.py": "import requests\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        assert len(lines) == 1
        assert lines[0] == "requests==2.31.0"


class TestSpecificVersions:
    """Test that exact versions are captured correctly."""

    def test_django_specific_version(self, venv_factory, project_factory):
        """Test Django 5.2 is detected with exact version."""
        venv = venv_factory()
        venv.install("django==5.2")

        project = project_factory(files={
            "app.py": "import django\nfrom django.http import HttpResponse\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        assert len(lines) == 1
        assert lines[0] == "django==5.2"
        assert warnings == []

    def test_multiple_pinned_versions(self, venv_factory, project_factory):
        """Test multiple packages with specific versions."""
        venv = venv_factory()
        venv.install("requests==2.31.0", "click==8.1.7")

        project = project_factory(files={
            "main.py": "import requests\nimport click\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        assert "click==8.1.7" in lines
        assert "requests==2.31.0" in lines


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_project(self, venv_factory, project_factory):
        """Test project with no Python files."""
        venv = venv_factory()
        project = project_factory(files={})

        lines, warnings = venv.run_freezeburn(project)

        assert lines == []
        assert warnings == []

    def test_syntax_error_file(self, venv_factory, project_factory):
        """Test that files with syntax errors are skipped gracefully."""
        venv = venv_factory()
        venv.install("requests")

        project = project_factory(files={
            "main.py": "import requests\n",
            "broken.py": "def broken(\n",  # Syntax error
        })

        lines, warnings = venv.run_freezeburn(project)

        # Should still find requests from main.py
        assert len(lines) == 1
        assert lines[0].startswith("requests==")

    def test_relative_imports_ignored(self, venv_factory, project_factory):
        """Test that relative imports are ignored."""
        venv = venv_factory()
        venv.install("requests")

        project = project_factory(files={
            "pkg/__init__.py": "",
            "pkg/main.py": "from . import utils\nimport requests\n",
            "pkg/utils.py": "pass\n",
        })

        lines, warnings = venv.run_freezeburn(project)

        # Only requests, not the relative import
        assert len(lines) == 1
        assert lines[0].startswith("requests==")
