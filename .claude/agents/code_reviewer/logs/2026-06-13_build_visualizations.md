# Code Review: `build_visualizations.py`

**Reviewed by:** `code_reviewer` agent
**Date:** 2026-06-13
**File:** `cloudecode/.claude/skills/visualize/Scripts/build_visualizations.py`
**Standards reference:** `cloudecode/.claude/CLAUDE.md`

---

## 1. Script Summary

`build_visualizations.py` discovers the latest datetime-stamped Parquet data folder produced by the `migrate` skill, loads all dimension and fact tables into memory, computes six business KPIs, and renders eight Matplotlib/Seaborn charts (four for sales, four for returns) saved as numbered PNG files in a matching output folder. It is invoked as a standalone script via `if __name__ == "__main__"`.

---

## 2. Findings

### Critical

**C-1 — Division by zero in `build_kpis` (lines 43–45)**

`sales["store_sk"].nunique()`, `sales["product_sk"].nunique()`, and `sales["customer_sk"].nunique()` all return `0` when the column exists but is entirely `NaN` or the DataFrame is empty. Dividing `total_sales` by zero produces `inf` (float dtype) or raises `ZeroDivisionError` (int dtype) — either silently corrupts the KPI report.

Fix: introduce a guarded helper:
```python
def _safe_avg(total: float, denominator: int, label: str) -> float:
    """Return total / denominator, raising ValueError when denominator is zero."""
    if denominator == 0:
        raise ValueError(f"Cannot compute average: '{label}' has zero unique values.")
    return total / denominator
```

Then replace the three bare divisions with `_safe_avg(total_sales, sales["store_sk"].nunique(), "store_sk")`, etc.

---

**C-2 — Unguarded `KeyError` on missing tables (lines 33–34, 59–64)**

`tables["fact_sales"]`, `tables["fact_returns"]`, and four dimension tables are accessed with plain dict indexing. If any Parquet file is absent, the script crashes with a cryptic `KeyError`. Fix: validate all required keys upfront in `main()`:

```python
REQUIRED_TABLES = {"fact_sales", "fact_returns", "dim_date", "dim_store", "dim_product", "dim_customer"}

def validate_tables(tables: dict[str, pd.DataFrame]) -> None:
    """Raise ValueError listing all missing tables."""
    missing = REQUIRED_TABLES - tables.keys()
    if missing:
        raise ValueError(f"Missing required tables: {sorted(missing)}")
```

---

### Major

**M-1 — Module-level side effect: `sns.set_theme` runs on import (line 13)**

`sns.set_theme(style="whitegrid")` mutates global Matplotlib `rcParams` whenever this module is imported — even by tests or other scripts. Move it inside `main()` so it only fires during intentional execution.

**M-2 — Relative paths break outside the project root (lines 200–201)**

```python
data_base = r".\.claude\skills\migrate\data"
viz_base  = r".\.claude\skills\visualize\visualizations"
```
These resolve against `os.getcwd()`. Running from any other directory silently produces a wrong path. Fix: anchor to `__file__`:

```python
_SCRIPT_DIR   = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parents[3]
DATA_BASE = _PROJECT_ROOT / ".claude" / "skills" / "migrate" / "data"
VIZ_BASE  = _PROJECT_ROOT / ".claude" / "skills" / "visualize" / "visualizations"
```

**M-3 — Mixed OOP/pyplot API: `plt.xticks()` called while explicit `ax` exists (lines 78, 93, 108, 127, 147, 162, 177, 194)**

Every chart creates `fig, ax = plt.subplots(...)` but then uses `plt.xticks(rotation=...)` (global-state API). These are not reliably equivalent; `plt.xticks` targets `plt.gca()`. Replace with the OOP call:

```python
# Before:
plt.xticks(rotation=45)
# After:
ax.tick_params(axis="x", rotation=45)
```

**M-4 — In-place mutation of a shared input DataFrame (lines 112–114)**

```python
dim_customer["full_name"] = dim_customer["first_name"] + " " + dim_customer["last_name"]
```
This mutates the DataFrame stored in the `tables` dict, permanently altering it for any later caller. Use `.assign()` instead:

```python
dim_customer = tables["dim_customer"].assign(
    full_name=lambda df: df["first_name"] + " " + df["last_name"]
)
```

---

### Minor

- **m-1:** `load_data` has no guard for an empty folder (line 28). An empty dict is returned silently; the first `KeyError` appears deep in `build_kpis`. Add an early check.
- **m-2:** `get_latest_folder` uses lexicographic max on folder names (line 22). Works only with zero-padded ISO 8601 names. Sorting by `st_mtime` is more robust.
- **m-3:** `returns_with_customer` join on `sales_id` is fragile (lines 181–188). If `fact_returns` lacks `sales_id`, all `full_name` values are `NaN`, producing a silent empty chart.
- **m-4:** Docstring hard-codes chart count (line 58): `"Generate and save all 8 charts."` will go stale if charts are added or removed.

---

### Suggestions

- **S-1:** Extract a `_bar_chart(df, x, y, title, output_dir, filename)` helper to reduce `build_visualizations` from ~130 lines to ~40.
- **S-2:** KPIs are printed and discarded. Write them to a JSON sidecar file next to the PNGs for downstream accessibility.
- **S-3:** Replace `print()` calls with stdlib `logging` for log-level control and unattended-run compatibility.

---

## 3. Top 3 Priority Fixes

### Priority 1 — Guard division by zero in `build_kpis` (C-1)

```python
# Before (lines 43–45)
"Avg Sales per Store":    total_sales / sales["store_sk"].nunique(),
"Avg Sales per Product":  total_sales / sales["product_sk"].nunique(),
"Avg Sales per Customer": total_sales / sales["customer_sk"].nunique(),

# After
def _safe_avg(total: float, denominator: int, label: str) -> float:
    """Return total / denominator, raising ValueError when denominator is zero."""
    if denominator == 0:
        raise ValueError(f"Cannot compute average: '{label}' has zero unique values.")
    return total / denominator

"Avg Sales per Store":    _safe_avg(total_sales, sales["store_sk"].nunique(),    "store_sk"),
"Avg Sales per Product":  _safe_avg(total_sales, sales["product_sk"].nunique(),  "product_sk"),
"Avg Sales per Customer": _safe_avg(total_sales, sales["customer_sk"].nunique(), "customer_sk"),
```

### Priority 2 — Anchor paths to `__file__` (M-2)

```python
# Before (lines 200–201)
data_base = r".\.claude\skills\migrate\data"
viz_base  = r".\.claude\skills\visualize\visualizations"

# After
_SCRIPT_DIR   = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parents[3]
DATA_BASE = _PROJECT_ROOT / ".claude" / "skills" / "migrate" / "data"
VIZ_BASE  = _PROJECT_ROOT / ".claude" / "skills" / "visualize" / "visualizations"
```

### Priority 3 — Move `sns.set_theme` inside `main()` (M-1)

```python
# Before (line 13, module level)
sns.set_theme(style="whitegrid")

# After — first line of main()
def main() -> None:
    """Orchestrate KPI computation and chart generation."""
    sns.set_theme(style="whitegrid")
    ...
```
