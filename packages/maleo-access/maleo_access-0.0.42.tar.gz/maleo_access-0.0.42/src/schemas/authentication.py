from pydantic import BaseModel, Field, model_validator
from typing import Annotated, Literal, Self
from nexo.enums.system import SystemRole, FullSystemRoleMixin
from nexo.schemas.error.enums import ErrorCode
from nexo.types.string import OptStr
from maleo.identity.enums.user import IdentifierType
from maleo.identity.mixins.user import UserIdentifier


class AuthenticationData(BaseModel):
    organization_key: Annotated[
        OptStr, Field(None, description="Organization's Key", max_length=255)
    ] = None
    identifier_type: Annotated[
        Literal[IdentifierType.EMAIL, IdentifierType.USERNAME],
        Field(..., description="Identifier's Type"),
    ]
    identifier_value: Annotated[str, Field(..., description="Identifier's Value")]
    password: Annotated[str, Field(..., description="Password")]


class OldAuthenticationData(
    AuthenticationData,
    FullSystemRoleMixin[Literal[SystemRole.ADMINISTRATOR, SystemRole.USER]],
):
    @model_validator(mode="after")
    def validate_system_role_and_organization_key(self) -> Self:
        if self.system_role is SystemRole.ADMINISTRATOR:
            if self.organization_key is not None:
                raise ValueError(
                    ErrorCode.BAD_REQUEST,
                    "Organization Key must be None for Administrator System Role",
                )
        elif self.system_role is SystemRole.USER:
            if self.organization_key is None:
                raise ValueError(
                    ErrorCode.BAD_REQUEST,
                    "Organization Key can not be None for User System Role",
                )
        return self


class RegularAuthenticationParameters(BaseModel):
    organization_key: Annotated[
        OptStr, Field(None, description="Organization's Key", max_length=255)
    ] = None
    identifier: Annotated[UserIdentifier, Field(..., description="User's Identifier")]
    password: Annotated[str, Field(..., description="User's Password")]

    @classmethod
    def from_data(cls, data: AuthenticationData | OldAuthenticationData) -> Self:
        return cls(
            organization_key=data.organization_key,
            identifier=UserIdentifier(
                type=data.identifier_type,
                value=data.identifier_value,
            ),
            password=data.password,
        )


class RefreshAuthenticationParameters(BaseModel):
    refresh_token: Annotated[str, Field(..., description="Refresh Token")]


AuthenticationParameters = (
    RegularAuthenticationParameters | RefreshAuthenticationParameters
)
