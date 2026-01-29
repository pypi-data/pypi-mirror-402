# freezeburn

**Freeze what you actually use.**

Generate `requirements.txt` from real imports + installed packages.

## Install

```bash
pip install freezeburn
```

## Usage

```bash
freezeburn                      # Scan current directory
freezeburn /path/to/project     # Scan specific directory
freezeburn -o requirements.txt  # Custom output file
freezeburn -q                   # Suppress warnings
```

## What It Does

1. Scans `.py` files (respects `.gitignore` and `.reqignore`)
2. Extracts imports via AST
3. Detects stdlib dynamically (`sys.stdlib_module_names`)
4. Intersects with installed packages
5. Outputs exact pinned versions

## Ignore Files

Create `.reqignore` for freezeburn-specific exclusions:

```
tests/
scripts/
examples/*.py
```

Uses gitignore syntax. `.gitignore` is also respected.

## How It Works

```
Imports (AST)  +  Installed (env)  =  requirements.txt
     |                  |                    |
   flask              flask==2.3.2      flask==2.3.2
   requests           requests==2.31    requests==2.31
   mymodule           (not installed)   (skipped + warning)
   os                 (stdlib)          (skipped)
```

## Requirements

- Python 3.10+
- Activated virtualenv with your dependencies

## License

GPL-3.0
