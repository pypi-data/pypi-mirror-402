"""Pytest fixtures for freezeburn integration tests."""

import subprocess
import sys
import venv
from pathlib import Path

import pytest


class VenvManager:
    """Manages a temporary virtual environment for testing."""

    def __init__(self, path: Path):
        self.path = path
        self.python = self._get_python_path()

    def _get_python_path(self) -> Path:
        """Get path to python executable in venv."""
        if sys.platform == "win32":
            return self.path / "Scripts" / "python.exe"
        return self.path / "bin" / "python"

    def create(self) -> None:
        """Create the virtual environment."""
        venv.create(self.path, with_pip=True)

    def install(self, *packages: str) -> None:
        """Install packages into the venv."""
        subprocess.run(
            [str(self.python), "-m", "pip", "install", "-q", *packages],
            check=True,
            capture_output=True,
        )

    def run_freezeburn(self, project_path: Path) -> tuple[list[str], list[str]]:
        """Run freezeburn logic using this venv's installed packages.

        This imports freezeburn and runs it in a subprocess using this venv's
        Python, so it sees this venv's installed packages.
        """
        # We need to run in subprocess to use the venv's importlib.metadata
        code = f'''
import sys
sys.path.insert(0, "{Path(__file__).parent.parent}")
from freezeburn.core import generate_requirements
from pathlib import Path
lines, warnings, orphans = generate_requirements(Path("{project_path}"))
print("LINES:")
for line in lines:
    print(line)
print("WARNINGS:")
for w in warnings:
    print(w)
'''
        result = subprocess.run(
            [str(self.python), "-c", code],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"freezeburn failed: {result.stderr}")

        # Parse output
        output = result.stdout
        lines_section = False
        warnings_section = False
        lines = []
        warnings = []

        for line in output.strip().split("\n"):
            if line == "LINES:":
                lines_section = True
                warnings_section = False
                continue
            elif line == "WARNINGS:":
                lines_section = False
                warnings_section = True
                continue

            if lines_section and line:
                lines.append(line)
            elif warnings_section and line:
                warnings.append(line)

        return lines, warnings


@pytest.fixture
def venv_factory(tmp_path: Path):
    """Factory fixture to create virtual environments."""
    created_venvs = []

    def _create(name: str = "test_venv") -> VenvManager:
        venv_path = tmp_path / name
        manager = VenvManager(venv_path)
        manager.create()
        created_venvs.append(manager)
        return manager

    yield _create

    # Cleanup is handled by tmp_path fixture


@pytest.fixture
def project_factory(tmp_path: Path):
    """Factory fixture to create test project directories."""

    def _create(name: str = "test_project", files: dict[str, str] | None = None) -> Path:
        project_path = tmp_path / name
        project_path.mkdir(exist_ok=True)

        if files:
            for filename, content in files.items():
                file_path = project_path / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)

        return project_path

    return _create
