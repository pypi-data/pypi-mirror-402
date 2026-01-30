"""Configuration loading for launcher section icons.

Loads YAML configuration files following the jupyter_app_launcher pattern.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from jsonschema import ValidationError, validate
from jupyter_core.paths import jupyter_path

logger = logging.getLogger(__name__)


# Configuration file patterns
CONFIG_PATTERNS = ["*.yaml", "*.yml"]
CONFIG_DIR = "jupyter_launcher_sections"


def get_schema() -> Dict:
    """Load the JSON schema for config validation."""
    schema_path = Path(__file__).parent / "schema" / "config.schema.json"
    with open(schema_path, "r") as f:
        return json.load(f)


def get_config_paths() -> List[Path]:
    """Return config directories to search for configuration files.

    Searches:
    - All jupyter data directories
    - Current working directory
    - JUPYTER_LAUNCHER_SECTION_ICONS_PATH environment variable
    """
    paths = []

    # Jupyter data directories
    for jp in jupyter_path():
        config_dir = Path(jp) / CONFIG_DIR
        if config_dir.is_dir():
            paths.append(config_dir)

    # Current working directory
    cwd_config = Path.cwd() / CONFIG_DIR
    if cwd_config.is_dir():
        paths.append(cwd_config)

    # Environment variable override
    env_path = os.environ.get("JUPYTER_LAUNCHER_SECTION_ICONS_PATH")
    if env_path:
        env_config = Path(env_path)
        if env_config.is_dir():
            paths.append(env_config)

    return paths


def path_to_svg(icon_path: str, cwd: Path) -> Optional[str]:
    """Read SVG file content from path.

    Args:
        icon_path: Path to SVG file (relative to cwd or absolute)
        cwd: Current working directory for relative paths

    Returns:
        SVG content as string, or None if file not found/readable
    """
    if not icon_path:
        return None

    # Resolve path
    path = Path(icon_path)
    if not path.is_absolute():
        path = cwd / icon_path

    # Read SVG content
    try:
        if path.exists() and path.suffix.lower() == ".svg":
            logger.debug(f"Found SVG icon: {path}")
            return path.read_text(encoding="utf-8")
        else:
            logger.debug(f"SVG icon not found: {path}")
    except (IOError, OSError) as e:
        logger.debug(f"Error reading SVG icon {path}: {e}")

    return None


def parse_config(config_path: Path, schema: Dict) -> List[Dict]:
    """Parse and validate a YAML config file.

    Args:
        config_path: Path to the YAML config file
        schema: JSON schema for validation

    Returns:
        List of section configuration dictionaries with resolved SVG content
    """
    configs = []
    logger.debug(f"Loading config file: {config_path}")

    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, IOError) as e:
        logger.debug(f"Error loading config file {config_path}: {e}")
        return []

    if not isinstance(data, list):
        return []

    config_dir = config_path.parent

    for item in data:
        if not isinstance(item, dict):
            continue

        # Validate against schema
        try:
            validate(instance=item, schema=schema)
        except ValidationError:
            continue

        # Build config entry
        entry = {"section": item["section"]}

        # Resolve icon path to SVG content
        if "icon" in item and item["icon"]:
            svg_content = path_to_svg(item["icon"], config_dir)
            if svg_content:
                entry["icon"] = svg_content

        # Copy tooltip if present
        if "tooltip" in item:
            entry["tooltip"] = item["tooltip"]

        configs.append(entry)

    return configs


def load_all_configs() -> List[Dict]:
    """Load all section icon configurations from all config paths.

    Returns:
        List of section configuration dictionaries
    """
    schema = get_schema()
    configs = []
    seen_sections = set()

    config_paths = get_config_paths()
    logger.debug(f"Searching for configs in: {config_paths}")

    for config_dir in config_paths:
        # Find all matching config files across all patterns
        config_files = []
        for pattern in CONFIG_PATTERNS:
            config_files.extend(config_dir.glob(pattern))

        for config_file in sorted(set(config_files)):
            for config in parse_config(config_file, schema):
                section = config["section"]
                # First config wins for duplicate sections
                if section not in seen_sections:
                    configs.append(config)
                    seen_sections.add(section)
                    logger.debug(f"Loaded section config: {section}")

    logger.debug(f"Total section configs loaded: {len(configs)}")
    return configs
