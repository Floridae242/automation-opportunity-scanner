"use client";

import { useEffect, useState } from "react";
import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { isSystemStatus, type SystemStatus } from "./contract";

type CheckState = { kind: "loading" } | { kind: "error" } | { kind: "complete"; data: SystemStatus };

const services = [
  { key: "live", title: "Application API", description: "The application service is responding.", available: "Available" },
  { key: "ready", title: "Database readiness", description: "The API can connect to its database.", available: "Ready" },
] as const;

export function StatusPanel() {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<CheckState>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    let disposed = false;
    const timeout = setTimeout(() => controller.abort(), 8000);
    async function check() {
      try {
        const response = await fetch("/api/system-status", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Status check failed");
        const data: unknown = await response.json();
        if (!isSystemStatus(data)) throw new Error("Invalid status response");
        if (!disposed) setState({ kind: "complete", data });
      } catch {
        if (!disposed) setState({ kind: "error" });
      } finally {
        clearTimeout(timeout);
      }
    }
    void check();
    return () => { disposed = true; clearTimeout(timeout); controller.abort(); };
  }, [attempt]);

  const healthy = state.kind === "complete" && state.data.live === "available" && state.data.ready === "available";
  const title = state.kind === "loading" ? "Checking your services…" : state.kind === "error" ? "Unable to check services" : healthy ? "Services are available" : "Some services need attention";
  const description = state.kind === "loading" ? "Contacting the application and checking database readiness." : state.kind === "error" ? "The check could not finish. Check your connection and try again." : healthy ? "The application and database responded to the latest check." : "Check that your local API and database are running, then try again.";

  return <section className="status-panel" aria-label="Service health">
    <div className={`status-summary ${healthy ? "is-healthy" : ""}`}><div aria-live="polite" role="status"><span className="status-kicker"><span className="small-dot" />LIVE SERVICE CHECK</span><h2>{title}</h2><p>{description}</p></div><Button disabled={state.kind === "loading"} onClick={() => { setState({ kind: "loading" }); setAttempt((current) => current + 1); }}><Icon name="refresh" size={17} />{state.kind === "loading" ? "Checking services…" : "Check again"}</Button></div>
    <ul className="service-list">{services.map((service) => {
      const available = state.kind === "complete" && state.data[service.key] === "available";
      const badge = state.kind === "loading" ? "Checking" : state.kind === "error" ? "Unknown" : available ? service.available : "Unavailable";
      return <li key={service.key}><span className="service-icon"><Icon name={service.key === "live" ? "pulse" : "layers"} size={22} /></span><div><h3>{service.title}</h3><p>{service.description}</p></div><span className={`service-badge ${available ? "available" : ""}`}><span className="small-dot" />{badge}</span></li>;
    })}</ul>
    <p className="status-footnote">A point-in-time check. Use “Check again” to refresh the result.</p>
  </section>;
}
