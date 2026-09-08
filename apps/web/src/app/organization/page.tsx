import { redirect } from "next/navigation";
import { readServerSession } from "@/features/auth/session";
import {
  MemberAdministration,
  type OrganizationMember,
} from "@/features/auth/member-administration";
import { fetchWorkspaceJson } from "@/features/intake/workspace-data";

export const dynamic = "force-dynamic";

function parseMembers(value: unknown): OrganizationMember[] | null {
  if (!Array.isArray(value)) return null;
  const roles = new Set(["owner", "admin", "analyst", "reviewer", "viewer"]);
  return value.filter(
    (item): item is OrganizationMember =>
      Boolean(item) &&
      typeof item === "object" &&
      typeof (item as OrganizationMember).id === "string" &&
      typeof (item as OrganizationMember).user_id === "string" &&
      typeof (item as OrganizationMember).email === "string" &&
      typeof (item as OrganizationMember).display_name === "string" &&
      roles.has((item as OrganizationMember).role),
  );
}

export default async function OrganizationPage() {
  const session = await readServerSession();
  if (!session) redirect("/login");
  const active = session.memberships.find(
    (membership) =>
      membership.organization_id === session.active_organization_id,
  );
  if (active?.role !== "owner") redirect("/");
  const members = await fetchWorkspaceJson(
    "organization-members",
    parseMembers,
    [],
  );
  return (
    <div className="page-content">
      <section className="page-intro">
        <div className="intro">
          <p className="eyebrow">ORGANIZATION ADMINISTRATION</p>
          <h1>Manage workspace access</h1>
          <p className="intro-description">
            Control who can work in this organization and the access each person
            receives.
          </p>
        </div>
      </section>
      <MemberAdministration members={members} />
    </div>
  );
}
