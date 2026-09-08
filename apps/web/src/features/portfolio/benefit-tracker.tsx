"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { callScannerApi } from "@/features/intake/client-api";

export type BenefitRealization = Readonly<{
  id: string;
  period: string;
  hours_saved: number | null;
  monetary_benefit: number | null;
  notes: string | null;
}>;

export function BenefitTracker({
  opportunityId,
  benefits,
  editable,
}: {
  opportunityId: string;
  benefits: readonly BenefitRealization[];
  editable: boolean;
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const hours = String(form.get("hours_saved") || "");
    const monetary = String(form.get("monetary_benefit") || "");
    if (!hours && !monetary) {
      setError("Record hours saved, monetary benefit, or both.");
      return;
    }
    setPending(true);
    setError(null);
    const result = await callScannerApi(
      "POST",
      `opportunities/${opportunityId}/benefits`,
      {
        period: String(form.get("period")),
        hours_saved: hours ? Number(hours) : null,
        monetary_benefit: monetary ? Number(monetary) : null,
        notes: String(form.get("notes") || "").trim() || null,
      },
    );
    setPending(false);
    if (!result.ok) return setError(result.message);
    router.refresh();
  }

  return (
    <section aria-label="Benefit realization" className="workflow-section">
      <h2 className="quiet-label">ACTUAL BENEFITS</h2>
      <article className="guide-card">
        <p>
          Record observed results separately from the estimate above. One entry
          is kept for each calendar month.
        </p>
        {benefits.length === 0 ? (
          <p className="margin-note">No actual benefits recorded yet.</p>
        ) : (
          <div className="table-scroll">
            <table className="score-table">
              <thead>
                <tr>
                  <th>Month</th>
                  <th>Hours saved</th>
                  <th>Monetary benefit</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {benefits.map((benefit) => (
                  <tr key={benefit.id}>
                    <td>{benefit.period}</td>
                    <td>{benefit.hours_saved ?? "—"}</td>
                    <td>{benefit.monetary_benefit ?? "—"}</td>
                    <td>{benefit.notes ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {editable ? (
          <form className="intake-form" onSubmit={submit}>
            <label htmlFor="benefit-period">
              Month
              <input id="benefit-period" name="period" required type="month" />
            </label>
            <label htmlFor="hours-saved">
              Actual hours saved
              <input
                id="hours-saved"
                min="0"
                name="hours_saved"
                step="0.1"
                type="number"
              />
            </label>
            <label htmlFor="monetary-benefit">
              Actual monetary benefit
              <input
                id="monetary-benefit"
                min="0"
                name="monetary_benefit"
                step="0.01"
                type="number"
              />
            </label>
            <label htmlFor="benefit-notes">
              Evidence or notes
              <textarea id="benefit-notes" maxLength={2000} name="notes" />
            </label>
            {error && (
              <p className="auth-error" role="alert">
                {error}
              </p>
            )}
            <button
              className="button button-secondary"
              disabled={pending}
              type="submit"
            >
              {pending ? "Recording…" : "Record actual benefit"}
            </button>
          </form>
        ) : (
          <p className="margin-note">
            Only owners, administrators, analysts, and reviewers can record
            actual benefits.
          </p>
        )}
      </article>
    </section>
  );
}
