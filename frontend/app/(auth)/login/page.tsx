"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { getApiUrl } from "@/lib/api";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const justRegistered = searchParams.get("registered") === "1";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const trimmedEmail = email.trim().toLowerCase();
    if (!trimmedEmail) {
      setError("Email is required.");
      return;
    }
    if (!password) {
      setError("Password is required.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch(getApiUrl("/api/users/login"), {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: trimmedEmail, password }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error((data as { detail?: string }).detail ?? "Invalid email or password");
      }
      router.push("/dashboard");
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="w-full max-w-sm space-y-6 rounded-lg border border-border bg-card p-6 shadow-sm">
      <div className="space-y-1 text-center">
        <h1 className="text-2xl font-semibold tracking-tight">Log in</h1>
        <p className="text-sm text-muted-foreground">
          Enter your email and password to access HavenJob.
        </p>
      </div>
      {justRegistered && (
        <p className="text-sm text-green-600 dark:text-green-400 text-center rounded-md bg-green-500/10 py-2" role="status">
          Account created. You can log in now.
        </p>
      )}
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
          <label htmlFor="password" className="block text-sm font-medium text-foreground mb-1">
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="••••••••"
            disabled={submitting}
          />
        </div>
        {error && (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        )}
        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? "Logging in…" : "Log in"}
        </Button>
      </form>
      <p className="text-center text-sm text-muted-foreground">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="font-medium text-primary hover:underline">
          Sign up
        </Link>
      </p>
    </div>
  );
}
