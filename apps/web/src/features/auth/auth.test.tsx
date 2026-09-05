import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { parseApiErrorMessage, parseAuthSession } from "./contract";
import { AccountMenu } from "@/components/app-shell";
import { LoginForm } from "./login-form";

const nav = vi.hoisted(() => ({ replace: vi.fn(), refresh: vi.fn() }));
vi.mock("next/navigation", () => ({
  usePathname: () => "/login",
  useRouter: () => nav,
}));

const session = {
  user: {
    id: "6f1d0b3e-1a2b-4c5d-8e9f-0a1b2c3d4e5f",
    email: "ada@corp.test",
    display_name: "Ada",
  },
  active_organization_id: "1b2c3d4e-5f60-41a2-93b4-c5d6e7f80911",
  memberships: [
    {
      organization_id: "1b2c3d4e-5f60-41a2-93b4-c5d6e7f80911",
      organization_name: "Corp",
      role: "owner" as const,
    },
  ],
};

beforeEach(() => {
  nav.replace.mockClear();
  nav.refresh.mockClear();
});

describe("auth contract", () => {
  it("accepts a valid session and rejects malformed payloads", () => {
    expect(parseAuthSession(session)?.user.email).toBe("ada@corp.test");
    expect(
      parseAuthSession({ ...session, memberships: [{ role: "superuser" }] }),
    ).toBeNull();
    expect(
      parseAuthSession({ ...session, user: { ...session.user, id: "leak" } }),
    ).toBeNull();
    expect(parseAuthSession(null)).toBeNull();
    expect(
      parseApiErrorMessage({
        error: { message: "Email or password is incorrect." },
      }),
    ).toBe("Email or password is incorrect.");
    expect(parseApiErrorMessage({ token: "secret" })).toBeNull();
  });
});

describe("account menu", () => {
  it("shows who is signed in and where", () => {
    render(<AccountMenu session={session} />);
    expect(screen.getByText("Ada")).toBeVisible();
    expect(screen.getByText("Corp · owner")).toBeVisible();
    expect(screen.getByRole("button", { name: "Sign out" })).toBeEnabled();
  });
});

describe("login form", () => {
  it("signs in through the proxy and leaves the page", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => session });
    vi.stubGlobal("fetch", fetchMock);
    render(<LoginForm />);
    await userEvent.type(screen.getByLabelText("Email"), "ada@corp.test");
    await userEvent.type(screen.getByLabelText("Password"), "strong-pass-123");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await vi.waitFor(() => expect(nav.replace).toHaveBeenCalledWith("/"));
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/auth/login",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("surfaces the API message on rejection", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({
          error: { message: "Email or password is incorrect." },
        }),
      }),
    );
    render(<LoginForm />);
    await userEvent.type(screen.getByLabelText("Email"), "ada@corp.test");
    await userEvent.type(screen.getByLabelText("Password"), "wrong-password");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Email or password is incorrect.",
    );
    expect(nav.replace).not.toHaveBeenCalled();
  });

  it("names the offending field when the API returns validation details", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({
          error: {
            code: "VALIDATION_ERROR",
            message: "The request body is invalid.",
            request_id: "r1",
            details: {
              fields: [{ field: "password", issue: "string_too_short" }],
            },
          },
        }),
      }),
    );
    render(<LoginForm />);
    await userEvent.click(screen.getByRole("tab", { name: "Create account" }));
    await userEvent.type(screen.getByLabelText("Email"), "ada@corp.test");
    await userEvent.type(screen.getByLabelText("Password"), "strong-pass-123");
    await userEvent.type(screen.getByLabelText("Your name"), "Ada");
    await userEvent.type(screen.getByLabelText("Organization name"), "Corp");
    await userEvent.click(
      screen.getByRole("button", { name: "Create organization" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Password is too short.",
    );
  });

  it("blocks a short password before any network call", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    render(<LoginForm />);
    await userEvent.click(screen.getByRole("tab", { name: "Create account" }));
    await userEvent.type(screen.getByLabelText("Email"), "ada@corp.test");
    await userEvent.type(screen.getByLabelText("Password"), "short123");
    await userEvent.type(screen.getByLabelText("Your name"), "Ada");
    await userEvent.type(screen.getByLabelText("Organization name"), "Corp");
    await userEvent.click(
      screen.getByRole("button", { name: "Create organization" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "at least 10 characters",
    );
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("asks for organization details when creating an account", async () => {
    render(<LoginForm />);
    await userEvent.click(screen.getByRole("tab", { name: "Create account" }));
    expect(screen.getByLabelText("Organization name")).toBeRequired();
    expect(
      screen.getByRole("button", { name: "Create organization" }),
    ).toBeEnabled();
  });
});
