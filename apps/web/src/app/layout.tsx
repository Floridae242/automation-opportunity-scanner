import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AppShell } from "@/components/app-shell";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Opportunity Scanner — Process studio", template: "%s — Opportunity Scanner" },
  description: "An evidence-first workspace for understanding processes and investigating automation opportunities. Foundation preview.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return <html lang="en"><body><AppShell>{children}</AppShell></body></html>;
}
