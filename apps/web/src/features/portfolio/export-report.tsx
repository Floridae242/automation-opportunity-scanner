"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function ExportReportButton({ analysisId }: { analysisId: string }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function exportReport() {
    setPending(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/scanner/analyses/${analysisId}/reports`,
        { method: "POST" },
      );
      const body = await response.json().catch(() => null);
      if (!response.ok) {
        setError(
          typeof body?.error?.message === "string"
            ? body.error.message
            : "Export failed. Try again.",
        );
        return;
      }
      router.push(`/analyses/${analysisId}/report`);
    } catch {
      setError("Export failed. Try again.");
    } finally {
      setPending(false);
    }
  }
  return (
    <div className="report-actions">
      <button
        type="button"
        className="button button-primary"
        onClick={exportReport}
        disabled={pending}
      >
        {pending ? "Freezing facts…" : "Export executive report"}
      </button>
      {error && (
        <p role="alert" className="auth-error">
          {error}
        </p>
      )}
    </div>
  );
}
