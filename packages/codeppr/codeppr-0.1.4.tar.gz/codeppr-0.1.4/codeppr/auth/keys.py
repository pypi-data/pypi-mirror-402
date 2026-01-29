import keyring, keyring.errors

SERVICE_NAME = "codeppr"

# Check if a suitable keyring backend is available
def ensure_keyring_backend():
    try:
        keyring.get_keyring()
        return True
    except keyring.errors.NoKeyringError:
        raise RuntimeError("No suitable keyring backend available.")

def get_api_key(provider: str) -> str | None:
    ensure_keyring_backend()
    
    ret = keyring.get_password(SERVICE_NAME, provider)
    return ret

def set_api_key(provider: str, key: str) -> None:
    if not key:
        raise ValueError("API key cannot be empty.")
    
    ensure_keyring_backend()
    
    keyring.set_password(SERVICE_NAME, provider, key)

def delete_api_key(provider: str) -> None:
    ensure_keyring_backend()
    keyring.delete_password(SERVICE_NAME, provider)