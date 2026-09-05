"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

type Mode = "signin" | "register";

export function LoginForm() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("signin");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());
    try {
      const response = await fetch(
        `/api/auth/${mode === "signin" ? "login" : "register"}`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(payload),
        },
      );
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        setError(
          body?.error?.message ??
            "We could not reach the identity service. Try again.",
        );
        return;
      }
      router.replace("/");
      router.refresh();
    } catch {
      setError("We could not reach the identity service. Try again.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="auth-card" aria-labelledby="auth-title">
      <div
        role="tablist"
        aria-label="Authentication mode"
        className="auth-tabs"
      >
        <button
          type="button"
          role="tab"
          aria-selected={mode === "signin"}
          className={mode === "signin" ? "auth-tab active" : "auth-tab"}
          onClick={() => {
            setMode("signin");
            setError(null);
          }}
        >
          Sign in
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === "register"}
          className={mode === "register" ? "auth-tab active" : "auth-tab"}
          onClick={() => {
            setMode("register");
            setError(null);
          }}
        >
          Create account
        </button>
      </div>
      <h2 id="auth-title" className="sr-only">
        {mode === "signin" ? "Sign in" : "Create account"}
      </h2>
      <form onSubmit={submit} noValidate>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
          maxLength={320}
        />
        <label htmlFor="password">Password</label>
        <input
          id="password"
          name="password"
          type="password"
          required
          autoComplete={mode === "signin" ? "current-password" : "new-password"}
          minLength={mode === "register" ? 10 : undefined}
          maxLength={1024}
        />
        {mode === "register" && (
          <>
            <label htmlFor="display_name">Your name</label>
            <input
              id="display_name"
              name="display_name"
              required
              maxLength={200}
              autoComplete="name"
            />
            <label htmlFor="organization_name">Organization name</label>
            <input
              id="organization_name"
              name="organization_name"
              required
              maxLength={200}
            />
          </>
        )}
        {error && (
          <p role="alert" className="auth-error">
            {error}
          </p>
        )}
        <button type="submit" className="auth-submit" disabled={pending}>
          {pending
            ? mode === "signin"
              ? "Signing in…"
              : "Creating account…"
            : mode === "signin"
              ? "Sign in"
              : "Create organization"}
        </button>
      </form>
    </section>
  );
}
