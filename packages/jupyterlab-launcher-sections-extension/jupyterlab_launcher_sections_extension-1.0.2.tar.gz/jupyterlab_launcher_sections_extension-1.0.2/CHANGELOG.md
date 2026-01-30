# Changelog

<!-- <START NEW CHANGELOG ENTRY> -->

## 1.0.1

Initial public release.

### Features

- YAML-based configuration for launcher section icons
- Load configs from `{jupyter_data_dir}/jupyter_launcher_sections/*.yaml` or `*.yml`
- JSON schema validation for configuration files
- SVG icon support with relative or absolute paths
- Custom tooltips for launcher sections
- MutationObserver-based icon replacement for dynamic launcher content

### Configuration

Create YAML files in `jupyter_launcher_sections/` directory:

```yaml
- section: 'Services'
  icon: 'services.svg'
  tooltip: 'Supporting services for data science'
```

<!-- <END NEW CHANGELOG ENTRY> -->
