"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import type { ReactNode } from "react";
import type { AuthSession } from "@/features/auth/contract";
import { Icon } from "./icon";

const navigation = [
  { href: "/", label: "Overview", icon: "grid" },
  { href: "/projects", label: "Projects", icon: "folder" },
  { href: "/portfolio", label: "Portfolio", icon: "grid" },
  { href: "/settings", label: "Scoring settings", icon: "sliders" },
  { href: "/guide", label: "Assessment guide", icon: "book" },
  { href: "/status", label: "Workspace status", icon: "pulse" },
] as const;

const PAGE_LABELS: Record<string, string> = {
  ...Object.fromEntries(navigation.map((item) => [item.href, item.label])),
  "/login": "Sign in",
};

export function AccountMenu({ session }: { session: AuthSession }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const active = session.memberships.find(
    (membership) =>
      membership.organization_id === session.active_organization_id,
  );
  async function signOut(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    await fetch("/api/auth/logout", { method: "POST" });
    router.replace("/login");
    router.refresh();
  }
  return (
    <div className="account-menu">
      <span className="account-name" title={session.user.email}>
        {session.user.display_name}
      </span>
      {active && (
        <span className="account-org">
          {active.organization_name} · {active.role}
        </span>
      )}
      <button
        type="button"
        className="account-signout"
        onClick={signOut}
        disabled={pending}
      >
        {pending ? "Signing out…" : "Sign out"}
      </button>
    </div>
  );
}

export function AppShell({
  children,
  session = null,
}: {
  children: ReactNode;
  session?: AuthSession | null;
}) {
  const pathname = usePathname();
  const section =
    pathname === "/projects"
      ? "Projects"
      : pathname.startsWith("/projects/")
        ? "Project detail"
        : pathname.startsWith("/processes/")
          ? "Process intake"
            : pathname === "/portfolio"
              ? "Portfolio"
              : pathname === "/settings"
                ? "Scoring settings"
            : pathname.startsWith("/analyses/")
              ? "Opportunity analysis"
              : pathname.startsWith("/opportunities/")
                ? "Opportunity detail"
                : (PAGE_LABELS[pathname] ?? "Page not found");
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside className="sidebar">
        <Link
          className="brand"
          href="/"
          aria-label="Automation Opportunity Scanner home"
        >
          <span className="brand-mark" aria-hidden="true">
            <i />
            <i />
            <i />
          </span>
          <span>
            opportunity
            <span className="brand-second">
              scanner<span className="brand-dot">.</span>
            </span>
          </span>
        </Link>
        <div className="workspace-label">
          <span className="workspace-monogram">OS</span>
          <span>
            Process studio<small>Evidence workspace</small>
          </span>
        </div>
        <p className="nav-caption">WORKSPACE</p>
        <nav aria-label="Main navigation">
          {navigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="nav-link"
              aria-current={pathname === item.href ? "page" : undefined}
            >
              <Icon name={item.icon} />
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
        <div className="sidebar-note">
          <span className="note-symbol">
            <Icon name="shield" size={23} />
          </span>
          <p>
            Evidence first.
            <br />
            Better decisions follow.
          </p>
          <small>
            A clear process is the starting point for useful automation.
          </small>
        </div>
        <div className="sidebar-foot">
          <span className="small-dot" />
          Evidence-first analysis<span className="version">MVP</span>
        </div>
      </aside>
      <div className="page-frame">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace<span aria-hidden="true">/</span>
            <strong>{section}</strong>
          </div>
          {session ? (
            <AccountMenu session={session} />
          ) : (
            <div className="topbar-actions">
              <Link className="signin-link" href="/login">
                Sign in
              </Link>
              <span className="preview-tag">
                <span className="small-dot" />
                Read-only preview
              </span>
            </div>
          )}
        </header>
        <main id="main-content" tabIndex={-1}>
          {children}
        </main>
        <footer className="page-footer">
          <span>Automation Opportunity Scanner</span>
          <span>Built around evidence. Guided by people.</span>
        </footer>
      </div>
    </div>
  );
}
