import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { parseProject } from "@/features/intake/contract";
import { fetchWorkspaceJson } from "@/features/intake/workspace-data";
import {
  ProcessCreateForm,
  ProjectActions,
} from "@/features/intake/workspace-forms";
import { readServerSession } from "@/features/auth/session";

export const dynamic = "force-dynamic";

export default async function ProjectPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  if (!(await readServerSession())) redirect("/login");
  const { id } = await params;
  const project = await fetchWorkspaceJson(
    `projects/${id}`,
    parseProject,
    null,
  );
  if (project === null) notFound();
  return (
    <div className="page-content">
      <section className="page-intro">
        <div className="intro">
          <p className="eyebrow">
            <span className="eyebrow-line" />
            PROJECT
          </p>
          <h1>{project.name}</h1>
          <p className="intro-description">
            {project.department ?? "No department set"} · {project.status}
          </p>
        </div>
        <ProjectActions
          projectId={project.id}
          name={project.name}
          status={project.status}
        />
      </section>
      <section aria-label="Processes" className="workflow-section">
        <h2 className="quiet-label">PROCESSES IN THIS PROJECT</h2>
        {(project.processes ?? []).length === 0 ? (
          <div className="empty-state">
            <h3>No processes yet</h3>
            <p>Add a process, then capture its intake details.</p>
          </div>
        ) : (
          <div className="guide-grid">
            {(project.processes ?? []).map((process) => (
              <article key={process.id} className="guide-card compact">
                <h3>
                  <Link href={`/processes/${process.id}`}>{process.name}</Link>
                </h3>
                <span
                  className={
                    process.latest_version ? "evidence-chip" : "outline-tag"
                  }
                >
                  {process.latest_version
                    ? `${process.latest_version.review_status} v${process.latest_version.version_no}`
                    : "intake needed"}
                </span>
              </article>
            ))}
          </div>
        )}
        {project.status === "active" && (
          <ProcessCreateForm projectId={project.id} />
        )}
      </section>
    </div>
  );
}
