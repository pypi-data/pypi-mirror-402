import keyring
import getpass
import re
import os

CANOPY_SECRET_PATTERN = re.compile(r'\$\{(CANOPY_[A-Z0-9_]+)\}')

def resolve_canopy_secrets(config: dict) -> dict:
    """
    Recursively resolve ${CANOPY_...} secrets in the config dict using keyring.
    If a secret is not found, it will be set to "TODO".
    Returns a new config dict with secrets injected.
    """
    def _resolve(obj):
        if isinstance(obj, dict):
            return {k: _resolve(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_resolve(i) for i in obj]
        elif isinstance(obj, str):
            match = CANOPY_SECRET_PATTERN.fullmatch(obj)
            if match:
                secret_name = match.group(1)
                secret = keyring.get_password('canopy', secret_name)
                if secret is None:
                    keyring.set_password('canopy', secret_name, "TODO")
                    secret = "TODO"
                return secret
            else:
                return obj
        else:
            return obj
    return _resolve(config)
