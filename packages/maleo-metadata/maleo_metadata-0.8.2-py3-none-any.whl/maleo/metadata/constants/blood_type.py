from nexo.schemas.resource import Resource, ResourceIdentifier


BLOOD_TYPE_RESOURCE = Resource(
    identifiers=[
        ResourceIdentifier(key="blood_type", name="Blood Type", slug="blood-types")
    ],
    details=None,
)
