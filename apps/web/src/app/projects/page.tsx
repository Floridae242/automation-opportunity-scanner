import Link from "next/link";
import { redirect } from "next/navigation";
import { ProjectCreateForm } from "@/features/intake/workspace-forms";
import { fetchWorkspaceJson } from "@/features/intake/workspace-data";
import { parseProjectList } from "@/features/intake/contract";
import { readServerSession } from "@/features/auth/session";

export const dynamic = "force-dynamic";

export default async function ProjectsPage() {
  if (!(await readServerSession())) redirect("/login");
  const projects = await fetchWorkspaceJson("projects", parseProjectList, []);
  return (
    <div className="page-content">
      <section className="page-intro">
        <div className="intro">
          <p className="eyebrow">
            <span className="eyebrow-line" />
            PROJECTS
          </p>
          <h1>
            Where the work
            <br />
            <span>gets organized.</span>
          </h1>
          <p className="intro-description">
            Projects group the processes you assess. Everything here is scoped
            to your active organization.
          </p>
        </div>
        <ProjectCreateForm />
      </section>
      {projects.length === 0 ? (
        <section className="empty-state">
          <h2>No projects yet</h2>
          <p className="intro-description">
            Create your first project to start capturing processes.
          </p>
        </section>
      ) : (
        <section aria-label="Project list" className="guide-grid">
          {projects.map((project) => (
            <article key={project.id} className="guide-card">
              <h3>
                <Link href={`/projects/${project.id}`}>{project.name}</Link>
              </h3>
              <p>{project.department ?? "No department set"}</p>
              <p className="status-footnote">
                {project.process_count} process
                {project.process_count === 1 ? "" : "es"}
                {project.status === "archived" ? " · archived" : ""}
              </p>
            </article>
          ))}
        </section>
      )}
    </div>
  );
}
