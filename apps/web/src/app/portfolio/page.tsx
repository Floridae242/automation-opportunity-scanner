import Link from "next/link";
import { redirect } from "next/navigation";
import { readServerSession } from "@/features/auth/session";
import { fetchWorkspaceJson } from "@/features/intake/workspace-data";
import { parseOpportunityList } from "@/features/portfolio/contract";

function parsePortfolio(value: unknown) {
  if (typeof value !== "object" || value === null) return null;
  const items = (value as { items?: unknown }).items;
  return parseOpportunityList(items);
}

export const dynamic = "force-dynamic";

function matrixCell(impact: number | null, effort: number | null) {
  if (impact === null || effort === null) return null;
  return {
    row: 4 - Math.min(4, Math.floor(impact / 20)),
    col: Math.min(4, Math.floor(effort / 20)),
  };
}

export default async function PortfolioPage({
  searchParams,
}: {
  searchParams: Promise<{
    min_score?: string;
    min_confidence?: string;
    department?: string;
    category?: string;
    result_state?: string;
    governance_review?: string;
  }>;
}) {
  if (!(await readServerSession())) redirect("/login");
  const filters = await searchParams;
  const query = new URLSearchParams();
  for (const key of ["min_score", "min_confidence"] as const) {
    const value = Number(filters[key]);
    if (Number.isFinite(value) && value >= 0 && value <= 100) {
      query.set(key, String(value));
    }
  }
  if (filters.department && filters.department.length <= 200) {
    query.set("department", filters.department);
  }
  if (filters.category && /^[a-z_]{1,64}$/.test(filters.category)) {
    query.set("category", filters.category);
  }
  if (
    filters.result_state === "final" ||
    filters.result_state === "provisional" ||
    filters.result_state === "insufficient_evidence"
  ) {
    query.set("result_state", filters.result_state);
  }
  if (
    filters.governance_review === "true" ||
    filters.governance_review === "false"
  ) {
    query.set("governance_review", filters.governance_review);
  }
  const opportunities = await fetchWorkspaceJson(
    `portfolio/opportunities?${query.toString()}`,
    parsePortfolio,
    [],
  );
  return (
    <div className="page-content">
      <section className="page-intro">
        <p className="eyebrow">
          <span className="eyebrow-line" />
          PORTFOLIO
        </p>
        <h1>
          Prioritize opportunities.
          <br />
          <span>Keep the evidence visible.</span>
        </h1>
        <p className="intro-description">
          Organization-wide opportunities ranked by the stored deterministic
          score. Missing axes remain unplaced.
        </p>
      </section>
      <section
        className="workflow-section"
        aria-label="Impact versus effort matrix"
      >
        <h2 className="quiet-label">IMPACT VS EFFORT</h2>
        <div
          className="matrix-grid"
          role="img"
          aria-label="Organization impact versus effort matrix"
        >
          <div className="matrix-axis-y">Impact</div>
          <div className="matrix-cells">
            {Array.from({ length: 5 }, (_, row) =>
              Array.from({ length: 5 }, (_, col) => {
                const hits = opportunities.filter((item) => {
                  const cell = matrixCell(item.axes.impact, item.axes.effort);
                  return cell?.row === row && cell.col === col;
                });
                return (
                  <span
                    key={`${row}-${col}`}
                    className={
                      hits.length ? "matrix-cell filled" : "matrix-cell"
                    }
                  >
                    {hits.map((item) => (
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
        </div>
        {opportunities.some(
          (item) => matrixCell(item.axes.impact, item.axes.effort) === null,
        ) && (
          <p className="status-footnote">
            Some opportunities lack reviewed axis inputs and remain unplaced.
          </p>
        )}
      </section>
      <section
        className="workflow-section"
        aria-label="Portfolio opportunities"
      >
        <h2 className="quiet-label">RANKED OPPORTUNITIES</h2>
        <form className="metrics-grid" method="get">
          <label>
            Minimum score
            <input
              name="min_score"
              type="number"
              min="0"
              max="100"
              defaultValue={filters.min_score}
            />
          </label>
          <label>
            Minimum confidence
            <input
              name="min_confidence"
              type="number"
              min="0"
              max="100"
              defaultValue={filters.min_confidence}
            />
          </label>
          <label>
            Department
            <input
              name="department"
              maxLength={200}
              defaultValue={filters.department}
            />
          </label>
          <label>
            Pain category
            <input
              name="category"
              maxLength={64}
              pattern="[a-z_]+"
              defaultValue={filters.category}
            />
          </label>
          <label>
            Result state
            <select
              name="result_state"
              defaultValue={filters.result_state ?? ""}
            >
              <option value="">Any</option>
              <option value="final">Final</option>
              <option value="provisional">Provisional</option>
              <option value="insufficient_evidence">
                Insufficient evidence
              </option>
            </select>
          </label>
          <label>
            Governance review
            <select
              name="governance_review"
              defaultValue={filters.governance_review ?? ""}
            >
              <option value="">Any</option>
              <option value="true">Suggested</option>
              <option value="false">Not suggested</option>
            </select>
          </label>
          <button className="button button-secondary" type="submit">
            Apply filters
          </button>
          <Link className="text-link" href="/portfolio">
            Reset
          </Link>
        </form>
        {opportunities.length === 0 ? (
          <div className="empty-state">
            <h3>No scored opportunities yet</h3>
            <p>
              Review a process and run opportunity analysis to populate this
              portfolio.
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
                  {item.priority_band ?? "unbanded"} · confidence{" "}
                  {item.confidence}
                </p>
                <p>
                  {item.axes.impact === null || item.axes.effort === null
                    ? "Impact/effort: insufficient reviewed evidence"
                    : `Impact ${item.axes.impact.toFixed(0)} · effort ${item.axes.effort.toFixed(0)}`}
                </p>
                {item.total_score !== null && (
                  <p className="opportunity-score">
                    {item.total_score.toFixed(1)}
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
