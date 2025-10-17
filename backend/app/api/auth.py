from fastapi import Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
VALID_API_KEYS = ["dev-key-123", "prod-key-456"]

def verify_api_key(api_key: str = Security(api_key_header)):
    # If no key is provided, just allow access (optional auth)
    if api_key is None:
        return None
    # If key is provided, check if it's valid
    if api_key not in VALID_API_KEYS:
        # Optionally, you can log or track invalid attempts here
        return None
    return api_key

