from .types import SpintlyTokenResponse


def format_spintly_token(data: SpintlyTokenResponse) -> str:
    return f"{data.access_token}"


def build_headers(token: SpintlyTokenResponse) -> dict:
    return dict(
        Authorization=format_spintly_token(token),
    )
