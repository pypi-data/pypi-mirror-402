from nexo.schemas.resource import Resource, ResourceIdentifier


MEDICAL_SERVICE_RESOURCE = Resource(
    identifiers=[
        ResourceIdentifier(
            key="medical_service", name="Medical Service", slug="medical-services"
        )
    ],
    details=None,
)
