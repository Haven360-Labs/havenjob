"""User-related business logic (e.g. forwarding address generation)."""

import secrets

from apps.users.models import User

FORWARDING_DOMAIN = "havenjob.app"
MAX_GENERATION_ATTEMPTS = 10


def generate_forwarding_address() -> str:
    """
    Generate a unique forwarding address (local@havenjob.app).
    Uses a random local part and ensures uniqueness against User.forwarding_address.
    """
    for _ in range(MAX_GENERATION_ATTEMPTS):
        local = secrets.token_hex(8)
        address = f"{local}@{FORWARDING_DOMAIN}"
        if not User.objects.filter(forwarding_address__iexact=address).exists():
            return address
    raise RuntimeError("Could not generate unique forwarding address")
