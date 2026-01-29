import hvac
import os


class VaultSecretsClient:
    def __init__(
            self,
            url=None,
            role_id=None,
            secret_id=None,
            mount_point='secret',
            approle_mount_point='approle',
            verify=True,
            login_on_init=True,
    ):
        self.url = url or os.getenv('VAULT_ADDR')
        self.role_id = role_id or os.getenv('VAULT_ROLE_ID')
        self.secret_id = secret_id or os.getenv('VAULT_SECRET_ID')
        self.mount_point = mount_point
        self.approle_mount_point = approle_mount_point
        self.verify = verify
        self.client = hvac.Client(url=self.url, verify=self.verify)
        if login_on_init:
            self.__login_approle()

    def __login_approle(self):
        if not self.role_id or not self.secret_id:
            raise ValueError("AppRole role_id and secret_id are required for authentication.")
        login_response = self.client.auth.approle.login(
            role_id=self.role_id,
            secret_id=self.secret_id,
            mount_point=self.approle_mount_point,
        )
        if not self.client.is_authenticated():
            raise Exception("AppRole authentication failed")
        return login_response

    def get_secret(self, path, env, version=None):
        """Fetches a single secret at the specified path."""
        if not self.client.is_authenticated():
            self.__login_approle()
        params = {
            'path': f"{self.__standardize_env(env)}/{path}",
            'mount_point': self.mount_point
        }
        if version:
            params['version'] = version
        secret = self.client.secrets.kv.v2.read_secret_version(**params)
        return secret['data']['data']

    @staticmethod
    def __standardize_env(env):
        """Converts environment names to standardized folder names."""
        mapping = {
            'development': 'stg',
            'dev': 'stg',
            'staging': 'stg',
            'stg': 'stg',
            'production': 'prd',
            'prd': 'prd',
        }
        return mapping.get(env.lower(), "stg")

    def get_supabase_secrets(self, env, version=None):
        """
        Fetches Supabase-related secrets stored under the given path.
        returns in the form: (POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        """
        secrets = self.get_secret(f"supabase", env, version)
        return secrets["POSTGRES_HOST"], secrets["POSTGRES_DB"], secrets["POSTGRES_USER"], secrets["POSTGRES_PASSWORD"]

    def get_supabase_transaction_secrets(self, env, version=None):
        """
        Fetches Supabase-related secrets stored under the given path.
        returns in the form: (POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
        """
        secrets = self.get_secret(f"supabase", env, version)
        return secrets["POSTGRES_HOST_TRANSACTION"], secrets["POSTGRES_DB"], secrets["POSTGRES_USER"], secrets[
            "POSTGRES_PASSWORD"]

    def __list_secrets(self, env, path=""):
        """Lists all sub-secrets (folders and keys) under the given path."""
        if not self.client.is_authenticated():
            self.__login_approle()
        result = self.client.secrets.kv.v2.list_secrets(
            path=f"{self.__standardize_env(env)}/{path}",
            mount_point=self.mount_point,
        )
        return result["data"]["keys"]

    def get_all_secrets(self, env, path=""):
        """
        Recursively gets all secrets under a given path. Returns a dict:
        {
            "subpath/key1": { ...secret keyvalues... },
            "subpath/key2": { ...secret keyvalues... },
        }
        """
        all_secrets = {}
        keys = self.__list_secrets(env, path)
        for key in keys:
            next_path = f"{path}/{key}" if path else key
            if key.endswith("/"):
                # It's a subfolder. Recursively get secrets.
                more_secrets = self.get_all_secrets(env, next_path.rstrip("/"))
                all_secrets.update(more_secrets)
            else:
                # It's a secret entry.
                try:
                    secret = self.get_secret(next_path, env)
                    all_secrets[next_path] = secret
                except Exception as e:
                    # Optionally handle missing or unreadable secrets
                    print(f"Error fetching {next_path}: {e}")
        return all_secrets
