from nexo.schemas.resource import Resource, ResourceIdentifier


AUTHENTICATION_RESOURCE = Resource(
    identifiers=[
        ResourceIdentifier(
            key="authentication", name="Authentication", slug="authentications"
        )
    ],
    details=None,
)
