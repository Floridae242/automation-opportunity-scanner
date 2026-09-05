export type ProjectStatus = "active" | "archived";
export type ReviewStatus = "draft" | "reviewed" | "superseded";

export type PerPeriod = Readonly<{ value: number; period: string }>;

export type IntakeMetrics = Readonly<{
  frequency?: PerPeriod;
  duration_minutes?: number;
  volume_per_period?: PerPeriod;
  error_rate?: number;
  rework_rate?: number;
  sla?: string;
  systems?: readonly string[];
  approvals_required?: number;
  sensitivity?: "low" | "medium" | "high" | "restricted";
}>;

export type ProcessVersion = Readonly<{
  id: string;
  version_no: number;
  review_status: ReviewStatus;
  source_summary: string;
  metrics: IntakeMetrics;
  created_at: string;
}>;

export type Process = Readonly<{
  id: string;
  project_id: string;
  name: string;
  status: ProjectStatus;
  versions: readonly ProcessVersion[];
  latest_version: ProcessVersion | null;
}>;

export type Project = Readonly<{
  id: string;
  name: string;
  department: string | null;
  status: ProjectStatus;
  process_count: number;
  created_at: string;
  updated_at: string;
  processes?: readonly Process[];
}>;

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const STATUSES = new Set(["active", "archived"]);
const REVIEWS = new Set(["draft", "reviewed", "superseded"]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function parseVersion(value: unknown): ProcessVersion | null {
  if (!isRecord(value)) return null;
  if (typeof value.id !== "string" || !UUID.test(value.id)) return null;
  if (typeof value.version_no !== "number") return null;
  if (
    typeof value.review_status !== "string" ||
    !REVIEWS.has(value.review_status)
  )
    return null;
  if (typeof value.source_summary !== "string") return null;
  if (!isRecord(value.metrics) || typeof value.created_at !== "string")
    return null;
  return value as unknown as ProcessVersion;
}

export function parseProcess(value: unknown): Process | null {
  if (!isRecord(value)) return null;
  if (typeof value.id !== "string" || !UUID.test(value.id)) return null;
  if (typeof value.project_id !== "string" || !UUID.test(value.project_id))
    return null;
  if (typeof value.name !== "string") return null;
  if (typeof value.status !== "string" || !STATUSES.has(value.status))
    return null;
  if (!Array.isArray(value.versions)) return null;
  const versions: ProcessVersion[] = [];
  for (const item of value.versions) {
    const version = parseVersion(item);
    if (!version) return null;
    versions.push(version);
  }
  if (value.latest_version !== null) {
    const latest = parseVersion(value.latest_version);
    if (!latest) return null;
  }
  return value as unknown as Process;
}

export function parseProject(value: unknown): Project | null {
  if (!isRecord(value)) return null;
  if (typeof value.id !== "string" || !UUID.test(value.id)) return null;
  if (typeof value.name !== "string") return null;
  if (value.department !== null && typeof value.department !== "string")
    return null;
  if (typeof value.status !== "string" || !STATUSES.has(value.status))
    return null;
  if (typeof value.process_count !== "number") return null;
  if (
    typeof value.created_at !== "string" ||
    typeof value.updated_at !== "string"
  )
    return null;
  if (value.processes !== undefined) {
    if (!Array.isArray(value.processes)) return null;
    for (const item of value.processes) {
      if (!parseProcess(item)) return null;
    }
  }
  return value as unknown as Project;
}

export function parseProjectList(value: unknown): Project[] | null {
  if (!Array.isArray(value)) return null;
  const projects: Project[] = [];
  for (const item of value) {
    const project = parseProject(item);
    if (!project) return null;
    projects.push(project);
  }
  return projects;
}
