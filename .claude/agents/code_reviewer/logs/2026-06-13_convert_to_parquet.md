# Code Review: `convert_to_parquet.py`

**Reviewed by:** `code_reviewer` agent
**Date:** 2026-06-13
**File:** `cloudecode/.claude/skills/migrate/scripts/convert_to_parquet.py`
**Standards reference:** `cloudecode/.claude/CLAUDE.md`

---

## 1. Script Summary

The script scans a hard-coded relative path (`.\.claude\skills\fetchAPI\data`) for datetime-named sub-folders, selects the lexicographically latest one, converts every CSV file inside it to Parquet using `pandas` + `pyarrow`, and writes the results to a parallel datetime-named folder under `.\.claude\skills\migrate\data`. A short status report is printed for each file converted.

---

## 2. Findings

### Critical

**C-1: Relative paths resolve against the process working directory, not the script location** (lines 91-92)

`r".\.claude\skills\fetchAPI\data"` silently resolves to the wrong location whenever the script is called from a directory other than the project root. Fix: anchor paths to `Path(__file__).resolve()`.

```python
_REPO_ROOT = Path(__file__).resolve().parents[3]
source_base: Path = _REPO_ROOT / ".claude" / "skills" / "fetchAPI" / "data"
output_base: Path = _REPO_ROOT / ".claude" / "skills" / "migrate" / "data"
```

**C-2: Script always exits with code 0 — failures are invisible to callers** (lines 111-114)

Both `except` blocks only print and return normally. Automation sees success even on total failure. Fix: add `import sys` and call `sys.exit(1)` in both except blocks, printing to `sys.stderr`.

**C-3: Per-file conversion errors are silently swallowed** (lines 84-85)

If one CSV fails, the loop continues and the script exits 0. Downstream tools receive a partial Parquet folder but no error signal. Fix: collect failed filenames and raise after the loop.

---

### Major

**M-1: Folder selection uses lexicographic sort, not datetime sort** (line 35)

`max(folders, key=lambda x: x.name)` is correct only while folder names happen to be zero-padded ISO timestamps. Any folder with a non-conforming name (e.g. `backup`, `temp`) silently wins. Fix: parse the name as `datetime`, falling back to `st_mtime`.

```python
from datetime import datetime

def _parse_folder_datetime(folder: Path) -> datetime:
    for fmt in ("%Y-%m-%d_%H-%M-%S", "%Y-%m-%d_%H%M%S", "%Y%m%d_%H%M%S"):
        try:
            return datetime.strptime(folder.name, fmt)
        except ValueError:
            continue
    return datetime.fromtimestamp(folder.stat().st_mtime)

latest_folder = max(folders, key=_parse_folder_datetime)
```

**M-2: No-CSV-files case returns `None` but `main()` prints "Conversion completed successfully!"** (lines 61-63)

The function should raise `FileNotFoundError` so the caller can react correctly instead of reporting false success.

**M-3: `get_latest_folder` returns `str` then the caller immediately wraps it in `Path` again**

Unnecessary `str`/`Path` round-trip. Change the return type to `tuple[str, Path]` and remove the `str()` cast.

---

### Minor

- **m-1:** `main()` lacks a return type annotation (`-> None`). Required by CLAUDE.md.
- **m-2:** `str(e)` inside f-strings is redundant (lines 28, 85, 112-113). Write `f"... {e}"`.
- **m-3:** Module docstring does not mention invocation or required dependencies (PEP 257).
- **m-4:** Raw-string Windows separators (`r".\..."`) are non-portable; resolved by C-1 fix.
- **m-5:** `output_folder.mkdir()` is called before checking whether any CSVs exist, creating empty directories on no-op runs (lines 56, 59-63). Move it after the guard.

---

### Suggestions

- **S-1:** Replace `print` with `logging` for controllable output levels, consistent with `_run_fetch.py`.
- **S-2:** Add `argparse` with a `--dry-run` flag for safe inspection.
- **S-3:** Accept `source_base`/`output_base` as CLI arguments for reusability.
- **S-4:** Declare `pyarrow` explicitly in `requirements.txt` / `pyproject.toml` (CLAUDE.md standard).

---

## 3. Top 3 Priority Fixes

### Priority 1 — Fix path resolution (C-1)

```python
# Before (lines 91-92)
source_base = r".\.claude\skills\fetchAPI\data"
output_base = r".\.claude\skills\migrate\data"

# After
_REPO_ROOT = Path(__file__).resolve().parents[3]
source_base: Path = _REPO_ROOT / ".claude" / "skills" / "fetchAPI" / "data"
output_base: Path = _REPO_ROOT / ".claude" / "skills" / "migrate" / "data"
```

### Priority 2 — Propagate failures via exit code (C-2 + C-3)

```python
# Before (lines 111-114)
    except FileNotFoundError as e:
        print(f"\n[ERROR] {str(e)}")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")

# After
import sys

    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
```

Inside `convert_csv_to_parquet`, collect per-file errors and raise after the loop so `main()` catches them via the outer `except`.

### Priority 3 — Datetime-aware folder selection (M-1)

```python
# Before (line 35)
latest_folder = max(folders, key=lambda x: x.name)

# After
from datetime import datetime

def _parse_folder_datetime(folder: Path) -> datetime:
    """Parse folder name as datetime, falling back to mtime."""
    for fmt in ("%Y-%m-%d_%H-%M-%S", "%Y-%m-%d_%H%M%S", "%Y%m%d_%H%M%S"):
        try:
            return datetime.strptime(folder.name, fmt)
        except ValueError:
            continue
    return datetime.fromtimestamp(folder.stat().st_mtime)

latest_folder = max(folders, key=_parse_folder_datetime)
```
