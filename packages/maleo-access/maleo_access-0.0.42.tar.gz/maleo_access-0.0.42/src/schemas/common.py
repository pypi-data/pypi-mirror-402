from pydantic import BaseModel, Field
from typing import Annotated
from ..mixins.authentication import AccessToken, TokenType, ExpiresIn


class OldAuthenticationSchema(BaseModel):
    token: Annotated[str, Field(..., description="Token String")]


class AuthenticationSchema(
    ExpiresIn,
    TokenType,
    AccessToken,
):
    pass
