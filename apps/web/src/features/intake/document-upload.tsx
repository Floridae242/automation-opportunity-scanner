"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { uploadScannerFile } from "./client-api";

export function DocumentUpload({ processId }: { processId: string }) {
  const router = useRouter();
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const input = form.elements.namedItem("file");
    const file = input instanceof HTMLInputElement ? input.files?.[0] : null;
    if (!file || file.size === 0) {
      setError("Choose a non-empty text or PDF document.");
      return;
    }
    setPending(true);
    setError(null);
    setMessage(null);
    const result = await uploadScannerFile(
      `processes/${processId}/documents`,
      file,
    );
    setPending(false);
    if (!result.ok) {
      setError(result.message);
      return;
    }
    form.reset();
    setMessage(
      "Document stored as untrusted evidence. Review it before using it in an assessment.",
    );
    if (typeof router.refresh === "function") router.refresh();
  }

  return (
    <form
      onSubmit={submit}
      className="guide-card compact intake-form"
      aria-label="Upload process document"
    >
      <h2>Supporting document</h2>
      <label htmlFor="process-document">Text or PDF, up to 1 MB</label>
      <input
        id="process-document"
        name="file"
        type="file"
        accept="text/plain,application/pdf,.txt,.pdf"
        required
      />
      <p className="margin-note">
        Documents are treated as untrusted evidence. Uploading never changes a
        reviewed process or score.
      </p>
      {error && (
        <p role="alert" className="auth-error">
          {error}
        </p>
      )}
      {message && (
        <p role="status" className="intake-saved">
          {message}
        </p>
      )}
      <button
        type="submit"
        className="button button-secondary"
        disabled={pending}
      >
        {pending ? "Uploading…" : "Upload document"}
      </button>
    </form>
  );
}
