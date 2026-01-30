# jupyterlab_launcher_sections_extension

[![GitHub Actions](https://github.com/stellarshenson/jupyterlab_launcher_sections_extension/actions/workflows/build.yml/badge.svg)](https://github.com/stellarshenson/jupyterlab_launcher_sections_extension/actions/workflows/build.yml)
[![npm version](https://img.shields.io/npm/v/jupyterlab_launcher_sections_extension.svg)](https://www.npmjs.com/package/jupyterlab_launcher_sections_extension)
[![PyPI version](https://img.shields.io/pypi/v/jupyterlab-launcher-sections-extension.svg)](https://pypi.org/project/jupyterlab-launcher-sections-extension/)
[![Total PyPI downloads](https://static.pepy.tech/badge/jupyterlab-launcher-sections-extension)](https://pepy.tech/project/jupyterlab-launcher-sections-extension)
[![JupyterLab 4](https://img.shields.io/badge/JupyterLab-4-orange.svg)](https://jupyterlab.readthedocs.io/en/stable/)
[![Brought To You By KOLOMOLO](https://img.shields.io/badge/Brought%20To%20You%20By-KOLOMOLO-00ffff?style=flat)](https://kolomolo.com)
[![Donate PayPal](https://img.shields.io/badge/Donate-PayPal-blue?style=flat)](https://www.paypal.com/donate/?hosted_button_id=B4KPBJDLLXTSA)

Customize your JupyterLab launcher with section-specific icons. This extension allows you to set custom icons for different launcher sections, making it easier to visually distinguish between categories of notebooks and other items.

## Features

- **Custom section icons** - Set unique icons for each launcher section (Notebooks, Console, Other, etc.)
- **Server-side configuration** - Configure icons through Jupyter server settings
- **Visual organization** - Improve launcher usability with distinctive section markers

## Requirements

- JupyterLab >= 4.0.0

## Installation

```bash
pip install jupyterlab_launcher_sections_extension
```

For development installation, use:

```bash
make install
```

## Configuration

Create YAML configuration files in `{jupyter_data_dir}/jupyter_launcher_sections/` directory. Each file can contain one or more section configurations.

**Example** (`services.yml`):

```yaml
- section: 'Services'
  icon: 'services.svg'
  tooltip: 'Supporting services for data science and environment management'

- section: 'Notebook'
  icon: 'notebook-custom.svg'
  tooltip: 'Create a new Jupyter Notebook'
```

**Configuration options**:

- `section` (required) - Name of the launcher section to customize
- `icon` (optional) - Path to SVG icon file (relative to config directory or absolute)
- `tooltip` (optional) - Tooltip text shown on hover

Place SVG icon files in the same directory as the YAML configuration or specify absolute paths.

## Uninstall

```bash
pip uninstall jupyterlab_launcher_sections_extension
```
