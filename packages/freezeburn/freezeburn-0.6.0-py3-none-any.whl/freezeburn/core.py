"""Core logic for freezeburn.

See ROADMAP.md for the algorithm design.
"""

import ast
import fnmatch
import re
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


def _is_submodule(path: Path, project_path: Path) -> bool:
    """Check if path is inside a git submodule."""
    current = path.parent if path.is_file() else path
    while current != project_path and current != current.parent:
        # Submodules have a .git file (not directory) or .git directory
        if (current / ".git").exists():
            return True
        current = current.parent
    return False


def _should_skip(
    relative_path: Path,
    patterns: list[str],
    project_path: Path | None = None,
    exclude_submodules: bool = False,
) -> bool:
    """Check if path should be skipped based on ALWAYS_SKIP, patterns, or submodules."""
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
    # Check if inside a git submodule (only if flag is set).
    if exclude_submodules and project_path is not None:
        full_path = project_path / relative_path
        if _is_submodule(full_path, project_path):
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


def _find_local_modules(project_path: Path, patterns: list[str], exclude_submodules: bool = False) -> set[str]:
    """Find local module/package names in the project.

    Detects:
    - Directories with __init__.py (packages)
    - Directories with any .py files (namespace packages)
    - All .py files (modules) - anywhere in the project
    """
    local_modules = set()

    # Find top-level packages/directories
    for item in project_path.iterdir():
        # Skip hidden and ignored
        if item.name.startswith(".") or _should_skip(Path(item.name), patterns, project_path, exclude_submodules):
            continue

        if item.is_dir():
            # Check if directory contains any .py files (package or namespace package)
            if any(item.rglob("*.py")):
                local_modules.add(item.name)
        elif item.suffix == ".py" and item.stem != "__init__":
            # Top-level .py file
            local_modules.add(item.stem)

    # Find all .py files anywhere in the project (for intra-package imports)
    for py_file in project_path.rglob("*.py"):
        relative = py_file.relative_to(project_path)
        if _should_skip(relative, patterns, project_path, exclude_submodules):
            continue
        if py_file.stem != "__init__":
            local_modules.add(py_file.stem)

    return local_modules


def _collect_imports(project_path: Path, exclude_submodules: bool = False) -> tuple[set[str], set[str]]:
    """STEP 1: Find all .py files and extract imports.

    Returns:
        (imports, local_modules) where local_modules are the project's own modules.
    """
    patterns = _load_ignore_patterns(project_path)
    imports = set()

    for py_file in project_path.rglob("*.py"):
        relative = py_file.relative_to(project_path)
        if _should_skip(relative, patterns, project_path, exclude_submodules):
            continue
        imports.update(_extract_imports_from_file(py_file))

    local_modules = _find_local_modules(project_path, patterns, exclude_submodules)

    return imports, local_modules


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
# Orphan Detection
# =============================================================================

def _get_package_requires(package_name: str) -> set[str]:
    """Get direct dependencies of a package from metadata.

    Args:
        package_name: Normalized package name (lowercase, underscores).

    Returns:
        Set of normalized dependency package names.
    """
    # Pattern to extract package name from requirement spec
    # Handles: "requests>=2.0", "click", "package[extra]", "pkg; python_version<'3'"
    req_pattern = re.compile(r"^([a-zA-Z0-9_-]+)")

    for dist in distributions():
        name = dist.metadata["Name"]
        if not name:
            continue
        norm = name.lower().replace("-", "_")
        if norm != package_name:
            continue

        requires = dist.requires or []
        deps = set()
        for req in requires:
            # Skip extras-only requirements like "package; extra == 'dev'"
            if "extra ==" in req or "extra==" in req:
                continue
            match = req_pattern.match(req.strip())
            if match:
                deps.add(match.group(1).lower().replace("-", "_"))
        return deps

    return set()


def _build_dependency_tree(
    root_packages: set[str],
    all_packages: dict[str, str],
) -> set[str]:
    """Recursively collect all transitive dependencies.

    Args:
        root_packages: Set of package names that are directly used.
        all_packages: Dict of all installed packages {name: version}.

    Returns:
        Set of all package names in the dependency tree.
    """
    tree = set()
    to_visit = list(root_packages)

    while to_visit:
        pkg = to_visit.pop()
        if pkg in tree:
            continue
        if pkg not in all_packages:
            continue
        tree.add(pkg)
        deps = _get_package_requires(pkg)
        to_visit.extend(deps - tree)

    return tree


# Packages always present in venvs, not useful to report as orphans.
VENV_PACKAGES = {"pip", "setuptools", "wheel", "pkg_resources", "freezeburn"}


def _find_orphans(
    tree: set[str],
    all_packages: dict[str, str],
) -> dict[str, str]:
    """Find installed packages not in dependency tree.

    Returns only "root" orphans - packages that are not dependencies of other
    orphans. For example, if uvicorn is orphan and depends on click, only
    uvicorn is returned (not click).

    Args:
        tree: Set of package names in the dependency tree.
        all_packages: Dict of all installed packages {name: version}.

    Returns:
        Dict of orphan packages {name: version}.
    """
    orphan_names = set(all_packages.keys()) - tree - VENV_PACKAGES

    # Build dependency tree of orphans to find root orphans only
    orphan_deps = set()
    for orphan in orphan_names:
        deps = _get_package_requires(orphan)
        orphan_deps.update(deps)

    # Root orphans = orphans that are not dependencies of other orphans
    root_orphans = orphan_names - orphan_deps
    return {name: all_packages[name] for name in root_orphans}


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
    local_modules: set[str],
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
        # Skip stdlib.
        if imp in stdlib:
            continue

        # Skip local project modules.
        if imp in local_modules:
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
    exclude_submodules: bool = False,
    include_orphans: bool = False,
) -> tuple[list[str], list[str], dict[str, str]]:
    """Generate requirements.txt content.

    Args:
        project_path: Directory to scan.
        warn_missing: Include warnings for unresolved imports.
        exclude_submodules: Skip scanning git submodules.
        include_orphans: Include orphan packages (installed but not in dependency tree).

    Returns:
        (lines, warnings, orphans) where:
        - lines: "package==version" strings
        - warnings: warning messages
        - orphans: dict of orphan packages {name: version}
    """
    # Step 1: Collect imports and local modules.
    imports, local_modules = _collect_imports(project_path, exclude_submodules)

    # Step 2: Collect installed packages.
    packages, import_map, ambiguous = _collect_installed()

    # Step 3: Filter and match.
    requirements, warnings = _match_requirements(
        imports, packages, import_map, ambiguous, local_modules
    )

    # Step 4: Build dependency tree and find orphans.
    tree = _build_dependency_tree(set(requirements.keys()), packages)
    orphans = _find_orphans(tree, packages)

    # Step 5: Optionally include orphans in requirements.
    if include_orphans:
        requirements.update(orphans)

    # Step 6: Format output.
    lines = [f"{pkg}=={ver}" for pkg, ver in sorted(requirements.items())]

    return lines, warnings if warn_missing else [], orphans
