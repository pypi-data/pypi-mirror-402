"""Configuration loading and saving utilities."""

from __future__ import annotations

from pathlib import Path

import yaml

from red9.config.schema import Red9Config


def ensure_red9_dir(project_root: Path) -> Path:
    """Ensure the .red9 directory exists.

    Args:
        project_root: Root directory of the project.

    Returns:
        Path to the .red9 directory.
    """
    red9_dir = project_root / ".red9"
    red9_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (red9_dir / "embeddings").mkdir(exist_ok=True)
    (red9_dir / "backups").mkdir(exist_ok=True)

    return red9_dir


def load_config(project_root: Path) -> Red9Config:
    """Load RED9 configuration from .red9/config.yaml.

    If the config file doesn't exist, returns default configuration.

    Args:
        project_root: Root directory of the project.

    Returns:
        RED9 configuration.
    """
    config_path = project_root / ".red9" / "config.yaml"

    if not config_path.exists():
        return Red9Config()

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    return Red9Config.model_validate(data)


def save_config(config: Red9Config, project_root: Path) -> Path:
    """Save RED9 configuration to .red9/config.yaml.

    Args:
        config: Configuration to save.
        project_root: Root directory of the project.

    Returns:
        Path to the saved config file.
    """
    red9_dir = ensure_red9_dir(project_root)
    config_path = red9_dir / "config.yaml"

    # Convert to dict for YAML serialization
    data = config.model_dump(exclude_defaults=False)

    # Add header comment
    yaml_content = "# RED9 Configuration\n"
    yaml_content += "# See CLAUDE.md for full schema documentation\n\n"
    yaml_content += yaml.dump(data, default_flow_style=False, sort_keys=False)

    config_path.write_text(yaml_content)
    return config_path


def config_exists(project_root: Path) -> bool:
    """Check if RED9 has been initialized in this project.

    Args:
        project_root: Root directory of the project.

    Returns:
        True if .red9/config.yaml exists.
    """
    return (project_root / ".red9" / "config.yaml").exists()


def get_project_root() -> Path:
    """Get the project root directory.

    Walks up from current directory looking for .red9/ or .git/.

    Returns:
        Project root directory, or current directory if not found.
    """
    current = Path.cwd()

    for parent in [current, *current.parents]:
        if (parent / ".red9").exists():
            return parent
        if (parent / ".git").exists():
            return parent

    return current
