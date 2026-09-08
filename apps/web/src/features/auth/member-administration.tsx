"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { callScannerApi } from "@/features/intake/client-api";
import type { AuthRole } from "./contract";

export type OrganizationMember = Readonly<{
  id: string;
  user_id: string;
  email: string;
  display_name: string;
  role: AuthRole;
}>;

const ROLES: readonly AuthRole[] = [
  "owner",
  "admin",
  "analyst",
  "reviewer",
  "viewer",
];

export function MemberAdministration({
  members,
}: {
  members: readonly OrganizationMember[];
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function addMember(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setPending(true);
    setError(null);
    const result = await callScannerApi("POST", "organization-members", {
      email: String(form.get("email") || "").trim(),
      role: String(form.get("role") || "viewer"),
    });
    setPending(false);
    if (!result.ok) return setError(result.message);
    router.refresh();
  }

  async function changeRole(memberId: string, role: string) {
    setPending(true);
    setError(null);
    const result = await callScannerApi(
      "PATCH",
      `organization-members/${memberId}`,
      { role },
    );
    setPending(false);
    if (!result.ok) return setError(result.message);
    router.refresh();
  }

  return (
    <section className="guide-card" aria-label="Organization members">
      <h2>Organization members</h2>
      <p>
        Add people who already have an account, then assign the least privileged
        role they need.
      </p>
      <form className="intake-form" onSubmit={addMember}>
        <label htmlFor="member-email">
          Account email
          <input id="member-email" name="email" required type="email" />
        </label>
        <label htmlFor="member-role">
          Initial role
          <select defaultValue="viewer" id="member-role" name="role">
            {ROLES.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
        </label>
        <button
          className="button button-primary"
          disabled={pending}
          type="submit"
        >
          {pending ? "Adding…" : "Add member"}
        </button>
      </form>
      {error && (
        <p className="auth-error" role="alert">
          {error}
        </p>
      )}
      <div className="table-scroll">
        <table className="score-table">
          <thead>
            <tr>
              <th>Member</th>
              <th>Email</th>
              <th>Role</th>
            </tr>
          </thead>
          <tbody>
            {members.map((member) => (
              <tr key={member.id}>
                <td>{member.display_name}</td>
                <td>{member.email}</td>
                <td>
                  <label
                    className="sr-only"
                    htmlFor={`member-role-${member.id}`}
                  >
                    Role for {member.display_name}
                  </label>
                  <select
                    defaultValue={member.role}
                    disabled={pending}
                    id={`member-role-${member.id}`}
                    onChange={(event) =>
                      changeRole(member.id, event.target.value)
                    }
                  >
                    {ROLES.map((role) => (
                      <option key={role} value={role}>
                        {role}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
