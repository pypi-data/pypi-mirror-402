from nexo.schemas.resource import Resource, ResourceIdentifier


MEDICAL_ROLE_RESOURCE = Resource(
    identifiers=[
        ResourceIdentifier(
            key="medical_role", name="Medical Role", slug="medical-roles"
        )
    ],
    details=None,
)
