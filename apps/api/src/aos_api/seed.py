"""Run explicitly with python -m aos_api.seed in local development only."""

from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert

from aos_api.config import Settings
from aos_api.models import Membership, Organization, User

ORG_ID = UUID("00000000-0000-4000-8000-000000000001")
USER_ID = UUID("00000000-0000-4000-8000-000000000002")
MEMBERSHIP_ID = UUID("00000000-0000-4000-8000-000000000003")


def seed(settings: Settings) -> None:
    if settings.environment not in {"development", "test"}:
        raise ValueError("Demo seed requires development or test environment")
    engine = create_engine(settings.database_url.get_secret_value())
    try:
        with engine.begin() as connection:
            connection.execute(
                insert(Organization)
                .values(id=ORG_ID, name="Local demo organization")
                .on_conflict_do_nothing(index_elements=["id"])
            )
            connection.execute(
                insert(User)
                .values(
                    id=USER_ID,
                    auth_subject="local-demo:no-login",
                    email="demo@example.invalid",
                    display_name="Local demo user",
                )
                .on_conflict_do_nothing(index_elements=["id"])
            )
            connection.execute(
                insert(Membership)
                .values(id=MEMBERSHIP_ID, organization_id=ORG_ID, user_id=USER_ID, role="owner")
                .on_conflict_do_nothing(index_elements=["id"])
            )
    finally:
        engine.dispose()


if __name__ == "__main__":
    seed(Settings())
