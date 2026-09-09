import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from aos_api.intake import audit
from aos_api.models import Organization
from aos_api.routes_auth import AuthContext, db_session, require_roles, tenant_context

cost_templates_router = APIRouter(tags=["cost templates"])
_admin = require_roles("owner", "admin")


class CostTemplateIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    loaded_hourly_cost: float = Field(ge=0)
    monthly_operating_cost: float = Field(ge=0)
    implementation_cost: float = Field(ge=0)


def _templates(organization: Organization) -> list[dict[str, object]]:
    raw = organization.settings_json.get("cost_templates", [])
    return raw if isinstance(raw, list) else []


@cost_templates_router.get("/cost-templates")
def list_cost_templates(
    org_id: uuid.UUID = Depends(tenant_context),
    context: AuthContext = Depends(_admin),
    db: Session = Depends(db_session),
) -> list[dict[str, object]]:
    organization = db.get(Organization, org_id)
    return _templates(organization) if organization is not None else []


@cost_templates_router.post("/cost-templates", status_code=201)
def create_cost_template(
    body: CostTemplateIn,
    org_id: uuid.UUID = Depends(tenant_context),
    context: AuthContext = Depends(_admin),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    organization = db.get(Organization, org_id)
    if organization is None:
        return {}
    templates = _templates(organization)
    template = {"id": str(uuid.uuid4()), **body.model_dump()}
    organization.settings_json = {
        **organization.settings_json,
        "cost_templates": [*templates, template],
    }
    audit(
        db,
        "cost_template.created",
        org_id=org_id,
        actor_id=context.user.id,
        entity_type="organization",
        entity_id=str(org_id),
        details={"name": body.name.strip()},
    )
    db.commit()
    return template
