"use client";

import { useEffect, useState, type FormEvent } from "react";
import { callScannerApi } from "./client-api";

type Comment = { id: string; body: string; author: { display_name: string } };

export function CommentsPanel({ versionId }: { versionId: string }) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    fetch(`/api/scanner/process-versions/${versionId}/comments`)
      .then((response) => response.json())
      .then((data: unknown) => {
        if (Array.isArray(data)) setComments(data as Comment[]);
      })
      .catch(() => setError("We could not load the discussion."));
  }, [versionId]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const body = String(new FormData(form).get("body") || "").trim();
    if (!body) return setError("Write a comment before posting.");
    setPending(true);
    setError(null);
    setMessage(null);
    const result = await callScannerApi(
      "POST",
      `process-versions/${versionId}/comments`,
      { body },
    );
    setPending(false);
    if (!result.ok) return setError(result.message);
    form.reset();
    setMessage("Comment added. Refresh to see the latest discussion.");
  }

  return (
    <section className="guide-card compact" aria-label="Version discussion">
      <h2>Review discussion</h2>
      {comments.length === 0 ? (
        <p className="margin-note">No comments on this version yet.</p>
      ) : (
        <ul>
          {comments.map((comment) => (
            <li key={comment.id}>
              <strong>{comment.author.display_name}</strong>
              <p>{comment.body}</p>
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={submit}>
        <label htmlFor="comment-body">Add comment</label>
        <textarea id="comment-body" name="body" maxLength={2000} required />
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
          {pending ? "Posting…" : "Post comment"}
        </button>
      </form>
    </section>
  );
}
