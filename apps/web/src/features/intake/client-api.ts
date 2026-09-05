export type ApiResult = { ok: true } | { ok: false; message: string };

export async function callScannerApi(
  method: "GET" | "POST" | "PATCH",
  path: string,
  body?: Record<string, unknown>,
): Promise<ApiResult> {
  try {
    const response = await fetch(`/api/scanner/${path}`, {
      method,
      headers: body ? { "content-type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
    if (response.ok) return { ok: true };
    const payload = await response.json().catch(() => null);
    const message = payload?.error?.message;
    return {
      ok: false,
      message:
        typeof message === "string"
          ? message
          : "Something went wrong. Please try again.",
    };
  } catch {
    return {
      ok: false,
      message: "We could not reach the workspace service. Try again.",
    };
  }
}

export function parseMetricsInput(form: FormData): Record<string, unknown> {
  const metrics: Record<string, unknown> = {};
  const frequency = Number(form.get("frequency_value"));
  const period = String(form.get("frequency_period") || "");
  if (
    form.get("frequency_value") &&
    !Number.isNaN(frequency) &&
    frequency > 0 &&
    period
  ) {
    metrics.frequency = { value: frequency, period };
  }
  const duration = Number(form.get("duration_minutes"));
  if (form.get("duration_minutes") && !Number.isNaN(duration) && duration > 0) {
    metrics.duration_minutes = duration;
  }
  const errorRate = String(form.get("error_rate") || "");
  if (errorRate !== "") {
    const parsed = Number(errorRate);
    if (!Number.isNaN(parsed) && parsed >= 0 && parsed <= 1)
      metrics.error_rate = parsed;
  }
  const reworkRate = String(form.get("rework_rate") || "");
  if (reworkRate !== "") {
    const parsed = Number(reworkRate);
    if (!Number.isNaN(parsed) && parsed >= 0 && parsed <= 1)
      metrics.rework_rate = parsed;
  }
  const sla = String(form.get("sla") || "").trim();
  if (sla) metrics.sla = sla.slice(0, 200);
  const systems = String(form.get("systems") || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 50);
  if (systems.length) metrics.systems = systems;
  const approvals = Number(form.get("approvals_required"));
  if (
    form.get("approvals_required") &&
    !Number.isNaN(approvals) &&
    approvals >= 0
  ) {
    metrics.approvals_required = Math.floor(approvals);
  }
  const sensitivity = String(form.get("sensitivity") || "");
  if (["low", "medium", "high", "restricted"].includes(sensitivity)) {
    metrics.sensitivity = sensitivity;
  }
  return metrics;
}

export function formatMetricValue(value: unknown): string {
  if (value === null || value === undefined) return "Not provided";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    if (typeof record.value === "number" && typeof record.period === "string") {
      return `${record.value} per ${record.period}`;
    }
  }
  return String(value);
}
