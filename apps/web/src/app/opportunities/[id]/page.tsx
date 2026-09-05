import { notFound, redirect } from "next/navigation";
import { readServerSession } from "@/features/auth/session";
import { fetchWorkspaceJson } from "@/features/intake/workspace-data";
import { parseOpportunityDetail } from "@/features/portfolio/contract";

export const dynamic = "force-dynamic";

const WEIGHTS: Record<string, string> = {
  business_value: "20%",
  time_saving: "20%",
  repetitiveness: "15%",
  feasibility: "15%",
  error_reduction: "10%",
  integration_ease: "10%",
  risk_safety: "10%",
};

export default async function OpportunityPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  if (!(await readServerSession())) redirect("/login");
  const { id } = await params;
  const opportunity = await fetchWorkspaceJson(
    `opportunities/${id}`,
    parseOpportunityDetail,
    null,
  );
  if (opportunity === null) notFound();
  return (
    <div className="page-content">
      <section className="page-intro">
        <div className="intro">
          <p className="eyebrow">
            <span className="eyebrow-line" />
            OPPORTUNITY DETAIL
          </p>
          <h1>{opportunity.title}</h1>
          <p className="intro-description">
            {opportunity.result_state === "final"
              ? "Final score — all dimensions computed from reviewed facts."
              : opportunity.result_state === "provisional"
                ? `Provisional score — ${opportunity.score.coverage ?? 0}% of dimensions have reviewed evidence. Add the missing facts to complete it.`
                : "Insufficient evidence — no score was published rather than guessing."}
          </p>
        </div>
        {opportunity.governance_review && (
          <p className="evidence-chip governance">
            governance review suggested (risk ≥ 70)
          </p>
        )}
      </section>
      <section aria-label="Score breakdown" className="workflow-section">
        <h2 className="quiet-label">
          SCORE BREAKDOWN · {opportunity.score.scoring_version}
        </h2>
        <div className="table-scroll">
          <table className="score-table">
            <thead>
              <tr>
                <th>Dimension</th>
                <th>Weight</th>
                <th>Score</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(WEIGHTS).map(([name, weight]) => (
                <tr key={name}>
                  <td>{name.replaceAll("_", " ")}</td>
                  <td>{weight}</td>
                  <td>
                    {opportunity.score.dimensions[name] ?? "Not provided"}
                  </td>
                  <td className="evidence-cell">
                    {(opportunity.score.dimension_evidence[name] ?? []).join(
                      "; ",
                    ) || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan={2}>Total ({opportunity.score.scoring_version})</td>
                <td>{opportunity.score.total ?? "—"}</td>
                <td>
                  confidence {opportunity.confidence} ·{" "}
                  {opportunity.score.confidence_version}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </section>
      <section aria-label="Scope" className="workflow-section">
        <h2 className="quiet-label">SCOPE</h2>
        <div className="evidence-rail">
          <h3>Referenced steps and patterns</h3>
          <ul>
            {Array.isArray(opportunity.scope.step_keys) ? (
              (opportunity.scope.step_keys as readonly unknown[]).map((key) => (
                <li key={String(key)}>step {String(key)}</li>
              ))
            ) : (
              <li>no step references</li>
            )}
            {Array.isArray(opportunity.scope.pain_categories)
              ? (opportunity.scope.pain_categories as readonly unknown[]).map(
                  (category) => (
                    <li key={String(category)}>
                      pattern: {String(category).replaceAll("_", " ")}
                    </li>
                  ),
                )
              : null}
          </ul>
        </div>
      </section>
    </div>
  );
}
