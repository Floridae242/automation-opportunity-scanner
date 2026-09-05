export type OpportunityRow = Readonly<{
  id: string;
  title: string;
  status: string;
  result_state: "final" | "provisional" | "insufficient_evidence";
  confidence: number;
  priority_band: string | null;
  total_score: number | null;
  scoring_version: string | null;
  axes: { version?: string; impact: number | null; effort: number | null };
  governance_review: boolean;
}>;

export type PainPoint = Readonly<{
  category: string;
  description: string;
  severity: "low" | "medium" | "high";
  confidence: "low" | "medium" | "high";
  evidence_refs: readonly string[];
}>;

export type AnalysisOverview = Readonly<{
  analysis_id: string;
  status: string;
  task: string;
  pain_points: readonly PainPoint[];
  error_code: string | null;
}>;

export type OpportunityDetail = Readonly<{
  id: string;
  analysis_run_id: string;
  priority_band: string | null;
  axes: OpportunityRow["axes"];
  governance_review: boolean;
  title: string;
  status: string;
  result_state: OpportunityRow["result_state"];
  confidence: number;
  scope: Record<string, unknown>;
  score: Readonly<{
    total: number | null;
    scoring_version: string;
    dimensions: Record<string, number | null>;
    dimension_evidence: Record<string, readonly string[]>;
    coverage: number | null;
    confidence_version: string;
  }>;
}>;

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const RESULT_STATES = new Set([
  "final",
  "provisional",
  "insufficient_evidence",
]);
const SEVERITIES = new Set(["low", "medium", "high"]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function numberOrNull(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function parseAxes(value: unknown): OpportunityRow["axes"] {
  if (!isRecord(value)) return { impact: null, effort: null };
  return {
    version: typeof value.version === "string" ? value.version : undefined,
    impact: numberOrNull(value.impact),
    effort: numberOrNull(value.effort),
  };
}

export function parseOpportunityRow(value: unknown): OpportunityRow | null {
  if (!isRecord(value)) return null;
  if (typeof value.id !== "string" || !UUID.test(value.id)) return null;
  if (typeof value.title !== "string") return null;
  if (
    typeof value.result_state !== "string" ||
    !RESULT_STATES.has(value.result_state)
  )
    return null;
  if (typeof value.confidence !== "number") return null;
  return {
    id: value.id,
    title: value.title,
    status: typeof value.status === "string" ? value.status : "candidate",
    result_state: value.result_state as OpportunityRow["result_state"],
    confidence: value.confidence,
    priority_band:
      typeof value.priority_band === "string" ? value.priority_band : null,
    total_score: numberOrNull(value.total_score),
    scoring_version:
      typeof value.scoring_version === "string" ? value.scoring_version : null,
    axes: parseAxes(value.axes),
    governance_review: value.governance_review === true,
  };
}

export function parseOpportunityList(value: unknown): OpportunityRow[] | null {
  if (!Array.isArray(value)) return null;
  const rows: OpportunityRow[] = [];
  for (const item of value) {
    const row = parseOpportunityRow(item);
    if (row === null) return null;
    rows.push(row);
  }
  return rows;
}

export function parseAnalysisOverview(value: unknown): AnalysisOverview | null {
  if (!isRecord(value)) return null;
  if (typeof value.analysis_id !== "string" || !UUID.test(value.analysis_id))
    return null;
  if (typeof value.status !== "string" || typeof value.task !== "string")
    return null;
  if (!Array.isArray(value.pain_points)) return null;
  const painPoints: PainPoint[] = [];
  for (const item of value.pain_points) {
    if (!isRecord(item)) return null;
    if (
      typeof item.category !== "string" ||
      typeof item.description !== "string"
    )
      return null;
    if (typeof item.severity !== "string" || !SEVERITIES.has(item.severity))
      return null;
    if (typeof item.confidence !== "string" || !SEVERITIES.has(item.confidence))
      return null;
    if (!Array.isArray(item.evidence_refs)) return null;
    painPoints.push(item as unknown as PainPoint);
  }
  return {
    analysis_id: value.analysis_id,
    status: value.status,
    task: value.task,
    pain_points: painPoints,
    error_code: typeof value.error_code === "string" ? value.error_code : null,
  };
}

export function parseOpportunityDetail(
  value: unknown,
): OpportunityDetail | null {
  if (!isRecord(value)) return null;
  const row = parseOpportunityRow(value);
  if (
    row === null ||
    !isRecord(value.score) ||
    typeof value.analysis_run_id !== "string"
  )
    return null;
  const score = value.score;
  if (!isRecord(score) || typeof score.scoring_version !== "string")
    return null;
  if (!isRecord(score.dimensions) || !isRecord(score.dimension_evidence))
    return null;
  const dimensions: Record<string, number | null> = {};
  for (const [key, item] of Object.entries(score.dimensions)) {
    if (item !== null && typeof item !== "number") return null;
    dimensions[key] = typeof item === "number" ? item : null;
  }
  return {
    ...row,
    analysis_run_id: value.analysis_run_id,
    scope: isRecord(value.scope) ? value.scope : {},
    score: {
      total: numberOrNull(score.total),
      scoring_version: score.scoring_version,
      dimensions,
      dimension_evidence: score.dimension_evidence as Record<
        string,
        readonly string[]
      >,
      coverage: numberOrNull(score.coverage),
      confidence_version:
        typeof score.confidence_version === "string"
          ? score.confidence_version
          : "",
    },
  };
}
