"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

export type AnalysisStatus = {
  analysis_id: string;
  status: "queued" | "running" | "completed" | "failed";
  error_code: string | null;
  draft_version_id: string | null;
};

function describeFailure(code: string | null): string {
  if (code === "AI_RATE_LIMITED")
    return "The AI service is busy. Please retry in a moment.";
  if (code === "AI_UNAVAILABLE")
    return "The AI service is unavailable. You can still edit the intake manually.";
  return "The extraction result was rejected by validation. Your intake is preserved — retry or continue by hand.";
}

export function ExtractionPanel({ processId }: { processId: string }) {
  const router = useRouter();
  const [analysis, setAnalysis] = useState<AnalysisStatus | null>(null);
  const [pending, setPending] = useState(false);
  const poll = useRef<ReturnType<typeof setInterval> | null>(null);
  const stop = useCallback(() => {
    if (poll.current !== null) clearInterval(poll.current);
    poll.current = null;
  }, []);
  useEffect(() => stop, [stop]);

  async function start() {
    setPending(true);
    const response = await fetch(
      `/api/scanner/processes/${processId}/analyses`,
      { method: "POST" },
    );
    const body = await response.json().catch(() => null);
    setPending(false);
    if (!response.ok || typeof body?.analysis_id !== "string") return;
    setAnalysis({
      analysis_id: body.analysis_id,
      status: body.status ?? "queued",
      error_code: null,
      draft_version_id: null,
    });
    let elapsed = 0;
    poll.current = setInterval(async () => {
      elapsed += 1500;
      try {
        const statusResponse = await fetch(
          `/api/scanner/analyses/${body.analysis_id}`,
          { cache: "no-store" },
        );
        if (!statusResponse.ok) return;
        const status: AnalysisStatus = await statusResponse.json();
        setAnalysis(status);
        if (
          status.status === "completed" ||
          status.status === "failed" ||
          elapsed > 60_000
        ) {
          stop();
          if (status.status === "completed") router.refresh();
        }
      } catch {
        if (elapsed > 60_000) stop();
      }
    }, 1500);
  }

  const inFlight =
    analysis !== null &&
    (analysis.status === "queued" || analysis.status === "running");
  return (
    <section
      className="guide-card compact extraction-panel"
      aria-label="AI extraction"
    >
      <div>
        <h3>Extract a process draft</h3>
        <p>
          {inFlight
            ? `Analysis is ${analysis.status}…`
            : analysis?.status === "failed"
              ? describeFailure(analysis.error_code)
              : "Turn your intake into reviewable steps. AI output is always a draft you must review."}
        </p>
      </div>
      <button
        type="button"
        className="button button-primary"
        onClick={start}
        disabled={pending || inFlight}
      >
        {inFlight
          ? "Analyzing…"
          : analysis?.status === "failed"
            ? "Retry extraction"
            : "Run extraction"}
      </button>
      {inFlight && <progress aria-label="Extraction progress" />}
    </section>
  );
}
