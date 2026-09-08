"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { callScannerApi } from "@/features/intake/client-api";

const labels: Record<string, string> = {
  business_value: "Business value",
  time_saving: "Time saving",
  repetitiveness: "Repetitiveness",
  feasibility: "Feasibility",
  error_reduction: "Error reduction",
  integration_ease: "Integration ease",
  risk_safety: "Risk and safety",
};

export type ScoringConfiguration = {
  id: string;
  version_no: number;
  weights: Record<string, number>;
};

export function ScoringSettings({
  configuration,
  editable,
}: {
  configuration: ScoringConfiguration | null;
  editable: boolean;
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  if (!configuration) {
    return <p className="auth-error">Scoring settings are unavailable for this workspace.</p>;
  }
  const activeConfiguration = configuration;
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const weights = Object.fromEntries(
      Object.keys(activeConfiguration.weights).map((key) => [key, Number(form.get(key)) / 100]),
    );
    setPending(true);
    setError(null);
    const result = await callScannerApi("POST", "scoring-configurations", { weights });
    setPending(false);
    if (!result.ok) return setError(result.message);
    router.refresh();
  }
  return (
    <section className="guide-card intake-form" aria-label="Scoring weights">
      <p className="eyebrow">SCORING CONFIGURATION</p>
      <h2>Version {activeConfiguration.version_no}</h2>
      <p>
        New analyses use the saved weights. Existing analysis and report snapshots keep their
        original configuration.
      </p>
      <form onSubmit={submit}>
        {Object.entries(activeConfiguration.weights).map(([key, weight]) => (
          <label key={key} htmlFor={`weight-${key}`}>
            {labels[key] ?? key}
            <input
              id={`weight-${key}`}
              name={key}
              type="number"
              min="0"
              max="100"
              step="1"
              defaultValue={weight * 100}
              disabled={!editable || pending}
            />
          </label>
        ))}
        {editable ? (
          <button className="button button-primary" disabled={pending} type="submit">
            {pending ? "Saving…" : "Save as new version"}
          </button>
        ) : (
          <p className="margin-note">Only owners and administrators can change scoring weights.</p>
        )}
        {error && <p className="auth-error" role="alert">{error}</p>}
      </form>
    </section>
  );
}
