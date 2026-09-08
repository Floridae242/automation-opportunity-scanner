import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { ExportReportButton } from "@/features/portfolio/export-report";
import { readServerSession } from "@/features/auth/session";
import { fetchWorkspaceJson } from "@/features/intake/workspace-data";
import {
  parseAnalysisOverview,
  parseOpportunityList,
  type OpportunityRow,
} from "@/features/portfolio/contract";

export const dynamic = "force-dynamic";

function cell(
  impact: number | null,
  effort: number | null,
): { row: number; col: number } | null {
  if (impact === null || effort === null) return null;
  return {
    row: 4 - Math.min(4, Math.floor(impact / 20)),
    col: Math.min(4, Math.floor(effort / 20)),
  };
}

function Matrix({
  opportunities,
}: {
  opportunities: readonly OpportunityRow[];
}) {
  const placed = opportunities.map((item) => ({
    item,
    at: cell(item.axes.impact, item.axes.effort),
  }));
  return (
    <div
      className="matrix-grid"
      role="img"
      aria-label="Impact versus effort matrix"
    >
      <div className="matrix-axis-y">Impact</div>
      <div className="matrix-cells">
        {Array.from({ length: 5 }, (_, row) =>
          Array.from({ length: 5 }, (_, col) => {
            const hits = placed.filter(
              (p) => p.at && p.at.row === row && p.at.col === col,
            );
            return (
              <span
                key={`${row}-${col}`}
                className={hits.length ? "matrix-cell filled" : "matrix-cell"}
              >
                {hits.map(({ item }) => (
                  <Link key={item.id} href={`/opportunities/${item.id}`}>
                    #{item.id.slice(0, 4)}
                  </Link>
                ))}
              </span>
            );
          }),
        )}
      </div>
      <div className="matrix-axis-x">Effort →</div>
      {placed.some((p) => p.at === null) && (
        <p className="status-footnote">
          Some opportunities lack reviewed axis inputs and are listed below
          without a position.
        </p>
      )}
    </div>
  );
}

export default async function AnalysisPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  if (!(await readServerSession())) redirect("/login");
  const { id } = await params;
  const overview = await fetchWorkspaceJson(
    `analyses/${id}`,
    parseAnalysisOverview,
    null,
  );
  if (
    overview === null ||
    overview.task !== "opportunity_analysis" ||
    overview.status !== "completed"
  )
    notFound();
  const opportunities = await fetchWorkspaceJson(
    `analyses/${id}/opportunities`,
    parseOpportunityList,
    [],
  );
  return (
    <div className="page-content">
      <section className="page-intro">
        <div className="intro">
          <p className="eyebrow">
            <span className="eyebrow-line" />
            OPPORTUNITY ANALYSIS
          </p>
          <h1>
            Scored by rules.
            <br />
            <span>Explained by evidence.</span>
          </h1>
          <p className="intro-description">
            Every number below comes from deterministic rules over reviewed
            facts — never from a model’s opinion. Confidence and score are
            separate measures.
          </p>
        </div>
      </section>
      <div className="workflow-section">
        <ExportReportButton analysisId={id} />
      </div>
      <section aria-label="Pain points" className="workflow-section">
        <h2 className="quiet-label">PAIN POINTS</h2>
        {overview.pain_points.length === 0 ? (
          <p className="intro-description">
            No pain-point patterns matched the reviewed facts.
          </p>
        ) : (
          <div className="guide-grid">
            {overview.pain_points.map((point) => (
              <article
                key={`${point.category}-${point.description}`}
                className="guide-card"
              >
                <header className="principle-heading">
                  <h3>{point.category.replaceAll("_", " ")}</h3>
                  <span className="evidence-chip">{point.severity}</span>
                </header>
                <p>{point.description}</p>
                <p className="status-footnote">
                  confidence {point.confidence} · evidence:{" "}
                  {point.evidence_refs.join(", ")}
                </p>
              </article>
            ))}
          </div>
        )}
      </section>
      <section aria-label="Portfolio matrix" className="workflow-section">
        <h2 className="quiet-label">IMPACT VS EFFORT</h2>
        <Matrix opportunities={opportunities} />
      </section>
      <section aria-label="Scored opportunities" className="workflow-section">
        <h2 className="quiet-label">OPPORTUNITIES</h2>
        {opportunities.length === 0 ? (
          <div className="empty-state">
            <h3>No actionable candidate</h3>
            <p>
              The reviewed evidence did not support any automation proposal —
              nothing was invented.
            </p>
          </div>
        ) : (
          <div className="guide-grid">
            {opportunities.map((item) => (
              <article key={item.id} className="guide-card">
                <h3>
                  <Link href={`/opportunities/${item.id}`}>{item.title}</Link>
                </h3>
                <p className="status-footnote">
                  {item.result_state === "final"
                    ? "final"
                    : item.result_state === "provisional"
                      ? "provisional"
                      : "insufficient evidence"}
                  {item.priority_band ? ` · ${item.priority_band}` : ""}
                  {" · confidence "}
                  {item.confidence}
                </p>
                {item.total_score !== null && (
                  <p className="opportunity-score">
                    {item.total_score.toFixed(1)}
                  </p>
                )}
                {item.governance_review && (
                  <p className="evidence-chip governance">
                    governance review suggested (risk ≥ 70)
                  </p>
                )}
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
