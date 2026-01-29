"""CLI interface for az-envs."""

import sys

import click

from az_envs.env_file import write_env_file
from az_envs.exceptions import AzEnvsError
from az_envs.keyvault import (
    fetch_secrets,
    fetch_secrets_by_prefix,
    list_keyvaults_in_resource_group,
)


@click.group()
@click.version_option()
def main():
    """Create .env files from Azure Key Vault secrets.

    Uses your local Azure CLI credentials (az login) to authenticate.
    """
    pass


@main.command()
@click.argument("vault_name")
@click.option(
    "-o", "--output",
    default=".env",
    help="Output file path (default: .env)",
)
@click.option(
    "--prefix",
    default=None,
    help="Only include secrets with this prefix",
)
@click.option(
    "--no-normalize",
    is_flag=True,
    help="Don't convert secret names to ENV_VAR format",
)
@click.option(
    "--header/--no-header",
    default=True,
    help="Include a header comment with vault name",
)
def generate(vault_name: str, output: str, prefix: str, no_normalize: bool, header: bool):
    """Generate .env file from a Key Vault.

    VAULT_NAME is the name of the Azure Key Vault (not the full URL).

    Example:
        az-envs generate my-keyvault -o .env.local
    """
    try:
        click.echo(f"Fetching secrets from '{vault_name}'...")

        if prefix:
            secrets = fetch_secrets_by_prefix(vault_name, prefix)
            click.echo(f"Found {len(secrets)} secrets matching prefix '{prefix}'")
        else:
            secrets = fetch_secrets(vault_name)
            click.echo(f"Found {len(secrets)} secrets")

        if not secrets:
            click.echo("No secrets found.", err=True)
            sys.exit(1)

        header_text = f"Generated from Azure Key Vault: {vault_name}" if header else None
        output_path = write_env_file(
            secrets,
            output_path=output,
            normalize_keys=not no_normalize,
            header=header_text,
        )
        click.echo(f"Written to {output_path}")

    except AzEnvsError as e:
        click.echo(f"\n{e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("list")
@click.argument("resource_group")
@click.option(
    "-s", "--subscription",
    required=True,
    help="Azure subscription ID",
)
def list_vaults(resource_group: str, subscription: str):
    """List Key Vaults in a resource group.

    Example:
        az-envs list my-resource-group -s <subscription-id>
    """
    try:
        click.echo(f"Listing Key Vaults in '{resource_group}'...")
        vaults = list_keyvaults_in_resource_group(subscription, resource_group)

        if not vaults:
            click.echo("No Key Vaults found.")
            return

        click.echo(f"Found {len(vaults)} Key Vault(s):")
        for vault in vaults:
            click.echo(f"  - {vault}")

    except AzEnvsError as e:
        click.echo(f"\n{e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
