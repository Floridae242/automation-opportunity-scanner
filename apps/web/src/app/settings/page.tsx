import { redirect } from "next/navigation";
import { readServerSession } from "@/features/auth/session";
import {
  ScoringSettings,
  type ScoringConfiguration,
} from "@/features/portfolio/scoring-settings";
import { fetchWorkspaceJson } from "@/features/intake/workspace-data";
import {
  CostTemplates,
  type CostTemplate,
} from "@/features/portfolio/cost-templates";

function parseCostTemplates(value: unknown): CostTemplate[] | null {
  if (!Array.isArray(value)) return null;
  return value.filter(
    (item): item is CostTemplate =>
      Boolean(item) &&
      typeof item === "object" &&
      typeof (item as CostTemplate).id === "string" &&
      typeof (item as CostTemplate).name === "string" &&
      typeof (item as CostTemplate).currency === "string" &&
      typeof (item as CostTemplate).loaded_hourly_cost === "number" &&
      typeof (item as CostTemplate).monthly_operating_cost === "number" &&
      typeof (item as CostTemplate).implementation_cost === "number",
  );
}

function parseConfigurations(
  value: unknown,
): { configurations: ScoringConfiguration[] } | null {
  if (
    !value ||
    typeof value !== "object" ||
    !Array.isArray((value as { configurations?: unknown }).configurations)
  ) {
    return null;
  }
  const configurations = (
    value as { configurations: unknown[] }
  ).configurations.filter(
    (item): item is ScoringConfiguration =>
      Boolean(item) &&
      typeof item === "object" &&
      typeof (item as { id?: unknown }).id === "string" &&
      typeof (item as { version_no?: unknown }).version_no === "number" &&
      typeof (item as { weights?: unknown }).weights === "object",
  );
  return { configurations };
}

export default async function SettingsPage() {
  const session = await readServerSession();
  if (!session) redirect("/login");
  const active = session.memberships.find(
    (membership) =>
      membership.organization_id === session.active_organization_id,
  );
  const data = await fetchWorkspaceJson(
    "scoring-configurations",
    parseConfigurations,
    {
      configurations: [],
    },
  );
  const templates = await fetchWorkspaceJson(
    "cost-templates",
    parseCostTemplates,
    [],
  );
  const editable = active?.role === "owner" || active?.role === "admin";
  return (
    <div className="page-content">
      <section className="page-intro">
        <div className="intro">
          <p className="eyebrow">
            <span className="eyebrow-line" />
            SCORING SETTINGS
          </p>
          <h1>Set how opportunities are prioritized</h1>
          <p className="intro-description">
            Each save creates an immutable configuration version for future
            analyses.
          </p>
        </div>
      </section>
      <ScoringSettings
        configuration={data.configurations[0] ?? null}
        editable={editable}
      />
      <CostTemplates editable={editable} templates={templates} />
    </div>
  );
}
