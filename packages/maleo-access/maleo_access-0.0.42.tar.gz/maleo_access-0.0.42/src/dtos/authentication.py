from uuid import UUID
from nexo.schemas.mixins.identity import UUIDOrganizationId, UUIDUserId
from nexo.types.uuid import OptUUID
from ..mixins.authentication import RefreshToken, AccessToken, TokenType, ExpiresIn


class AuthenticationDTO(
    ExpiresIn,
    TokenType,
    AccessToken,
    RefreshToken,
):
    pass


class RefreshTokenCacheValue(UUIDUserId[UUID], UUIDOrganizationId[OptUUID]):
    pass
