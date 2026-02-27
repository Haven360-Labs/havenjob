"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";

type UserMe = {
  id: string;
  email: string;
  forwarding_address: string | null;
  full_name: string | null;
  target_role: string | null;
  onboarding_completed: boolean;
};

type TrustedSender = { id: string; sender_email: string; label: string | null };

const STEPS = [
  { id: 1, title: "Your forwarding email" },
  { id: 2, title: "Add a trusted sender" },
  { id: 3, title: "Quick profile" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserMe | null>(null);
  const [step, setStep] = useState(1);
  const [senders, setSenders] = useState<TrustedSender[]>([]);
  const [senderEmail, setSenderEmail] = useState("");
  const [senderLabel, setSenderLabel] = useState("");
  const [fullName, setFullName] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchMe = useCallback(() => {
    return apiFetch<UserMe>("/api/users/me");
  }, []);
  const fetchSenders = useCallback(() => {
    return apiFetch<TrustedSender[]>("/api/users/trusted-senders");
  }, []);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchMe(), fetchSenders()])
      .then(([u, s]) => {
        if (!cancelled) {
          setUser(u);
          setSenders(s);
          if (u.full_name) setFullName(u.full_name);
          if (u.target_role) setTargetRole(u.target_role);
        }
      })
      .catch(() => {
        if (!cancelled) router.replace("/login");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [fetchMe, fetchSenders, router]);

  async function handleAddSender(e: React.FormEvent) {
    e.preventDefault();
    const email = senderEmail.trim().toLowerCase();
    if (!email) {
      setError("Enter an email address.");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await apiFetch("/api/users/trusted-senders", {
        method: "POST",
        body: JSON.stringify({
          sender_email: email,
          label: senderLabel.trim() || undefined,
        }),
      });
      const list = await fetchSenders();
      setSenders(list);
      setSenderEmail("");
      setSenderLabel("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add sender");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleFinish() {
    setError(null);
    setSubmitting(true);
    try {
      await apiFetch("/api/users/me", {
        method: "PATCH",
        body: JSON.stringify({
          full_name: fullName.trim() || undefined,
          target_role: targetRole.trim() || undefined,
          onboarding_completed: true,
        }),
      });
      router.push("/dashboard");
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save");
      setSubmitting(false);
    }
  }

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Loading…</p>
      </div>
    );
  }

  if (user.onboarding_completed) {
    router.replace("/dashboard");
    return null;
  }

  return (
    <div className="max-w-lg mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">Welcome to HavenJob</h2>
        <p className="text-muted-foreground mt-1">Complete these steps to get started.</p>
      </div>

      <nav aria-label="Onboarding steps" className="flex gap-2">
        {STEPS.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => setStep(s.id)}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              step === s.id
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground hover:bg-muted/80"
            }`}
          >
            {s.id}. {s.title}
          </button>
        ))}
      </nav>

      {step === 1 && (
        <section className="rounded-lg border border-border bg-card p-6">
          <h3 className="text-lg font-semibold text-foreground">Your forwarding email</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Use this address when signing up for job alerts. We&apos;ll parse application emails sent to it.
          </p>
          <div className="mt-4 rounded-md bg-muted/50 p-4 font-mono text-sm break-all">
            {user.forwarding_address ?? "—"}
          </div>
          <div className="mt-4 flex justify-end">
            <Button onClick={() => setStep(2)}>Next</Button>
          </div>
        </section>
      )}

      {step === 2 && (
        <section className="rounded-lg border border-border bg-card p-6">
          <h3 className="text-lg font-semibold text-foreground">Add a trusted sender</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Add an email address that can send job-related emails to your forwarding address (e.g. a job board).
          </p>
          <form onSubmit={handleAddSender} className="mt-4 space-y-3">
            <div>
              <label htmlFor="sender_email" className="block text-sm font-medium mb-1">Sender email</label>
              <input
                id="sender_email"
                type="email"
                value={senderEmail}
                onChange={(e) => setSenderEmail(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="noreply@jobboard.com"
                disabled={submitting}
              />
            </div>
            <div>
              <label htmlFor="sender_label" className="block text-sm font-medium mb-1">Label (optional)</label>
              <input
                id="sender_label"
                type="text"
                value={senderLabel}
                onChange={(e) => setSenderLabel(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Job Board"
                disabled={submitting}
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" disabled={submitting}>{submitting ? "Adding…" : "Add sender"}</Button>
          </form>
          {senders.length > 0 && (
            <ul className="mt-4 space-y-2">
              <p className="text-sm font-medium text-foreground">Trusted senders</p>
              {senders.map((s) => (
                <li key={s.id} className="text-sm text-muted-foreground">
                  {s.sender_email} {s.label ? `(${s.label})` : ""}
                </li>
              ))}
            </ul>
          )}
          <div className="mt-4 flex justify-between">
            <Button variant="outline" onClick={() => setStep(1)}>Back</Button>
            <Button onClick={() => setStep(3)}>Next</Button>
          </div>
        </section>
      )}

      {step === 3 && (
        <section className="rounded-lg border border-border bg-card p-6">
          <h3 className="text-lg font-semibold text-foreground">Quick profile</h3>
          <p className="text-sm text-muted-foreground mt-1">
            You can add more later in Profile.
          </p>
          <div className="mt-4 space-y-4">
            <div>
              <label htmlFor="fullName" className="block text-sm font-medium mb-1">Full name</label>
              <input
                id="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Jane Doe"
                disabled={submitting}
              />
            </div>
            <div>
              <label htmlFor="targetRole" className="block text-sm font-medium mb-1">Target role</label>
              <input
                id="targetRole"
                type="text"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Senior Software Engineer"
                disabled={submitting}
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
          <div className="mt-4 flex justify-between">
            <Button variant="outline" onClick={() => setStep(2)}>Back</Button>
            <Button onClick={handleFinish} disabled={submitting}>
              {submitting ? "Saving…" : "Finish"}
            </Button>
          </div>
        </section>
      )}
    </div>
  );
}
