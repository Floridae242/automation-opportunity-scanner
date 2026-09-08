"""Tenant-scoped, append-only configuration of deterministic score weights."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from aos_api.intake import audit
from aos_api.models import ScoringConfiguration
from aos_api.opportunity import validate_weights
from aos_api.routes_auth import AuthContext, db_session, require_roles, tenant_context
from aos_api.scoring_config import current_configuration, payload

scoring_router = APIRouter(tags=["scoring"])
_admin = require_roles("owner", "admin")


class WeightsIn(BaseModel):
    weights: dict[str, object]

    @field_validator("weights")
    @classmethod
    def complete_normalized_weights(cls, weights: dict[str, object]) -> dict[str, float]:
        try:
            return validate_weights(weights)
        except ValueError as error:
            raise ValueError(str(error)) from error


@scoring_router.get("/scoring-configurations")
def list_scoring_configurations(
    org_id: uuid.UUID = Depends(tenant_context),
    context: AuthContext = Depends(_admin),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    current_configuration(db, org_id, context.user.id)
    configurations = list(
        db.scalars(
            select(ScoringConfiguration)
            .where(ScoringConfiguration.organization_id == org_id)
            .order_by(ScoringConfiguration.version_no.desc())
        )
    )
    db.commit()
    return {"configurations": [payload(configuration) for configuration in configurations]}


@scoring_router.post("/scoring-configurations", status_code=201)
def create_scoring_configuration(
    body: WeightsIn,
    org_id: uuid.UUID = Depends(tenant_context),
    context: AuthContext = Depends(_admin),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    current = current_configuration(db, org_id, context.user.id)
    configuration = ScoringConfiguration(
        id=uuid.uuid4(),
        organization_id=org_id,
        version_no=current.version_no + 1,
        weights_json=body.weights,
        created_by=context.user.id,
    )
    db.add(configuration)
    db.flush()
    audit(
        db,
        "scoring.configuration_created",
        org_id=org_id,
        actor_id=context.user.id,
        entity_type="scoring_configuration",
        entity_id=str(configuration.id),
        details={"version_no": configuration.version_no},
    )
    db.commit()
    return payload(configuration)
