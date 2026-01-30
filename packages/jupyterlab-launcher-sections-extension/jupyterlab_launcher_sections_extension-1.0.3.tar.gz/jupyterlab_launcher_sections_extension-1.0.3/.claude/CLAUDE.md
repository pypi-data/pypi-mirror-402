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
- **No automatic version changes** - only modify version in package.json/pyproject.toml when user explicitly requests
- **No automatic publishing** - never run `make publish`, `npm publish`, `twine upload` without explicit user request
- **No manual package installs** - use `make install` target, not direct `pip install`/`npm install`/`jlpm install`/`yarn install`
- **No automatic git commits or pushes** - only when user explicitly requests

## Project Context

**Name**: jupyterlab_launcher_sections_extension
**Type**: JupyterLab 4.x extension (frontend + server)
**Version**: 0.1.0

A JupyterLab extension that allows setting section-specific icons for the launcher. The extension consists of:

- TypeScript frontend plugin (`src/index.ts`)
- Python server extension (`jupyterlab_launcher_sections_extension/`)
- Standard JupyterLab extension build tooling

**Technology Stack**:

- TypeScript for frontend extension
- Python for server extension
- JupyterLab 4.0.0+ APIs
- jlpm (yarn) for JavaScript dependencies
- pip/setuptools for Python packaging

**Development Commands**:

- `make install` - Build and install the extension
- `make build` - Build packages
- `make test` - Run tests
- `make clean` - Clean build artifacts
- `make publish` - Publish to npm and PyPI (requires explicit user request)

## Strengthened Rules

- Always use `make install` for development installation, never raw `pip install` or `jlpm install`
- Follow JUPYTERLAB_EXTENSION.md for extension development patterns
- Test both frontend and server components before considering work complete
