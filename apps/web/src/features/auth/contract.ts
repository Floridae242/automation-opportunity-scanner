export type AuthRole = "owner" | "admin" | "analyst" | "reviewer" | "viewer";

export type AuthUser = Readonly<{
  id: string;
  email: string;
  display_name: string;
}>;

export type OrganizationMembership = Readonly<{
  organization_id: string;
  organization_name: string;
  role: AuthRole;
}>;

export type AuthSession = Readonly<{
  user: AuthUser;
  active_organization_id: string | null;
  memberships: readonly OrganizationMembership[];
}>;

const ROLES = new Set(["owner", "admin", "analyst", "reviewer", "viewer"]);
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function parseAuthSession(value: unknown): AuthSession | null {
  if (typeof value !== "object" || value === null) return null;
  const candidate = value as Record<string, unknown>;
  const user = candidate.user;
  if (typeof user !== "object" || user === null) return null;
  const profile = user as Record<string, unknown>;
  if (
    typeof profile.id !== "string" ||
    !UUID.test(profile.id) ||
    typeof profile.email !== "string" ||
    typeof profile.display_name !== "string"
  )
    return null;
  if (!Array.isArray(candidate.memberships)) return null;
  const memberships: OrganizationMembership[] = [];
  for (const item of candidate.memberships) {
    if (typeof item !== "object" || item === null) return null;
    const membership = item as Record<string, unknown>;
    if (
      typeof membership.organization_id !== "string" ||
      !UUID.test(membership.organization_id) ||
      typeof membership.organization_name !== "string" ||
      typeof membership.role !== "string" ||
      !ROLES.has(membership.role)
    )
      return null;
    memberships.push({
      organization_id: membership.organization_id,
      organization_name: membership.organization_name,
      role: membership.role as AuthRole,
    });
  }
  const active = candidate.active_organization_id;
  if (active !== null && typeof active !== "string") return null;
  if (typeof active === "string" && !UUID.test(active)) return null;
  return {
    user: {
      id: profile.id,
      email: profile.email,
      display_name: profile.display_name,
    },
    active_organization_id: active,
    memberships,
  };
}

export function parseApiErrorMessage(value: unknown): string | null {
  if (typeof value !== "object" || value === null) return null;
  const error = (value as Record<string, unknown>).error;
  if (typeof error !== "object" || error === null) return null;
  const message = (error as Record<string, unknown>).message;
  return typeof message === "string" ? message : null;
}
