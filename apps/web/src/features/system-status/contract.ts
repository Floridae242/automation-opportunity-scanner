export type Availability = "available" | "unavailable";
export type SystemStatus = Readonly<{ live: Availability; ready: Availability }>;

export function isSystemStatus(value: unknown): value is SystemStatus {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  const isAvailability = (item: unknown) => item === "available" || item === "unavailable";
  return isAvailability(candidate.live) && isAvailability(candidate.ready);
}
