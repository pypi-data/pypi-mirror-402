<!-- @import /home/lab/workspace/.claude/CLAUDE.md -->

# Project-Specific Configuration

This file imports workspace-level configuration from `/home/lab/workspace/.claude/CLAUDE.md`.
All workspace rules apply. Project-specific rules below strengthen or extend them.

The workspace `/home/lab/workspace/.claude/` directory contains additional instruction files
(MERMAID.md, NOTEBOOK.md, DATASCIENCE.md, GIT.md, JUPYTERLAB_EXTENSION.md, and others) referenced by CLAUDE.md.
Consult workspace CLAUDE.md and the .claude directory to discover all applicable standards.

## Mandatory Bans (Reinforced)

The following workspace rules are STRICTLY ENFORCED for this project:

- **No automatic git tags** - only create tags when user explicitly requests
- **No automatic version changes** - only modify version in package.json/pyproject.toml/etc. when user explicitly requests
- **No automatic publishing** - never run `make publish`, `npm publish`, `twine upload`, or similar without explicit user request
- **No manual package installs if Makefile exists** - use `make install` or equivalent Makefile targets, not direct `pip install`/`uv install`/`npm install`
- **No automatic git commits or pushes** - only when user explicitly requests

## Project Context

`jupyterlab_server_proxy_launcher_fix` is a JupyterLab 4 extension that fixes issues with jupyter-server-proxy launchers:

- SVG icons not displaying when launchers are in categories other than "Notebook"
- New browser tab settings being ignored, causing proxy to always open in separate tab

**Technology Stack**:

- TypeScript frontend extension
- Python server extension
- JupyterLab 4.0.0+
- Uses copier-based extension template with jupyter-releaser CI/CD

**Build System**:

- Makefile-based workflow - always use `make install`, `make build`, `make test`
- Never use direct `npm install`, `jlpm install`, `pip install` commands

## Strengthened Rules

- Always follow JUPYTERLAB_EXTENSION.md when modifying extension code or CI/CD workflows
- Always commit both `package.json` and `package-lock.json` together when dependencies change
