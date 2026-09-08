import { StatusPanel } from "@/features/system-status/status-panel";

export default function StatusPage() {
  return (
    <div className="page-content">
      <section className="page-intro">
        <p className="eyebrow">WORKSPACE STATUS</p>
        <h1>
          A clear view of
          <br />
          <span>the workspace.</span>
        </h1>
        <p className="intro-description">
          Check the services supporting this workspace. Each check reflects the
          current connection, with a straightforward path to try again.
        </p>
      </section>
      <StatusPanel />
      <section className="status-note">
        <h2>What this check means</h2>
        <p>
          Service availability confirms the application can reach its API and
          that the API can reach its database. It does not prove that every
          external AI provider or report export dependency is available.
        </p>
      </section>
    </div>
  );
}
