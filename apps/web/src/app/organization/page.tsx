import { redirect } from "next/navigation";
import { readServerSession } from "@/features/auth/session";
import {
  MemberAdministration,
  type OrganizationMember,
} from "@/features/auth/member-administration";
import { fetchWorkspaceJson } from "@/features/intake/workspace-data";

export const dynamic = "force-dynamic";

type SsoStatus = { configured: boolean; missing: string[] };

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

function parseSsoStatus(value: unknown): SsoStatus | null {
  if (!value || typeof value !== "object") return null;
  const status = value as Record<string, unknown>;
  if (
    typeof status.configured !== "boolean" ||
    !Array.isArray(status.missing) ||
    !status.missing.every((item) => typeof item === "string")
  ) {
    return null;
  }
  return { configured: status.configured, missing: status.missing as string[] };
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
  const sso = await fetchWorkspaceJson("auth/sso/status", parseSsoStatus, {
    configured: false,
    missing: [
      "SSO_ISSUER",
      "SSO_CLIENT_ID",
      "SSO_CLIENT_SECRET",
      "SSO_REDIRECT_URI",
    ],
  });
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
      <section className="guide-card" aria-label="Single sign-on status">
        <p className="eyebrow">SINGLE SIGN-ON</p>
        <h2>
          {sso.configured
            ? "OIDC configuration is ready"
            : "OIDC setup required"}
        </h2>
        <p>
          {sso.configured
            ? "The deployment has all required OpenID Connect settings. Complete the provider verification before enabling sign-in."
            : `Set ${sso.missing.join(", ")} in the deployment secret store before enabling SSO.`}
        </p>
      </section>
      <MemberAdministration members={members} />
    </div>
  );
}
