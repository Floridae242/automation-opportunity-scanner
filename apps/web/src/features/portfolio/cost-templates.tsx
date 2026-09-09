"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { callScannerApi } from "@/features/intake/client-api";

export type CostTemplate = Readonly<{
  id: string;
  name: string;
  currency: string;
  loaded_hourly_cost: number;
  monthly_operating_cost: number;
  implementation_cost: number;
}>;

export function CostTemplates({
  templates,
  editable,
}: {
  templates: readonly CostTemplate[];
  editable: boolean;
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setPending(true);
    setError(null);

    const result = await callScannerApi("POST", "cost-templates", {
      name: String(form.get("name") || "").trim(),
      currency: String(form.get("currency") || "")
        .trim()
        .toUpperCase(),
      loaded_hourly_cost: Number(form.get("loaded_hourly_cost")),
      monthly_operating_cost: Number(form.get("monthly_operating_cost")),
      implementation_cost: Number(form.get("implementation_cost")),
    });

    setPending(false);
    if (!result.ok) {
      setError(result.message);
      return;
    }

    router.refresh();
  }

  return (
    <section className="guide-card intake-form" aria-label="Cost templates">
      <p className="eyebrow">COST TEMPLATES</p>
      <h2>Standardize ROI assumptions</h2>
      {templates.map((template) => (
        <p key={template.id}>
          <strong>{template.name}</strong> · {template.currency}{" "}
          {template.loaded_hourly_cost}/h
        </p>
      ))}
      {editable ? (
        <form onSubmit={submit}>
          <label>
            Name
            <input name="name" required maxLength={100} />
          </label>
          <label>
            Currency
            <input name="currency" required maxLength={3} />
          </label>
          <label>
            Loaded hourly cost
            <input name="loaded_hourly_cost" required type="number" min="0" />
          </label>
          <label>
            Monthly operating cost
            <input
              name="monthly_operating_cost"
              required
              type="number"
              min="0"
            />
          </label>
          <label>
            Implementation cost
            <input name="implementation_cost" required type="number" min="0" />
          </label>
          {error && <p role="alert">{error}</p>}
          <button disabled={pending} type="submit">
            Save cost template
          </button>
        </form>
      ) : (
        <p>Only owners and administrators can create cost templates.</p>
      )}
    </section>
  );
}
