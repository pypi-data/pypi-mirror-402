"""Azure Key Vault operations using local az login credentials."""

from azure.core.exceptions import (
    ClientAuthenticationError,
    HttpResponseError,
    ServiceRequestError,
)
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.mgmt.keyvault import KeyVaultManagementClient

from az_envs.exceptions import (
    AuthenticationError,
    PermissionError,
    ResourceNotFoundError,
)


def get_credential() -> DefaultAzureCredential:
    """Get Azure credential from local az login session."""
    return DefaultAzureCredential()


def list_keyvaults_in_resource_group(
    subscription_id: str,
    resource_group: str,
) -> list[str]:
    """List all Key Vault names in a resource group."""
    try:
        credential = get_credential()
        client = KeyVaultManagementClient(credential, subscription_id)
        vaults = client.vaults.list_by_resource_group(resource_group)
        return [vault.name for vault in vaults]
    except ClientAuthenticationError as e:
        raise AuthenticationError(e) from e
    except HttpResponseError as e:
        if e.status_code == 403:
            raise PermissionError(
                resource=resource_group,
                operation="list Key Vaults",
                original_error=e,
            ) from e
        if e.status_code == 404:
            raise ResourceNotFoundError(
                resource_type="Resource group",
                resource_name=resource_group,
                original_error=e,
            ) from e
        raise


def get_keyvault_url(vault_name: str) -> str:
    """Construct the Key Vault URL from its name."""
    return f"https://{vault_name}.vault.azure.net"


def fetch_secrets(vault_name: str) -> dict[str, str]:
    """Fetch all secrets from a Key Vault.

    Args:
        vault_name: Name of the Key Vault (not the full URL)

    Returns:
        Dictionary mapping secret names to their values
    """
    try:
        credential = get_credential()
        vault_url = get_keyvault_url(vault_name)
        client = SecretClient(vault_url=vault_url, credential=credential)

        secrets = {}
        for secret_properties in client.list_properties_of_secrets():
            if secret_properties.enabled:
                secret = client.get_secret(secret_properties.name)
                secrets[secret_properties.name] = secret.value

        return secrets
    except ClientAuthenticationError as e:
        raise AuthenticationError(e) from e
    except ServiceRequestError as e:
        raise ResourceNotFoundError(
            resource_type="Key Vault",
            resource_name=vault_name,
            original_error=e,
        ) from e
    except HttpResponseError as e:
        if e.status_code == 403:
            raise PermissionError(
                resource=vault_name,
                operation="read secrets",
                original_error=e,
            ) from e
        if e.status_code == 404:
            raise ResourceNotFoundError(
                resource_type="Key Vault",
                resource_name=vault_name,
                original_error=e,
            ) from e
        raise


def fetch_secrets_by_prefix(vault_name: str, prefix: str) -> dict[str, str]:
    """Fetch secrets from a Key Vault that match a prefix.

    Args:
        vault_name: Name of the Key Vault
        prefix: Only include secrets whose names start with this prefix

    Returns:
        Dictionary mapping secret names to their values
    """
    all_secrets = fetch_secrets(vault_name)
    return {k: v for k, v in all_secrets.items() if k.startswith(prefix)}
