# How to Add a New NLH Parser (Log Handler)

> **Audience:** Engineers who want to add a new log parser to the Nikon Log Handler (NLH).
> **Prerequisite:** Python 3.10+ and the NLH dev kit set up (see [Dev Kit Setup](#dev-kit-setup)).

---

## Table of Contents

1. [Overview](#overview)
2. [Dev Kit Setup](#dev-kit-setup)
3. [Step-by-Step Guide](#step-by-step-guide)
4. [File Naming Rules](#file-naming-rules)
5. [LogHandlerParameters Reference](#loghandlerparameters-reference)
6. [Required and Optional Methods](#required-and-optional-methods)
7. [Testing Your Parser](#testing-your-parser)
8. [Documentation Requirements](#documentation-requirements)
9. [Submitting Your Parser](#submitting-your-parser)
10. [Common Mistakes](#common-mistakes)
11. [FAQ](#faq)

---

## Overview

NLH uses a **plugin discovery** system. Every parser is a standalone `.py` file that
lives in a subsidiary's `scripts/` folder. At startup, NLH scans that folder, loads
each file, validates it, and registers it automatically — no code changes to NLH itself.

```
subsidiaries/
└── NPE/
    └── scripts/
        └── my_machine_log_handler.py   ← your new parser
```

---

## Dev Kit Setup

```bash
# 1. Clone the NLH repository
git clone http://npe-apgit01.nikonoa.net/NPE-ES-Hardware/Nikon_Log_Handler.git
cd Nikon_Log_Handler

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 3. Install dependencies
pip install -r framework/requirements.txt

# 4. Copy the handler template to your subsidiary
copy dev_kit\templates\template_log_handler.py subsidiaries\NPE\scripts\my_machine_log_handler.py
```

---

## Step-by-Step Guide

### Step 1 – Name your file

Pick a file name that follows the naming rule:

```
<sanitised_handler_name>_log_handler.py
```

Where `<sanitised_handler_name>` is the handler's display name lowercased with all
non-word characters replaced by underscores.

**Example:** handler name `"X6 CT SL Trace"` → file name `x6_ct_sl_trace_log_handler.py`

### Step 2 – Fill in `LogHandlerParameters`

Open your copy of the template and update `handler_parameters`:

```python
handler_parameters = LogHandlerParameters(
    log_handler_name="X6 CT SL Trace",       # Display name in UI (must match filename rule)
    version="1.0.0",                          # x.y.z format
    log_pattern=r"CT_SL_Trace.*\.log",        # Regex to match log filenames
    description="Parses X6 CT SL trace logs from the NSR.",
    supported_machine_types=["X6"],
    supported_logs=["CT_SL_Trace_20240101.log"],
    logs_locations=[r"C:\Nikon\Logs\CT_SL"],
    log_handler_group="X6",                   # Sidebar group label
    analysis_options={
        "Plot Trace":   "plot_trace",          # Button label → method name
        "Export CSV":   "export_csv",
    },
    save_method="csv",                         # "csv" | "excel" | "mesr"
)
```

### Step 3 – Implement `parser()`

This is the only **mandatory** method. It receives a single log file path and must
return a `pandas.DataFrame`.

```python
@classmethod
def parser(cls, file_location: str, **kwargs) -> DataFrame:
    df = read_table(file_location, sep='\t', skiprows=2, encoding='utf-8')
    # Rename / clean columns as needed
    df.columns = [c.strip() for c in df.columns]
    return df
```

**Rules:**
- Must return a `DataFrame` (may be empty, never `None`).
- Do **not** modify global state.
- Raise a descriptive `Exception` if the file cannot be parsed.

### Step 4 – Implement optional methods

| Method | Purpose |
|--------|---------|
| `join_tables(data_tables, **kwargs)` | Merge multiple parsed DataFrames (e.g. date-sorted concat) |
| `<your_analysis_method>(gui_container, file_name, data)` | Custom analysis triggered by UI button |

Each method name in `analysis_options` **must** exist as a `@classmethod` on your class.

### Step 5 – Test locally

```bash
# Run the NLH test runner against your handler
python -m pytest dev_kit/test_handler.py --handler my_machine_log_handler --log <path_to_test_log>

# Or use the built-in CD test suite
python framework/CD/test_parsers.py
```

### Step 6 – Write documentation

Create `subsidiaries/NPE/docs/<your_handler_name>.docx` using the template at
`dev_kit/templates/parser_documentation_template.docx`.

Required sections: Overview, Supported Machines, Log Location, Log Format,
Analysis Options, Known Limitations, Version History.

### Step 7 – Submit

Open a Pull Request on Gitea using the **Parser Request** issue template.
Attach your `.py` file and documentation.

---

## File Naming Rules

| Rule | Example |
|------|---------|
| All lowercase | ✅ `x6_ct_log_handler.py`  ❌ `X6_CT_Log_Handler.py` |
| End with `_log_handler` | ✅ `x6_ct_log_handler.py`  ❌ `x6_ct_handler.py` |
| Match display name | Name `"X6 CT"` → file `x6_ct_log_handler.py` |
| No spaces in filename | ✅ `x6_ct_log_handler.py`  ❌ `x6 ct log handler.py` |

---

## LogHandlerParameters Reference

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `log_handler_name` | `str` | ✅ | Display name. Drives filename rule. |
| `version` | `str` | ✅ | Format `"x.y.z"` (integers only) |
| `log_pattern` | `str` | ✅ | Regex for matching log filenames |
| `description` | `str` | ✅ | One-line description shown in UI |
| `supported_machine_types` | `list[str]` | ✅ | e.g. `["X6", "X8"]` |
| `supported_logs` | `list[str]` | ✅ | Example log file names |
| `logs_locations` | `list[str]` | ✅ | Where these logs live on the tool |
| `log_handler_group` | `str` | ✅ | Sidebar group label |
| `analysis_options` | `dict[str,str]` | ⚠️ | Required if `show_data_table="no"` |
| `save_method` | `str` | optional | `"csv"` (default), `"excel"`, `"mesr"` |
| `show_data_table` | `str` | optional | `"yes"` (default) or `"no"` |

---

## Required and Optional Methods

```python
class MyHandler(LogHandlerBaseClass):
    handler_parameters = LogHandlerParameters(...)

    # ── REQUIRED ──────────────────────────────────────────────────────────
    @classmethod
    def parser(cls, file_location: str, **kwargs) -> DataFrame:
        ...

    # ── OPTIONAL ──────────────────────────────────────────────────────────
    @classmethod
    def join_tables(cls, data_tables: dict, **kwargs) -> dict[str, DataFrame]:
        # Called after all files are parsed. Default: no joining.
        ...

    @classmethod
    def my_custom_action(cls, gui_container, file_name: str, data: DataFrame):
        # Must be listed in analysis_options. Called when user clicks the button.
        ...

    def __init__(self, **kwargs):
        super().__init__(**kwargs)   # Always call super().__init__
```

---

## Testing Your Parser

The dev kit includes a test harness at `dev_kit/test_handler.py`:

```python
# Quick smoke test
from dev_kit.test_handler import HandlerTester
tester = HandlerTester("subsidiaries/NPE/scripts/my_machine_log_handler.py")
tester.run("path/to/test.log")
```

The test checks:
- File naming compliance
- `LogHandlerParameters` validation
- `parser()` returns a non-empty `DataFrame`
- All `analysis_options` methods exist on the class

---

## Documentation Requirements

Every parser **must** have a matching `.docx` documentation file in the
`docs/` folder of its subsidiary. Use the template:

```
dev_kit/templates/parser_documentation_template.docx
```

Required sections:
1. **Overview** – what the parser does and why
2. **Supported Machines** – which NSR/tool types
3. **Log Location** – path on the machine where the log is found
4. **Log Format** – example lines from the log (anonymised)
5. **Analysis Options** – description of each button/action
6. **Known Limitations** – things the parser does NOT handle
7. **Version History** – date + change + author for each version

---

## Submitting Your Parser

1. Push your branch to the subsidiary Gitea repo (`NLH-Scripts-NPE`, etc.)
2. Open a Pull Request using the **Parser Request** template
3. Tag `@nlh-team` for review
4. After approval, the NLH team will encrypt and deploy the script

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| `handler_name` doesn't match filename | Read the [File Naming Rules](#file-naming-rules) |
| `parser()` returns `None` instead of `DataFrame` | Always return `DataFrame()` on failure |
| `analysis_options` lists a method that doesn't exist | Check spelling; method must be a `@classmethod` |
| Version format wrong | Must be `"x.y.z"` e.g. `"1.0.0"` not `"1.0"` |
| Missing `super().__init__()` in `__init__` | Always call `super().__init__(**kwargs)` |
| Importing from `main_app_files` with wrong relative path | Use the exact import shown in the template |

---

## FAQ

**Q: Can my parser handle multiple log files at once?**  
A: Yes — `parser()` is called once per file. Implement `join_tables()` to merge the results.

**Q: Can I use third-party libraries?**  
A: Yes, but they must be added to `requirements.txt` and approved by the NLH team.

**Q: How do I handle logs with different versions/formats?**  
A: Detect the format inside `parser()` and branch accordingly. Use `skiprows`, column detection, etc.

**Q: Can I ship encrypted scripts?**  
A: Yes — use `tools/script_encryptor.py` to encrypt before distribution. The NLH framework  
supports `.pyenc` files via `EncryptedPluginLoader`.

**Q: My parser needs SharePoint data, not just local files. Is that supported?**  
A: Use a Tool (see `template_nikon_tool.py`) rather than a log handler for interactive SharePoint workflows.
