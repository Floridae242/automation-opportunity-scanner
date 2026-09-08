"use client";

import { useState, type FormEvent } from "react";
import type { ProcessVersion } from "./contract";

type Comparison = {
  base: { version_no: number };
  target: { version_no: number };
  changes: { source_summary_changed: boolean };
};

export function VersionCompare({
  versions,
}: {
  versions: readonly ProcessVersion[];
}) {
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [error, setError] = useState<string | null>(null);
  if (versions.length < 2) return null;

  async function compare(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const target = String(form.get("target") || "");
    const against = String(form.get("against") || "");
    if (!target || !against || target === against)
      return setError("Choose two different versions.");
    const response = await fetch(
      `/api/scanner/process-versions/${target}/compare?against=${against}`,
    );
    const data = await response.json().catch(() => null);
    if (!response.ok || !data)
      return setError("The versions could not be compared.");
    setError(null);
    setComparison(data as Comparison);
  }

  return (
    <section className="guide-card compact" aria-label="Compare versions">
      <h2>Compare versions</h2>
      <form onSubmit={compare}>
        <label>
          Newer version
          <select name="target" defaultValue={versions[0].id}>
            {versions.map((version) => (
              <option key={version.id} value={version.id}>
                v{version.version_no}
              </option>
            ))}
          </select>
        </label>
        <label>
          Earlier version
          <select name="against" defaultValue={versions[1].id}>
            {versions.map((version) => (
              <option key={version.id} value={version.id}>
                v{version.version_no}
              </option>
            ))}
          </select>
        </label>
        <button className="button button-secondary" type="submit">
          Compare
        </button>
      </form>
      {error && (
        <p role="alert" className="auth-error">
          {error}
        </p>
      )}
      {comparison && (
        <p>
          v{comparison.base.version_no} → v{comparison.target.version_no}:{" "}
          {comparison.changes.source_summary_changed
            ? "summary changed"
            : "summary unchanged"}
        </p>
      )}
    </section>
  );
}
