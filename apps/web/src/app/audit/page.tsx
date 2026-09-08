import { redirect } from "next/navigation";
import { readServerSession } from "@/features/auth/session";
import { fetchWorkspaceJson } from "@/features/intake/workspace-data";

type Event = {
  id: string;
  action: string;
  actor: string | null;
  created_at: string;
};
function parse(value: unknown): Event[] | null {
  return Array.isArray(value)
    ? value.filter(
        (item): item is Event =>
          Boolean(item) &&
          typeof item === "object" &&
          typeof (item as Event).id === "string" &&
          typeof (item as Event).action === "string" &&
          typeof (item as Event).created_at === "string",
      )
    : null;
}

export default async function AuditPage() {
  const session = await readServerSession();
  if (!session) redirect("/login");
  const active = session.memberships.find(
    (m) => m.organization_id === session.active_organization_id,
  );
  if (!active || !["owner", "admin"].includes(active.role)) redirect("/");
  const events = await fetchWorkspaceJson("audit-events", parse, []);
  return (
    <div className="page-content">
      <section className="page-intro">
        <div className="intro">
          <p className="eyebrow">AUDIT EXPLORER</p>
          <h1>Organization activity</h1>
        </div>
      </section>
      <section className="guide-card" aria-label="Audit events">
        <ul>
          {events.map((event) => (
            <li key={event.id}>
              <strong>{event.action}</strong> · {event.actor ?? "System"} ·{" "}
              {new Date(event.created_at).toLocaleString()}
            </li>
          ))}
        </ul>
        {events.length === 0 && (
          <p className="margin-note">No audit events are available.</p>
        )}
      </section>
    </div>
  );
}
