import { redirect } from "next/navigation";
import { LoginForm } from "@/features/auth/login-form";
import { readServerSession } from "@/features/auth/session";

export const dynamic = "force-dynamic";

export default async function LoginPage() {
  if (await readServerSession()) redirect("/");
  return (
    <div className="page-content auth-page">
      <section className="page-intro">
        <p className="eyebrow">IDENTITY</p>
        <h1>
          Welcome back.
          <br />
          <span>Your evidence stays yours.</span>
        </h1>
        <p className="intro-description">
          Sign in to the studio, or create an organization to start your first
          assessment.
        </p>
      </section>
      <LoginForm />
    </div>
  );
}
