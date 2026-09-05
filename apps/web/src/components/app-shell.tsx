"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { Icon } from "./icon";

const navigation = [
  { href: "/", label: "Overview", icon: "grid" },
  { href: "/guide", label: "Assessment guide", icon: "book" },
  { href: "/status", label: "Workspace status", icon: "pulse" },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const current = navigation.find((item) => item.href === pathname);
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Skip to content</a>
    <aside className="sidebar">
      <Link className="brand" href="/" aria-label="Automation Opportunity Scanner home">
        <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
        <span>opportunity<span className="brand-second">scanner<span className="brand-dot">.</span></span></span>
      </Link>
      <div className="workspace-label"><span className="workspace-monogram">OS</span><span>Process studio<small>Workspace preview</small></span></div>
      <p className="nav-caption">WORKSPACE</p>
      <nav aria-label="Main navigation">{navigation.map((item) => <Link key={item.href} href={item.href} className="nav-link" aria-current={pathname === item.href ? "page" : undefined}><Icon name={item.icon} /><span>{item.label}</span></Link>)}</nav>
      <div className="sidebar-note"><span className="note-symbol"><Icon name="shield" size={23} /></span><p>Evidence first.<br />Better decisions follow.</p><small>A clear process is the starting point for useful automation.</small></div>
      <div className="sidebar-foot"><span className="small-dot" />Foundation preview<span className="version">M0</span></div>
    </aside>
    <div className="page-frame">
      <header className="topbar"><div className="breadcrumb">Workspace<span aria-hidden="true">/</span><strong>{current?.label ?? "Page not found"}</strong></div><span className="preview-tag"><span className="small-dot" />Read-only preview</span></header>
      <main id="main-content" tabIndex={-1}>{children}</main>
      <footer className="page-footer"><span>Automation Opportunity Scanner</span><span>Built around evidence. Guided by people.</span></footer>
    </div>
  </div>;
}
