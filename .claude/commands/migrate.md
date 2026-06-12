---
description: Converts CSV files from the latest fetchAPI data folder to Parquet format. Use when you want to migrate fetched CSV data to Parquet in .claude/skills/migrate/data/.
---

Migrate the fetched CSV data to Parquet format by following these steps:

## Step 1: Select the Python environment

Use the `.venv` environment at `C:\ClaudeCode\.venv`. Run Python as:
`C:\ClaudeCode\.venv\Scripts\python.exe`

## Step 2: Run the migration script

Execute the script at `.claude/skills/migrate/scripts/convert_to_parquet.py`:

```
C:\ClaudeCode\.venv\Scripts\python.exe .claude/skills/migrate/scripts/convert_to_parquet.py
```

The script will:
- Find the latest datetime-named folder in `.claude/skills/fetchAPI/data/`
- Convert all CSV files in that folder to Parquet format
- Save the converted files to `.claude/skills/migrate/data/` under the same datetime folder name
- Report file sizes and any errors encountered
