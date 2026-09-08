import { redirect } from "next/navigation";
import { readServerSession } from "@/features/auth/session";
import { fetchWorkspaceJson } from "@/features/intake/workspace-data";

type Integration = {
  key: string;
  name: string;
  capabilities: string[];
  evidence: string;
};

function parseCatalog(value: unknown): Integration[] | null {
  if (!Array.isArray(value)) return null;
  const catalog = value.filter(
    (item): item is Integration =>
      Boolean(item) &&
      typeof item === "object" &&
      typeof (item as { key?: unknown }).key === "string" &&
      typeof (item as { name?: unknown }).name === "string" &&
      typeof (item as { evidence?: unknown }).evidence === "string" &&
      Array.isArray((item as { capabilities?: unknown }).capabilities) &&
      (item as { capabilities: unknown[] }).capabilities.every(
        (capability) => typeof capability === "string",
      ),
  );
  return catalog.length === value.length ? catalog : null;
}

export default async function IntegrationsPage() {
  if (!(await readServerSession())) redirect("/login");
  const catalog = await fetchWorkspaceJson(
    "integration-catalog",
    parseCatalog,
    [],
  );
  return (
    <div className="page-content">
      <section className="page-intro">
        <div className="intro">
          <p className="eyebrow">
            <span className="eyebrow-line" />
            INTEGRATION CATALOG
          </p>
          <h1>Approved capability evidence</h1>
          <p className="intro-description">
            These entries support recommendations only. The Scanner never
            connects to or changes a customer system.
          </p>
        </div>
      </section>
      <section aria-label="Approved integrations" className="card-grid">
        {catalog.map((integration) => (
          <article className="guide-card" key={integration.key}>
            <h2>{integration.name}</h2>
            <ul className="check-list">
              {integration.capabilities.map((capability) => (
                <li key={capability}>{capability.replaceAll("_", " ")}</li>
              ))}
            </ul>
            <p className="margin-note">{integration.evidence}</p>
          </article>
        ))}
        {catalog.length === 0 && (
          <p className="margin-note">No approved integrations are available.</p>
        )}
      </section>
    </div>
  );
}
