import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from aos_api.errors import ApiError
from aos_api.intake import audit, get_owned
from aos_api.models import BenefitRealization, Opportunity
from aos_api.routes_auth import WRITE_ROLES, AuthContext, db_session, require_roles, tenant_context

benefits_router = APIRouter(tags=["benefits"])
_writer = require_roles(*WRITE_ROLES)


class BenefitIn(BaseModel):
    period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    hours_saved: float | None = Field(default=None, ge=0)
    monetary_benefit: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=2000)


def benefit_payload(item: BenefitRealization) -> dict[str, object]:
    return {
        "id": str(item.id),
        "period": item.period,
        "hours_saved": item.hours_saved,
        "monetary_benefit": item.monetary_benefit,
        "notes": item.notes,
        "created_at": item.created_at.isoformat(),
    }


@benefits_router.get("/opportunities/{opportunityId}/benefits")
def list_benefits(
    opportunityId: uuid.UUID,
    org_id: uuid.UUID = Depends(tenant_context),
    db: Session = Depends(db_session),
) -> list[dict[str, object]]:
    get_owned(db, Opportunity, org_id, opportunityId)
    items = db.scalars(
        select(BenefitRealization)
        .where(
            BenefitRealization.organization_id == org_id,
            BenefitRealization.opportunity_id == opportunityId,
        )
        .order_by(BenefitRealization.period.desc())
    )
    return [benefit_payload(item) for item in items]


@benefits_router.post("/opportunities/{opportunityId}/benefits", status_code=201)
def record_benefit(
    opportunityId: uuid.UUID,
    body: BenefitIn,
    org_id: uuid.UUID = Depends(tenant_context),
    context: AuthContext = Depends(_writer),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    get_owned(db, Opportunity, org_id, opportunityId)
    existing = db.scalar(
        select(BenefitRealization.id).where(
            BenefitRealization.organization_id == org_id,
            BenefitRealization.opportunity_id == opportunityId,
            BenefitRealization.period == body.period,
        )
    )
    if existing is not None:
        raise ApiError(
            409,
            "BENEFIT_ALREADY_RECORDED",
            "A benefit realization already exists for this opportunity and month.",
        )
    item = BenefitRealization(
        id=uuid.uuid4(),
        organization_id=org_id,
        opportunity_id=opportunityId,
        recorded_by=context.user.id,
        **body.model_dump(),
    )
    db.add(item)
    db.flush()
    audit(
        db,
        "benefit.recorded",
        org_id=org_id,
        actor_id=context.user.id,
        entity_type="opportunity",
        entity_id=str(opportunityId),
        details={"period": body.period},
    )
    db.commit()
    return benefit_payload(item)
