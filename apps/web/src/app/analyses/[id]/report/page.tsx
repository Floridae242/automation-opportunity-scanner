import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { readServerSession } from "@/features/auth/session";
import { fetchWorkspaceJson } from "@/features/intake/workspace-data";
import { parseReportEnvelope } from "@/features/portfolio/contract";

export const dynamic = "force-dynamic";

export default async function ReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  if (!(await readServerSession())) redirect("/login");
  const { id } = await params;
  const snapshot = await fetchWorkspaceJson(
    `analyses/${id}/report`,
    parseReportEnvelope,
    null,
  );
  if (snapshot === null) notFound();
  return (
    <div className="page-content">
      <section className="page-intro">
        <div className="intro">
          <p className="eyebrow">
            <span className="eyebrow-line" />
            EXECUTIVE REPORT
          </p>
          <h1>{snapshot.process ?? "Process"} — opportunity report</h1>
          <p className="intro-description">
            Frozen snapshot from reviewed facts ({snapshot.schema_version});
            re-analysis creates a new report, never edits this one.{" "}
            {snapshot.review_status === "reviewed"
              ? "Source version was human-reviewed."
              : "Source version was not reviewed at export time."}
          </p>
        </div>
        <div className="button-row">
          <a
            className="button button-secondary"
            href={`/api/scanner/reports/${snapshot.report_id}/pdf`}
          >
            Download PDF
          </a>
          <a
            className="button button-secondary"
            href={`/api/scanner/reports/${snapshot.report_id}/docx`}
          >
            Download DOCX
          </a>
          <a
            className="button button-secondary"
            href={`/api/scanner/reports/${snapshot.report_id}/slides`}
          >
            Download slides
          </a>
        </div>
      </section>
      <section aria-label="Pain points">
        <h2 className="quiet-label">PAIN POINTS</h2>
        <ul className="check-list">
          {snapshot.pain_points.map((point) => (
            <li key={`${point.category}-${point.description}`}>
              [{point.severity}] {point.category.replaceAll("_", " ")} —{" "}
              {point.description}
            </li>
          ))}
        </ul>
      </section>
      {snapshot.opportunities.map((opportunity, index) => (
        <article key={index} className="guide-card">
          <header className="principle-heading">
            <h2>
              {index + 1}. {String(opportunity.title ?? "Opportunity")}
            </h2>
            <span className="evidence-chip">
              {String(opportunity.priority_band ?? "unbanded")}
            </span>
          </header>
          <p>
            Score {String(opportunity.score ?? "—")} (
            {String(opportunity.result_state ?? "")}) · confidence{" "}
            {String(opportunity.confidence ?? "—")}
            {opportunity.governance_review === true
              ? " · governance review suggested"
              : ""}
          </p>
          {typeof opportunity.id === "string" && (
            <p>
              <Link href={`/opportunities/${opportunity.id}`}>
                Open full breakdown
              </Link>
            </p>
          )}
        </article>
      ))}
      <p className="margin-note">
        Labor savings are freed capacity, not automatic headcount reduction.
        Monetary figures need cost evidence entered by your team.
      </p>
    </div>
  );
}
