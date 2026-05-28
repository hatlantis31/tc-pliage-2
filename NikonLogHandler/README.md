# Nikon Log Handler – Refactored Framework

> **Nikon Confidential – Internal Use Only**

This repository contains the refactored NLH framework, separated into:
- **Core framework** (no parsers) in `framework/`
- **Subsidiary-specific scripts** in `subsidiaries/NPE/`, `NPI/`, `NPC/`
- **Developer kit** in `dev_kit/`
- **Utility tools** in `tools/`
- **Bug / issue tracker** in `bug_tracker/`

---

## Repository Structure

```
NikonLogHandler/
├── framework/                   Core NLH application (no parsers)
│   ├── main_app_files/          GUI, core logic, SharePoint, XML handler
│   ├── analysis_files/          General utilities, templates, tool files
│   ├── image_files/             App icons and images
│   ├── CD/                      Build and packaging scripts
│   ├── __main__.py              Application entry point
│   ├── NikonLogHandler.XML      App configuration
│   └── requirements.txt         Python dependencies
│
├── subsidiaries/
│   ├── NPE/                     Nikon Precision Europe
│   │   ├── scripts/             Parser scripts (.py / .pyenc)
│   │   └── docs/                Parser documentation (PDF / DOCX)
│   ├── NPI/                     Nikon Precision Inc.
│   │   ├── scripts/
│   │   └── docs/
│   └── NPC/                     Nikon Precision Corporation
│       ├── scripts/
│       └── docs/
│
├── dev_kit/
│   ├── HOW_TO_ADD_A_PARSER.md   Step-by-step parser development guide
│   ├── test_handler.py          Validate parser scripts locally
│   ├── templates/
│   │   └── template_log_handler.py   Parser template
│   └── examples/                Reference parser examples
│
├── tools/
│   ├── script_downloader.py     Download/sync scripts from SharePoint
│   ├── script_encryptor.py      Encrypt/decrypt parser scripts (Fernet)
│   ├── gitea_setup.py           Create subsidiary repos on Gitea
│   └── pdf_to_word.py           Convert PDF docs to Word
│
└── bug_tracker/
    ├── tracker.py               JSON-based issue tracker CLI
    ├── issues.json              Issue database (auto-created)
    └── templates/
        ├── bug_report.md
        ├── parser_request.md
        ├── feature_request.md
        └── improvement.md
```

---

## Quick Start

### Install dependencies
```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r framework/requirements.txt
pip install cryptography requests pdfplumber python-docx   # tool extras
```

### Run the application
```bash
cd framework
python __main__.py
```

### Sync parser scripts for your subsidiary
```bash
python tools/script_downloader.py --subsidiary NPE
```

### Add a new parser
See [dev_kit/HOW_TO_ADD_A_PARSER.md](dev_kit/HOW_TO_ADD_A_PARSER.md)

### Encrypt scripts for distribution
```bash
python tools/script_encryptor.py keygen           # generate key
python tools/script_encryptor.py encrypt-all NPE --key <key>
```

### Set up Gitea repositories
```bash
python tools/gitea_setup.py create-all \
    --gitea-url http://npe-apgit01.nikonoa.net \
    --token <your-pat>
```

### Report a bug or request a parser
```bash
python bug_tracker/tracker.py new bug
python bug_tracker/tracker.py new parser-request
python bug_tracker/tracker.py list --status open
```

---

## Subsidiary Script Repos (Gitea)

| Subsidiary | Repository |
|-----------|-----------|
| NPE | `NLH-Scripts-NPE` |
| NPI | `NLH-Scripts-NPI` |
| NPC | `NLH-Scripts-NPC` |

Each subsidiary has its own repo so scripts can be scoped per organisation.

---

## Key Architectural Changes vs. v2.x

| Old | New |
|-----|-----|
| Parsers bundled in the main repo | Parsers in separate subsidiary repos |
| Manual script placement | `script_downloader.py` syncs from SharePoint |
| No encryption | Fernet encryption via `script_encryptor.py` |
| No formal dev process | Dev kit with templates, tests, and guide |
| Issues via email only | `bug_tracker/tracker.py` + Gitea issue templates |
| PDF-only documentation | PDF → Word converter included |

---

## Contact

NLH Team: nlh-team.npe@nikonglobal.onmicrosoft.com
