from datetime import datetime
from typing import Dict, List, Optional

import requests
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt
from jose.utils import base64url_decode
from pydantic import BaseModel
from starlette.requests import Request
from util.form import as_form

JWK = Dict[str, str]


class JWKS(BaseModel):
    keys: List[JWK]


class JWTAuthorizationCredentials(BaseModel):
    jwt_token: str
    header: Dict[str, str]
    claims: Dict[str, str]
    signature: str
    message: str


@as_form
class PartnerLoginCredentials(BaseModel):
    username: str
    password: str
    user_pool_id: str
    client_id: str


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = False):
        super().__init__(auto_error=auto_error)

    def verify_jwk_token(self, jwt_credentials: JWTAuthorizationCredentials) -> bool:
        # Get jwks from cognito
        jwks = JWKS.parse_obj(
            requests.get(
                f"{jwt_credentials.claims['iss']}/.well-known/jwks.json"
            ).json()
        )

        # Create kid from jwk map
        kid_to_jwk = {jwk["kid"]: jwk for jwk in jwks.keys}

        # Verify KID
        try:
            public_key = kid_to_jwk[jwt_credentials.header["kid"]]
        except KeyError:
            raise HTTPException(
                status_code=403,
                detail="JWK public key not found",
            )

        # Verify signature
        key = jwk.construct(public_key)
        decoded_signature = base64url_decode(
            jwt_credentials.signature.encode()
        )  # consider changing bytes to str here

        return key.verify(jwt_credentials.message.encode(), decoded_signature)

    async def __call__(self, request: Request) -> Optional[JWTAuthorizationCredentials]:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)

        # Validate JWT
        if not credentials:
            return None

        if not credentials.scheme == "Bearer":
            raise HTTPException(
                status_code=403,
                detail="Wrong authentication method",
            )

        # Generate JWT credentials
        jwt_token = credentials.credentials

        try:
            message, signature = jwt_token.rsplit(".", 1)
        except ValueError:
            raise HTTPException(status_code=403, detail="JWT invalid")

        try:
            jwt_credentials = JWTAuthorizationCredentials(
                jwt_token=jwt_token,
                header=jwt.get_unverified_header(jwt_token),
                claims=jwt.get_unverified_claims(jwt_token),
                signature=signature,
                message=message,
            )
        except JWTError:
            raise HTTPException(status_code=403, detail="JWK invalid")

        if not self.verify_jwk_token(jwt_credentials):
            raise HTTPException(status_code=403, detail="JWK invalid")

        # Check the 'exp' claim for token expiration

        exp_timestamp = jwt_credentials.claims.get("exp")
        if exp_timestamp:
            current_time = datetime.utcnow().timestamp()
            if current_time > float(exp_timestamp):
                raise HTTPException(
                    status_code=401,
                    detail="Token has expired",
                )

        return jwt_credentials
