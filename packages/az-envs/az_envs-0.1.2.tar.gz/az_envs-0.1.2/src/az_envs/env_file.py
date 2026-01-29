"""Generate .env files from secrets."""

from pathlib import Path


def normalize_key_name(name: str) -> str:
    """Convert Key Vault secret name to .env variable format.

    Azure Key Vault names use hyphens, but .env files typically use
    uppercase with underscores.
    """
    return name.replace("-", "_").upper()


def format_env_line(key: str, value: str, normalize: bool = True) -> str:
    """Format a single .env line with proper escaping."""
    if normalize:
        key = normalize_key_name(key)

    if value is None:
        value = ""

    needs_quotes = any(c in value for c in [" ", '"', "'", "\n", "#", "$"])
    if needs_quotes:
        escaped_value = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'{key}="{escaped_value}"'

    return f"{key}={value}"


def generate_env_content(
    secrets: dict[str, str],
    normalize_keys: bool = True,
    header: str | None = None,
) -> str:
    """Generate .env file content from secrets dictionary.

    Args:
        secrets: Dictionary mapping secret names to values
        normalize_keys: Convert Key Vault names to ENV_VAR format
        header: Optional header comment to include at top of file

    Returns:
        String content for .env file
    """
    lines = []

    if header:
        lines.append(f"# {header}")
        lines.append("")

    for key, value in sorted(secrets.items()):
        lines.append(format_env_line(key, value, normalize=normalize_keys))

    return "\n".join(lines) + "\n"


def write_env_file(
    secrets: dict[str, str],
    output_path: Path | str = ".env",
    normalize_keys: bool = True,
    header: str | None = None,
) -> Path:
    """Write secrets to a .env file.

    Args:
        secrets: Dictionary mapping secret names to values
        output_path: Path for the output .env file
        normalize_keys: Convert Key Vault names to ENV_VAR format
        header: Optional header comment

    Returns:
        Path to the written file
    """
    output_path = Path(output_path)
    content = generate_env_content(secrets, normalize_keys, header)
    output_path.write_text(content)
    return output_path
