import { StatusPanel } from "@/features/system-status/status-panel";

export default function StatusPage() {
  return <div className="page-content"><section className="page-intro"><p className="eyebrow">WORKSPACE STATUS</p><h1>A clear view of<br /><span>the foundation.</span></h1><p className="intro-description">Check the services supporting this local preview. Each check reflects the current connection, with a straightforward path to try again.</p></section><StatusPanel /><section className="status-note"><h2>What this check means</h2><p>Service availability confirms the application can reach its API and that the API can reach its database. It does not enable assessment creation, sign-in, analysis, or reports in this foundation preview.</p></section></div>;
}
