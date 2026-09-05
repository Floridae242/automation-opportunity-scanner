"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { callScannerApi } from "./client-api";
import type { VersionDetail } from "./contract";

export function StepReviewEditor({ version }: { version: VersionDetail }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<"save" | "review" | null>(null);
  const reviewed = version.review_status === "reviewed";

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (reviewed) return;
    setPending("save");
    setError(null);
    const form = new FormData(event.currentTarget);
    const steps = version.steps.map((step) => {
      const name = String(form.get(`name.${step.step_key}`) ?? step.name);
      const duration = String(form.get(`duration.${step.step_key}`) ?? "");
      const actor = String(form.get(`actor.${step.step_key}`) ?? "");
      const system = String(form.get(`system.${step.step_key}`) ?? "");
      const patch: Record<string, unknown> = {
        step_key: step.step_key,
        name: name || step.name,
      };
      if (duration !== "" && Number(duration) >= 0)
        patch.duration_minutes = Number(duration);
      if (actor !== "") patch.actor = actor;
      if (system !== "") patch.system = system;
      const manual = String(form.get(`manual.${step.step_key}`) ?? "");
      if (manual === "yes") patch.manual = true;
      if (manual === "no") patch.manual = false;
      return patch;
    });
    const result = await callScannerApi(
      "PATCH",
      `process-versions/${version.id}`,
      { steps },
    );
    setPending(null);
    if (!result.ok) return setError(result.message);
    router.refresh();
  }

  async function review() {
    setPending("review");
    setError(null);
    const result = await callScannerApi(
      "POST",
      `process-versions/${version.id}/review`,
    );
    setPending(null);
    if (!result.ok) return setError(result.message);
    router.refresh();
  }

  return (
    <form
      onSubmit={save}
      className="guide-card review-card"
      aria-label="Review extracted steps"
    >
      <header className="principle-heading">
        <h3>Review draft v{version.version_no}</h3>
        <span className={reviewed ? "evidence-chip" : "outline-tag"}>
          {reviewed ? "reviewed — immutable" : "draft — editable"}
        </span>
      </header>
      <ol className="step-list">
        {version.steps.map((step) => (
          <li key={step.step_id}>
            <span className="stage-number">{step.sequence_no}</span>
            <label className="sr-only" htmlFor={`name-${step.step_key}`}>
              Step {step.step_key} name
            </label>
            <input
              id={`name-${step.step_key}`}
              name={`name.${step.step_key}`}
              defaultValue={step.name}
              maxLength={300}
              required
              disabled={reviewed}
            />
            <label className="sr-only" htmlFor={`actor-${step.step_key}`}>
              Actor
            </label>
            <input
              id={`actor-${step.step_key}`}
              name={`actor.${step.step_key}`}
              defaultValue={step.actor ?? ""}
              placeholder="Actor — not provided"
              disabled={reviewed}
              maxLength={200}
            />
            <label className="sr-only" htmlFor={`system-${step.step_key}`}>
              System
            </label>
            <input
              id={`system-${step.step_key}`}
              name={`system.${step.step_key}`}
              defaultValue={step.system ?? ""}
              placeholder="System — not provided"
              disabled={reviewed}
              maxLength={200}
            />
            <label className="sr-only" htmlFor={`duration-${step.step_key}`}>
              Minutes
            </label>
            <input
              id={`duration-${step.step_key}`}
              name={`duration.${step.step_key}`}
              type="number"
              min="0"
              step="0.1"
              defaultValue={step.duration_minutes ?? ""}
              placeholder="min — not provided"
              disabled={reviewed}
            />
            <label className="sr-only" htmlFor={`manual-${step.step_key}`}>
              Manual?
            </label>
            <select
              id={`manual-${step.step_key}`}
              name={`manual.${step.step_key}`}
              defaultValue=""
              disabled={reviewed}
            >
              <option value="">manual — unchanged</option>
              <option value="yes" selected={step.manual === true}>
                manual: yes
              </option>
              <option value="no" selected={step.manual === false}>
                manual: no
              </option>
            </select>
            {step.evidence_refs.length > 0 && (
              <small className="status-footnote">
                evidence: {step.evidence_refs.join(", ")}
              </small>
            )}
          </li>
        ))}
      </ol>
      {version.evidence.length > 0 && (
        <p className="margin-note">
          Source: “{version.evidence[0].excerpt.slice(0, 120)}
          {version.evidence[0].excerpt.length > 120 ? "…" : ""}”
        </p>
      )}
      {error && (
        <p role="alert" className="auth-error">
          {error}
        </p>
      )}
      {!reviewed && (
        <div className="review-actions">
          <button
            type="submit"
            className="button button-secondary"
            disabled={pending !== null}
          >
            {pending === "save" ? "Saving…" : "Save corrections"}
          </button>
          <button
            type="button"
            className="button button-primary"
            onClick={review}
            disabled={pending !== null || version.steps.length === 0}
          >
            {pending === "review" ? "Confirming…" : "Mark reviewed"}
          </button>
        </div>
      )}
    </form>
  );
}
