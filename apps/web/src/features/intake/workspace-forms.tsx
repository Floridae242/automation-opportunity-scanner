"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { callScannerApi } from "./client-api";

export function ProjectCreateForm() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const result = await callScannerApi("POST", "projects", {
      name: String(form.get("name") ?? ""),
      department: String(form.get("department") ?? "") || null,
    });
    setPending(false);
    if (!result.ok) return setError(result.message);
    formElement.reset();
    router.refresh();
  }
  return (
    <form
      onSubmit={submit}
      className="guide-card compact intake-form"
      aria-label="Create project"
    >
      <label htmlFor="project-name">Project name</label>
      <input
        id="project-name"
        name="name"
        required
        maxLength={200}
        placeholder="Claims intake"
      />
      <label htmlFor="project-department">Department (optional)</label>
      <input
        id="project-department"
        name="department"
        maxLength={200}
        placeholder="Operations"
      />
      {error && (
        <p role="alert" className="auth-error">
          {error}
        </p>
      )}
      <button
        type="submit"
        className="button button-primary"
        disabled={pending}
      >
        {pending ? "Creating…" : "Create project"}
      </button>
    </form>
  );
}

export function ProjectActions({
  projectId,
  name,
  status,
}: {
  projectId: string;
  name: string;
  status: string;
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  async function rename(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = String(new FormData(event.currentTarget).get("name") ?? "");
    await mutate({ name });
  }
  async function toggleArchive() {
    await mutate({ status: status === "active" ? "archived" : "active" });
  }
  async function mutate(body: Record<string, unknown>) {
    setPending(true);
    setError(null);
    const result = await callScannerApi("PATCH", `projects/${projectId}`, body);
    setPending(false);
    if (!result.ok) return setError(result.message);
    router.refresh();
  }
  return (
    <section
      className="guide-card compact project-actions"
      aria-label="Project actions"
    >
      <form onSubmit={rename} className="inline-form">
        <label htmlFor="rename-project" className="sr-only">
          Rename project
        </label>
        <input
          id="rename-project"
          name="name"
          defaultValue={name}
          required
          maxLength={200}
        />
        <button
          type="submit"
          className="button button-secondary"
          disabled={pending}
        >
          {pending ? "Saving…" : "Rename"}
        </button>
      </form>
      <button
        type="button"
        className="button button-secondary"
        onClick={toggleArchive}
        disabled={pending}
      >
        {status === "active" ? "Archive project" : "Restore project"}
      </button>
      {error && (
        <p role="alert" className="auth-error">
          {error}
        </p>
      )}
    </section>
  );
}

export function ProcessCreateForm({ projectId }: { projectId: string }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const result = await callScannerApi(
      "POST",
      `projects/${projectId}/processes`,
      {
        name: String(form.get("name") ?? ""),
      },
    );
    setPending(false);
    if (!result.ok) return setError(result.message);
    formElement.reset();
    router.refresh();
  }
  return (
    <form
      onSubmit={submit}
      className="guide-card compact intake-form"
      aria-label="Create process"
    >
      <label htmlFor="process-name">Process name</label>
      <input
        id="process-name"
        name="name"
        required
        maxLength={200}
        placeholder="Verify claim documents"
      />
      {error && (
        <p role="alert" className="auth-error">
          {error}
        </p>
      )}
      <button
        type="submit"
        className="button button-primary"
        disabled={pending}
      >
        {pending ? "Creating…" : "Add process"}
      </button>
    </form>
  );
}
