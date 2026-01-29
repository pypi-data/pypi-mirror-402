from pydantic import BaseModel, Field
from typing import Annotated, Literal
from nexo.types.string import OptStr


class RefreshToken(BaseModel):
    refresh_token: Annotated[OptStr, Field(None, description="Refresh Token")] = None


class AccessToken(BaseModel):
    access_token: Annotated[str, Field(..., description="Access Token")]


class TokenType(BaseModel):
    token_type: Annotated[
        Literal["Bearer"], Field("Bearer", description="Token's type")
    ] = "Bearer"


class ExpiresIn(BaseModel):
    expires_in: Annotated[
        int, Field(..., description="Expires In", ge=60, multiple_of=60)
    ]
