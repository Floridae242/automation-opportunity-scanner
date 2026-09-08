"""Immutable organization-level scoring weight configurations."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from aos_api.models import Organization, ScoringConfiguration
from aos_api.opportunity import DIMENSION_WEIGHTS, validate_weights


def current_configuration(
    db: Session, organization_id: uuid.UUID, actor_id: uuid.UUID
) -> ScoringConfiguration:
    # Serializes version allocation and first-default creation for an organization.
    db.scalar(select(Organization).where(Organization.id == organization_id).with_for_update())
    configuration = db.scalar(
        select(ScoringConfiguration)
        .where(ScoringConfiguration.organization_id == organization_id)
        .order_by(ScoringConfiguration.version_no.desc())
        .limit(1)
    )
    if configuration is not None:
        return configuration
    configuration = ScoringConfiguration(
        id=uuid.uuid4(),
        organization_id=organization_id,
        version_no=1,
        weights_json=dict(DIMENSION_WEIGHTS),
        created_by=actor_id,
    )
    db.add(configuration)
    db.flush()
    return configuration


def configuration_weights(configuration: ScoringConfiguration) -> dict[str, float]:
    return validate_weights(configuration.weights_json)


def payload(configuration: ScoringConfiguration) -> dict[str, object]:
    return {
        "id": str(configuration.id),
        "version_no": configuration.version_no,
        "weights": configuration_weights(configuration),
        "created_at": configuration.created_at.isoformat() if configuration.created_at else None,
    }
