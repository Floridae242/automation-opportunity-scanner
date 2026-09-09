"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { callScannerApi, parseMetricsInput } from "./client-api";

const PERIODS = ["hour", "day", "week", "month", "quarter", "year"] as const;

export function IntakeForm({ processId }: { processId: string }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [savedVersion, setSavedVersion] = useState<number | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    setSavedVersion(null);
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const result = await callScannerApi(
      "POST",
      `processes/${processId}/intake`,
      {
        description: String(form.get("description") ?? ""),
        metrics: parseMetricsInput(form),
      },
    );
    setPending(false);
    if (!result.ok) return setError(result.message);
    setSavedVersion((previous) => (previous ?? 0) + 1);
    formElement.reset();
    router.refresh();
  }

  return (
    <form
      onSubmit={submit}
      className="guide-card intake-form"
      aria-label="Process intake"
    >
      <label htmlFor="intake-description">Workflow description</label>
      <textarea
        id="intake-description"
        name="description"
        rows={5}
        required
        maxLength={20000}
        placeholder="Describe who does what, in which systems, in what order…"
      />
      <p className="margin-note">
        Leave any metric blank if unknown — blanks stay “Not provided” and are
        never guessed.
      </p>
      <div className="metrics-grid">
        <fieldset>
          <legend>Frequency</legend>
          <input
            type="number"
            name="frequency_value"
            min="0.001"
            step="any"
            placeholder="value"
            aria-label="Frequency value"
          />
          <select
            name="frequency_period"
            aria-label="Frequency period"
            defaultValue=""
          >
            <option value="">period</option>
            {PERIODS.map((period) => (
              <option key={period} value={period}>
                {period}
              </option>
            ))}
          </select>
        </fieldset>
        <label>
          Duration (minutes)
          <input
            type="number"
            name="duration_minutes"
            min="0.001"
            step="any"
            placeholder="Not provided"
          />
        </label>
        <label>
          Error rate (0–1)
          <input
            type="number"
            name="error_rate"
            min="0"
            max="1"
            step="0.001"
            placeholder="Not provided"
          />
        </label>
        <label>
          Rework rate (0–1)
          <input
            type="number"
            name="rework_rate"
            min="0"
            max="1"
            step="0.001"
            placeholder="Not provided"
          />
        </label>
        <label>
          SLA
          <input name="sla" maxLength={200} placeholder="Not provided" />
        </label>
        <label>
          Systems (comma separated)
          <input name="systems" placeholder="Not provided" />
        </label>
        <label>
          Approvals required
          <input
            type="number"
            name="approvals_required"
            min="0"
            max="999"
            step="1"
            placeholder="Not provided"
          />
        </label>
        <label>
          Sensitivity
          <select name="sensitivity" defaultValue="">
            <option value="">Not provided</option>
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
            <option value="restricted">restricted</option>
          </select>
        </label>
        <label>
          Loaded hourly cost
          <input min="0" name="loaded_hourly_cost" step="0.01" type="number" />
        </label>
        <label>
          Currency (ISO)
          <input maxLength={3} name="currency" placeholder="THB" />
        </label>
        <label>
          Monthly operating cost
          <input
            min="0"
            name="monthly_operating_cost"
            step="0.01"
            type="number"
          />
        </label>
        <label>
          Implementation cost
          <input min="0" name="implementation_cost" step="0.01" type="number" />
        </label>
      </div>
      {error && (
        <p role="alert" className="auth-error">
          {error}
        </p>
      )}
      {savedVersion !== null && (
        <p role="status" className="intake-saved">
          Intake saved as a new draft version.
        </p>
      )}
      <button
        type="submit"
        className="button button-primary"
        disabled={pending}
      >
        {pending ? "Saving…" : "Save intake draft"}
      </button>
    </form>
  );
}
