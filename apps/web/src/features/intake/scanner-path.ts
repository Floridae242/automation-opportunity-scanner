const ALLOWED_ROOTS = new Set([
  "projects",
  "processes",
  "analyses",
  "opportunities",
  "reports",
  "portfolio",
  "process-versions",
]);
const ACTION_SEGMENTS = new Set([
  "processes",
  "intake",
  "analyses",
  "review",
  "opportunities",
  "reports",
  "report",
  "pdf",
  "documents",
  "comments",
]);
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function scopedScannerPath(segments: string[]): string | null {
  if (segments.length === 0 || segments.length > 3) return null;
  if (!ALLOWED_ROOTS.has(segments[0])) return null;
  if (segments.length === 1) return segments[0];
  if (segments[0] === "portfolio" && segments[1] === "opportunities") {
    return segments.join("/");
  }
  if (!UUID.test(segments[1])) return null;
  if (segments.length === 3 && !ACTION_SEGMENTS.has(segments[2])) return null;
  return segments.join("/");
}
