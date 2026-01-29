# vault-secrets

Reusable Python package for downloading secrets from HashiCorp Vault using AppRole authentication.

## Installation

```sh
pip install .
```

## Usage

```python
from vault_secrets import VaultSecretsClient

client = VaultSecretsClient()
secret = client.get_secret("my/path")
```