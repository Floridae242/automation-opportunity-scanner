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
      {opportunity.recommendation && (
        <section aria-label="Recommendation" className="workflow-section">
          <h2 className="quiet-label">RECOMMENDED PATTERN</h2>
          <article className="guide-card">
            <header className="principle-heading">
              <h3>{opportunity.recommendation.patterns.join(" + ")}</h3>
              <span className="evidence-chip">
                confidence {opportunity.recommendation.confidence}
              </span>
            </header>
            <p>{opportunity.recommendation.rationale}</p>
            <h4>Prerequisites</h4>
            <ul className="check-list compact">
              {opportunity.recommendation.prerequisites.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <h4>Key risks</h4>
            <ul className="check-list compact">
              {opportunity.recommendation.risks.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <p className="margin-note">
              Human control: {opportunity.recommendation.human_control}
            </p>
            <details>
              <summary>Rejected alternatives</summary>
              <ul>
                {opportunity.recommendation.rejected_alternatives.map((alt) => (
                  <li key={alt.pattern}>
                    <strong>{alt.pattern}</strong> — {alt.why}
                  </li>
                ))}
              </ul>
            </details>
          </article>
        </section>
      )}
      {opportunity.roi && (
        <section aria-label="Time saving and ROI" className="workflow-section">
          <h2 className="quiet-label">TIME SAVING · ROI</h2>
          {opportunity.roi.available ? (
            <article className="guide-card">
              <table className="score-table">
                <thead>
                  <tr>
                    <th>Scenario</th>
                    <th>Net hours saved / month</th>
                    <th>Assumption source</th>
                  </tr>
                </thead>
                <tbody>
                  {(opportunity.roi.scenarios ?? []).map((scenario) => (
                    <tr key={scenario.automation_rate}>
                      <td>
                        {Math.round(scenario.automation_rate * 100)}% automated
                      </td>
                      <td>{scenario.net_hours_saved_month} h</td>
                      <td>{scenario.stated_by}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {opportunity.roi.monetary ? (
                <p>
                  Monetary: ROI {opportunity.roi.monetary.roi_percent}% ·
                  payback{" "}
                  {opportunity.roi.monetary.payback_months ?? "beyond horizon"}{" "}
                  months ({opportunity.roi.monetary.currency}, best scenario —
                  verify with owner).
                </p>
              ) : (
                <p className="margin-note">
                  Monetary ROI not calculated — missing{" "}
                  {(opportunity.roi.monetary_missing ?? []).join(", ") ||
                    "cost evidence"}
                  .
                </p>
              )}
              <p className="status-footnote">
                {opportunity.roi.assumptions_note}
              </p>
            </article>
          ) : (
            <p className="intro-description">
              Time saving unavailable — still missing:{" "}
              {(opportunity.roi.missing ?? []).join(", ")}. The system keeps it
              as “Not provided” instead of guessing.
            </p>
          )}
        </section>
      )}
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
