from pathlib import Path

import yaml

from .config import get_config_path


def get_aliases_file_path(alias_type: str = "env") -> Path:
    """Get the path to the aliases file.

    Args:
        alias_type: Type of aliases ('env' or 'tenant')
    """
    config_dir = get_config_path()
    if alias_type == "tenant":
        return config_dir / "tenant_aliases.yaml"
    return config_dir / "env_aliases.yaml"


def load_aliases(alias_type: str = "env") -> dict[str, str]:
    """Load aliases from the aliases file.

    Args:
        alias_type: Type of aliases ('env' or 'tenant')

    Returns:
        Dictionary mapping alias -> name
    """
    aliases_path = get_aliases_file_path(alias_type)

    if not aliases_path.exists():
        return {}

    with open(aliases_path, "r") as f:
        aliases = yaml.safe_load(f)
        return aliases if aliases else {}


def save_aliases(aliases: dict[str, str], alias_type: str = "env") -> None:
    """Save aliases to the aliases file.

    Args:
        aliases: Dictionary mapping alias -> name
        alias_type: Type of aliases ('env' or 'tenant')
    """
    aliases_path = get_aliases_file_path(alias_type)

    # Ensure config directory exists
    aliases_path.parent.mkdir(parents=True, exist_ok=True)

    with open(aliases_path, "w") as f:
        yaml.dump(aliases, f, default_flow_style=False, sort_keys=True)


def resolve_env_alias(name_or_alias: str) -> str:
    """Resolve an alias to its environment name, or return the input if not an alias.

    Args:
        name_or_alias: Either an alias or an actual environment name

    Returns:
        The resolved environment name
    """
    aliases = load_aliases("env")
    return aliases.get(name_or_alias, name_or_alias)


def resolve_tenant_alias(name_or_alias: str) -> str:
    """Resolve an alias to its tenant name, or return the input if not an alias.

    Args:
        name_or_alias: Either an alias or an actual tenant name

    Returns:
        The resolved tenant name
    """
    aliases = load_aliases("tenant")
    return aliases.get(name_or_alias, name_or_alias)


def set_alias(alias: str, name: str, alias_type: str = "env") -> None:
    """Set an alias for a name.

    Args:
        alias: The alias to set
        name: The actual name
        alias_type: Type of aliases ('env' or 'tenant')
    """
    aliases = load_aliases(alias_type)
    aliases[alias] = name
    save_aliases(aliases, alias_type)


def remove_alias(alias: str, alias_type: str = "env") -> bool:
    """Remove an alias.

    Args:
        alias: The alias to remove
        alias_type: Type of aliases ('env' or 'tenant')

    Returns:
        True if alias was removed, False if it didn't exist
    """
    aliases = load_aliases(alias_type)
    if alias in aliases:
        del aliases[alias]
        save_aliases(aliases, alias_type)
        return True
    return False
