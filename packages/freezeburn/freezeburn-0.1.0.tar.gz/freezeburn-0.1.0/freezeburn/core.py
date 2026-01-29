"""Core logic for freezeburn.

See ROADMAP.md for the algorithm design.
"""

import ast
import fnmatch
import sys
from importlib.metadata import distributions
from pathlib import Path

# Directories that are always skipped (not configurable).
ALWAYS_SKIP = {".git", ".hg", ".svn", "__pycache__"}


# =============================================================================
# STEP 1: Collect imports
# =============================================================================

def _load_ignore_patterns(project_path: Path) -> list[str]:
    """Load ignore patterns from .gitignore and .reqignore."""
    patterns = []
    for filename in (".gitignore", ".reqignore"):
        path = project_path / filename
        if not path.exists():
            continue
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith(("#", "!")):
                    patterns.append(line.rstrip("/"))
        except (OSError, UnicodeDecodeError):
            continue
    return patterns


def _should_skip(relative_path: Path, patterns: list[str]) -> bool:
    """Check if path should be skipped based on ALWAYS_SKIP or patterns."""
    # Check hardcoded skips.
    if ALWAYS_SKIP & set(relative_path.parts):
        return True
    # Check user patterns.
    path_str = str(relative_path)
    for pattern in patterns:
        if any(fnmatch.fnmatch(part, pattern) for part in relative_path.parts):
            return True
        if fnmatch.fnmatch(path_str, pattern):
            return True
    return False


def _extract_imports_from_file(file_path: Path) -> set[str]:
    """Parse a .py file and return top-level import names."""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, SyntaxError):
        return set()

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return imports


def _collect_imports(project_path: Path) -> set[str]:
    """STEP 1: Find all .py files and extract imports."""
    patterns = _load_ignore_patterns(project_path)
    imports = set()

    for py_file in project_path.rglob("*.py"):
        relative = py_file.relative_to(project_path)
        if _should_skip(relative, patterns):
            continue
        imports.update(_extract_imports_from_file(py_file))

    return imports


# =============================================================================
# STEP 2: Collect installed packages
# =============================================================================

def _collect_installed() -> tuple[dict[str, str], dict[str, str], set[str]]:
    """STEP 2: Get installed packages and import-to-package mapping.

    Returns:
        (packages, import_map, ambiguous) where:
        - packages: {normalized_name: version}
        - import_map: {import_name: package_name}
        - ambiguous: set of import names claimed by multiple packages
    """
    packages = {}
    import_map = {}
    ambiguous = set()

    def add_mapping(import_name: str, package_name: str) -> None:
        """Add import->package mapping, tracking collisions."""
        if import_name in import_map and import_map[import_name] != package_name:
            # Multiple packages claim this import name
            ambiguous.add(import_name)
        import_map[import_name] = package_name

    for dist in distributions():
        name = dist.metadata["Name"]
        version = dist.metadata["Version"]
        if not name or not version:
            continue

        # Normalize: lowercase, hyphens to underscores (PEP 503).
        norm = name.lower().replace("-", "_")
        packages[norm] = version
        add_mapping(norm, norm)

        # Method 1: Read top_level.txt if available.
        try:
            top_level = dist.read_text("top_level.txt")
            for line in (top_level or "").strip().split("\n"):
                if line.strip():
                    add_mapping(line.strip().lower().replace("-", "_"), norm)
        except FileNotFoundError:
            pass

        # Method 2: Parse RECORD file to find installed modules.
        # This catches packages like beautifulsoup4 (bs4/) or six (six.py).
        try:
            record = dist.read_text("RECORD")
            if record:
                for line in record.split("\n"):
                    if not line or "," not in line:
                        continue
                    file_path = line.split(",")[0]

                    # Skip metadata directories
                    if ".dist-info/" in file_path or ".egg-info/" in file_path:
                        continue

                    # Case 1: Package directory "bs4/__init__.py" -> "bs4"
                    if "/__init__.py" in file_path:
                        top_level_name = file_path.split("/")[0]
                        add_mapping(top_level_name.lower().replace("-", "_"), norm)

                    # Case 2: Single-file module "six.py" -> "six"
                    elif file_path.endswith(".py") and "/" not in file_path:
                        module_name = file_path[:-3]  # Remove .py
                        add_mapping(module_name.lower().replace("-", "_"), norm)

                    # Case 3: C extension "cv2.cpython-310-x86_64-linux-gnu.so" -> "cv2"
                    elif ".so" in file_path and "/" not in file_path:
                        module_name = file_path.split(".")[0]
                        add_mapping(module_name.lower().replace("-", "_"), norm)
        except FileNotFoundError:
            pass

    return packages, import_map, ambiguous


# =============================================================================
# STEP 3: Filter and match
# =============================================================================

def _find_candidate_packages(import_name: str, packages: dict[str, str]) -> list[str]:
    """Find installed packages that might provide an import.

    Checks if any package name contains the import name.
    Useful for namespace packages like google-cloud-*.
    """
    norm = import_name.lower().replace("-", "_")
    candidates = []
    for pkg_name in packages:
        # Check if package name contains the import name
        # e.g., "google" matches "google_cloud_storage", "google_auth"
        if norm in pkg_name or pkg_name.startswith(norm):
            candidates.append(pkg_name)
    return sorted(candidates)


def _match_requirements(
    imports: set[str],
    packages: dict[str, str],
    import_map: dict[str, str],
    ambiguous: set[str],
) -> tuple[dict[str, str], list[str]]:
    """STEP 3: Match imports to installed packages.

    Returns:
        (requirements, warnings) where:
        - requirements: {package_name: version}
        - warnings: list of warning messages
    """
    stdlib = sys.stdlib_module_names
    requirements = {}
    warnings = []

    for imp in imports:
        # Skip stdlib (takes priority over installed backport packages).
        if imp in stdlib:
            continue

        # Normalize and look up package.
        norm = imp.lower().replace("-", "_")

        # Check if this import is ambiguous (multiple packages claim it).
        if norm in ambiguous:
            candidates = _find_candidate_packages(imp, packages)
            suggestions = ", ".join(candidates)
            warnings.append(
                f"Import '{imp}' is ambiguous. Candidates: {suggestions}"
            )
            continue

        package = import_map.get(norm, norm)

        # Check if installed.
        if package in packages:
            requirements[package] = packages[package]
        else:
            # Not found - look for candidate packages.
            candidates = _find_candidate_packages(imp, packages)

            if len(candidates) == 1:
                # Single candidate - likely a namespace package, use it.
                pkg = candidates[0]
                requirements[pkg] = packages[pkg]
                warnings.append(
                    f"Import '{imp}' matched to '{pkg}' (auto-detected)"
                )
            elif candidates:
                # Multiple candidates - warn with suggestions.
                suggestions = ", ".join(candidates)
                warnings.append(
                    f"Import '{imp}' not found. Candidates: {suggestions}"
                )
            else:
                # No candidates at all.
                warnings.append(f"Import '{imp}' not found in installed packages")

    return requirements, warnings


# =============================================================================
# STEP 4: Output
# =============================================================================

def write_requirements(lines: list[str], output_path: Path) -> None:
    """Write requirements lines to file."""
    content = "\n".join(lines) + "\n" if lines else ""
    output_path.write_text(content, encoding="utf-8")


# =============================================================================
# Public API
# =============================================================================

def generate_requirements(
    project_path: Path,
    warn_missing: bool = True,
) -> tuple[list[str], list[str]]:
    """Generate requirements.txt content.

    Args:
        project_path: Directory to scan.
        warn_missing: Include warnings for unresolved imports.

    Returns:
        (lines, warnings) where lines are "package==version" strings.
    """
    # Step 1: Collect imports.
    imports = _collect_imports(project_path)

    # Step 2: Collect installed packages.
    packages, import_map, ambiguous = _collect_installed()

    # Step 3: Filter and match.
    requirements, warnings = _match_requirements(imports, packages, import_map, ambiguous)

    # Step 4: Format output.
    lines = [f"{pkg}=={ver}" for pkg, ver in sorted(requirements.items())]

    return lines, warnings if warn_missing else []
