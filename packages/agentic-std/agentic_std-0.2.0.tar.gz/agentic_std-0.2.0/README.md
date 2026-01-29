# Agentic Coding Standard CLI

**Agentic Coding Standard CLI** — Scaffold `.agent/` directories for AI-ready codebases.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

## Why?

AI coding agents (Cursor, Windsurf, GitHub Copilot) work best when they have immediate context about your project's standards, conventions, and goals. The `.agent/` directory provides this context in a standardized format.

## Installation

### Quick Install (Recommended)

**Windows (PowerShell as Admin):**
```powershell
irm https://raw.githubusercontent.com/Alaa-Taieb/agentic-std/main/install.ps1 | iex
```

**macOS/Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/Alaa-Taieb/agentic-std/main/install.sh | bash
```

### Via pip

```bash
pip install agentic-std
```

> **Note:** If using pip directly, ensure Python's Scripts directory is in your PATH.

## Usage

### Initialize a project

```bash
acs init
```

This creates a `.agent/` directory with:

| File | Purpose |
|------|---------|
| `blueprint.md` | Project vision, personas, MVP features |
| `rules.md` | Tech stack, naming conventions, verification steps |
| `vibe-guide.md` | Brand voice, visual language |
| `journal.md` | Decision log |

### Force overwrite

```bash
acs init --force
```

### Update templates

```bash
acs update
```

Fetches the latest templates from GitHub and caches them in `~/.acs/templates/`.

### Check version

```bash
acs --version
```

## The Standard

This CLI implements the [Agentic Coding Standard](https://github.com/Alaa-Taieb/agentic-coding-standard) — a set of documentation conventions for AI-agent-ready codebases.

## License

MIT
