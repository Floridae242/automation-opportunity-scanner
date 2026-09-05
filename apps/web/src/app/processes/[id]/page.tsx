import { notFound, redirect } from "next/navigation";
import { parseProcess, parseVersionDetail } from "@/features/intake/contract";
import { formatMetricValue } from "@/features/intake/client-api";
import { fetchWorkspaceJson } from "@/features/intake/workspace-data";
import { IntakeForm } from "@/features/intake/intake-form";
import { ExtractionPanel } from "@/features/intake/extraction-panel";
import { StepReviewEditor } from "@/features/intake/step-review";
import { readServerSession } from "@/features/auth/session";

export const dynamic = "force-dynamic";

const METRIC_LABELS: Record<string, string> = {
  frequency: "Frequency",
  duration_minutes: "Duration (minutes)",
  volume_per_period: "Volume",
  error_rate: "Error rate",
  rework_rate: "Rework rate",
  sla: "SLA",
  systems: "Systems",
  approvals_required: "Approvals",
  sensitivity: "Sensitivity",
};

export default async function ProcessPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  if (!(await readServerSession())) redirect("/login");
  const { id } = await params;
  const process = await fetchWorkspaceJson(
    `processes/${id}`,
    parseProcess,
    null,
  );
  if (process === null) notFound();
  const latestDraft =
    process.latest_version !== null &&
    process.latest_version.review_status === "draft"
      ? process.latest_version
      : null;
  const draftDetail = latestDraft
    ? await fetchWorkspaceJson(
        `process-versions/${latestDraft.id}`,
        parseVersionDetail,
        null,
      )
    : null;
  const reviewable = draftDetail !== null && draftDetail.steps.length > 0;
  return (
    <div className="page-content">
      <section className="page-intro">
        <div className="intro">
          <p className="eyebrow">
            <span className="eyebrow-line" />
            PROCESS INTAKE
          </p>
          <h1>{process.name}</h1>
          <p className="intro-description">
            Capture the workflow in your own words, with the numbers you
            actually know. Each save creates a new draft version for review.
          </p>
        </div>
      </section>
      <IntakeForm processId={process.id} />
      {reviewable ? (
        <StepReviewEditor version={draftDetail} />
      ) : latestDraft !== null ? (
        <ExtractionPanel processId={process.id} />
      ) : null}
      <section aria-label="Version history" className="workflow-section">
        <h2 className="quiet-label">DRAFT HISTORY</h2>
        {process.versions.length === 0 ? (
          <div className="empty-state">
            <h3>Nothing captured yet</h3>
            <p>
              Save your first intake draft above — you can refine it as often as
              needed.
            </p>
          </div>
        ) : (
          <div className="evidence-rail">
            <h3>Versions</h3>
            <ul>
              {process.versions.map((version) => (
                <li key={version.id}>
                  <article className="guide-card">
                    <header className="principle-heading">
                      <strong>v{version.version_no}</strong>
                      <span
                        className={
                          version.review_status === "draft"
                            ? "evidence-chip"
                            : "outline-tag"
                        }
                      >
                        {version.review_status}
                      </span>
                    </header>
                    <p>{version.source_summary}</p>
                    <dl className="metrics-readout">
                      {Object.entries(METRIC_LABELS).map(([key, label]) => (
                        <div key={key}>
                          <dt>{label}</dt>
                          <dd>
                            {formatMetricValue(
                              version.metrics[
                                key as keyof typeof version.metrics
                              ],
                            )}
                          </dd>
                        </div>
                      ))}
                    </dl>
                  </article>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>
    </div>
  );
}
