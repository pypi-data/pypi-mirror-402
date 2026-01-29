# az-envs

Create `.env` files from Azure Key Vault secrets using your local Azure CLI credentials.

## Installation

```bash
pip install az-envs
```

Or from source:

```bash
pip install git+https://github.com/dillonjohnson/az-envs.git
```

## Prerequisites

1. Azure CLI installed and logged in:
   ```bash
   az login
   ```

2. Appropriate permissions to read secrets from the target Key Vault(s)

## Usage

### Generate .env from a Key Vault

```bash
az-envs generate <vault-name> -o .env
```

Options:
- `-o, --output` - Output file path (default: `.env`)
- `--prefix` - Only include secrets with this prefix
- `--no-normalize` - Keep original secret names (don't convert to `ENV_VAR` format)
- `--no-header` - Don't include a header comment

### List Key Vaults in a resource group

```bash
az-envs list <resource-group> -s <subscription-id>
```

## Secret Name Conversion

By default, Key Vault secret names are converted to standard environment variable format:
- `my-secret-name` becomes `MY_SECRET_NAME`

Use `--no-normalize` to keep the original names.

## Examples

```bash
# Generate .env from a vault named "myapp-secrets"
az-envs generate myapp-secrets

# Generate only secrets starting with "DB-"
az-envs generate myapp-secrets --prefix DB-

# List all vaults in a resource group
az-envs list my-resource-group -s 12345678-1234-1234-1234-123456789012
```
