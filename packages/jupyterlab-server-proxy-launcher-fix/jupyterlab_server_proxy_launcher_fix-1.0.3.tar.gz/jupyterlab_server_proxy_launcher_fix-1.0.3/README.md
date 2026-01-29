# jupyterlab_server_proxy_launcher_fix

[![GitHub Actions](https://github.com/stellarshenson/jupyterlab_server_proxy_launcher_fix/actions/workflows/build.yml/badge.svg)](https://github.com/stellarshenson/jupyterlab_server_proxy_launcher_fix/actions/workflows/build.yml)
[![npm version](https://img.shields.io/npm/v/jupyterlab_server_proxy_launcher_fix.svg)](https://www.npmjs.com/package/jupyterlab_server_proxy_launcher_fix)
[![PyPI version](https://img.shields.io/pypi/v/jupyterlab-server-proxy-launcher-fix.svg)](https://pypi.org/project/jupyterlab-server-proxy-launcher-fix/)
[![Total PyPI downloads](https://static.pepy.tech/badge/jupyterlab-server-proxy-launcher-fix)](https://pepy.tech/project/jupyterlab-server-proxy-launcher-fix)
[![JupyterLab 4](https://img.shields.io/badge/JupyterLab-4-orange.svg)](https://jupyterlab.readthedocs.io/en/stable/)
[![Brought To You By KOLOMOLO](https://img.shields.io/badge/Brought%20To%20You%20By-KOLOMOLO-00ffff?style=flat)](https://kolomolo.com)
[![Donate PayPal](https://img.shields.io/badge/Donate-PayPal-blue?style=flat)](https://www.paypal.com/donate/?hosted_button_id=B4KPBJDLLXTSA)

JupyterLab extension that fixes SVG icon display for [jupyter-server-proxy](https://github.com/jupyterhub/jupyter-server-proxy) launchers when placed in custom categories other than "Notebook" or "Console".

> [!WARNING]
> This extension is a temporary fix for [jupyterhub/jupyter-server-proxy](https://github.com/jupyterhub/jupyter-server-proxy). Once the upstream project implements proper icon support for custom launcher categories, this extension will be deprecated. We look forward to our own obsolescence.

## The Problem

When configuring jupyter-server-proxy launchers with custom categories (e.g., "Services", "Tools"), SVG icons fail to display. This happens because JupyterLab's launcher widget handles icons differently based on category:

- **Notebook/Console categories**: Uses `kernelIconUrl` property - works correctly
- **Other categories**: Calls `commands.icon(command, args)` to get the icon - server-proxy's `server-proxy:open` command doesn't define an `icon` property, so icons are missing

## The Fix

This extension wraps JupyterLab's `commands.icon()` method to intercept calls for the `server-proxy:open` command and return pre-cached LabIcon instances.

**How it works**:

- Fetches server-proxy configuration from `/server-proxy/servers-info` endpoint
- Pre-fetches SVG icons and creates LabIcon instances for non-kernel categories
- Wraps `app.commands.icon()` to return cached icons when command is `server-proxy:open`
- Matches icons by `args.title` (handles both plain titles and titles with ` [↗]` suffix for `new_browser_tab: true`)

**Implementation details**:

- **No command override**: Preserves server-proxy's original `execute` function completely
- **No timing issues**: Wrapper intercepts all calls regardless of extension load order
- **No private API access**: Uses public method wrapping instead of accessing internal `_commands` Map
- **Non-destructive**: Original behavior preserved for all other commands

## Fix Implementation Details

The extension consists of frontend TypeScript code that wraps the commands registry icon method.

**Frontend Implementation** (`src/index.ts`):

- **Icon Caching**: Fetches server info, creates LabIcon from `icon_url` for each non-kernel category launcher, caches by title
- **Title Matching**: Caches icons under both plain title and `${title} [↗]` suffix (server-proxy appends this when `new_browser_tab: true`)
- **Method Wrapping**: `const originalIcon = app.commands.icon.bind(app.commands)` preserves original, then `(app.commands as any).icon = ...` installs wrapper
- **Conditional Return**: If `id === 'server-proxy:open'` and `args.title` matches cache key, returns cached LabIcon; otherwise delegates to original

**Icon Utilities** (`src/iconUtils.ts`):

- **SVG Fetching**: `fetchSvgIcon(url, name)` fetches SVG content and creates LabIcon instance
- **Fallback Icons**: `createTextIcon(name, title)` generates simple SVG with first letter when icon_url unavailable

## Requirements

- JupyterLab >= 4.0.0
- [jupyter-server-proxy](https://github.com/jupyterhub/jupyter-server-proxy) installed and configured

## Install

To install the extension, execute:

```bash
pip install jupyterlab_server_proxy_launcher_fix
```

## Uninstall

To remove the extension, execute:

```bash
pip uninstall jupyterlab_server_proxy_launcher_fix
```
