"""Read-only integration catalog routes; no customer-system connections."""

import uuid

from fastapi import APIRouter, Depends

from aos_api.integration_catalog import CATALOG
from aos_api.routes_auth import tenant_context

catalog_router = APIRouter(tags=["integration-catalog"])


@catalog_router.get("/integration-catalog")
def list_integration_catalog(
    _org_id: uuid.UUID = Depends(tenant_context),
) -> list[dict[str, object]]:
    return [dict(entry) for entry in CATALOG]
