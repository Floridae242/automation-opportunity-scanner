"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function OpportunityAnalyzer({ processId }: { processId: string }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function run() {
    setPending(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/scanner/processes/${processId}/analyses`,
        { method: "POST" },
      );
      const body = await response.json().catch(() => null);
      if (!response.ok || typeof body?.analysis_id !== "string") {
        setError(
          typeof body?.error?.message === "string"
            ? body.error.message
            : "The opportunity engine is unavailable. Try again.",
        );
        return;
      }
      router.push(`/analyses/${body.analysis_id}`);
    } catch {
      setError("The opportunity engine is unavailable. Try again.");
    } finally {
      setPending(false);
    }
  }
  return (
    <section className="guide-card compact" aria-label="Opportunity analysis">
      <div>
        <h3>This version is reviewed</h3>
        <p>
          Score it deterministically and surface candidate automation
          opportunities.
        </p>
      </div>
      <button
        type="button"
        className="button button-primary"
        onClick={run}
        disabled={pending}
      >
        {pending ? "Analyzing…" : "Analyze opportunities"}
      </button>
      {error && (
        <p role="alert" className="auth-error">
          {error}
        </p>
      )}
    </section>
  );
}
