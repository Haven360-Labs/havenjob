"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getApiUrl } from "@/lib/api";
import { Button } from "@/components/ui/button";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const trimmedEmail = email.trim().toLowerCase();
    if (!trimmedEmail) {
      setError("Email is required.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch(getApiUrl("/api/users/register"), {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: trimmedEmail,
          password,
          full_name: fullName.trim() || undefined,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error((data as { detail?: string }).detail ?? "Registration failed");
      }
      router.push("/login?registered=1");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Registration failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="w-full max-w-sm space-y-6 rounded-lg border border-border bg-card p-6 shadow-sm">
      <div className="space-y-1 text-center">
        <h1 className="text-2xl font-semibold tracking-tight">Create an account</h1>
        <p className="text-sm text-muted-foreground">
          Enter your details to sign up for HavenJob.
        </p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-foreground mb-1">
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="you@example.com"
            disabled={submitting}
          />
        </div>
        <div>
          <label htmlFor="fullName" className="block text-sm font-medium text-foreground mb-1">
            Full name (optional)
          </label>
          <input
            id="fullName"
            type="text"
            autoComplete="name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="Jane Doe"
            disabled={submitting}
          />
        </div>
        <div>
          <label htmlFor="password" className="block text-sm font-medium text-foreground mb-1">
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="At least 8 characters"
            disabled={submitting}
          />
        </div>
        {error && (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        )}
        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? "Signing up…" : "Sign up"}
        </Button>
      </form>
      <p className="text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-primary hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}
