from nexo.schemas.resource import Resource, ResourceIdentifier


ORGANIZATION_TYPE_RESOURCE = Resource(
    identifiers=[
        ResourceIdentifier(
            key="organization_type",
            name="Organization Type",
            slug="organization-types",
        )
    ],
    details=None,
)
