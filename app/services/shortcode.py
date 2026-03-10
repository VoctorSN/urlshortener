import re
import secrets

RESERVED_PATHS = {
    "api", "health", "docs", "redoc", "openapi.json", "favicon.ico",
}
ALIAS_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")


def generate_short_code(length: int = 7) -> str:
    """Generate a cryptographically random URL-safe short code."""
    return secrets.token_urlsafe(length)[:length]


def is_valid_custom_alias(alias: str) -> bool:
    """Validate that a custom alias is well-formed and not reserved."""
    if alias.lower() in RESERVED_PATHS:
        return False
    return bool(ALIAS_PATTERN.match(alias))
