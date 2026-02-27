"use client";

import { useState } from "react";
import { getApiUrl } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const STATUS_OPTIONS = [
  "Applied",
  "Under Review",
  "Phone Screen",
  "Interview",
  "Offer",
  "Accepted",
  "Rejected",
  "Withdrawn",
];

type AddApplicationModalProps = {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
};

export function AddApplicationModal({ open, onClose, onSuccess }: AddApplicationModalProps) {
  const [companyName, setCompanyName] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [dateApplied, setDateApplied] = useState(() => {
    const d = new Date();
    return d.toISOString().slice(0, 10);
  });
  const [status, setStatus] = useState("Applied");
  const [source, setSource] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitError(null);
    setSubmitting(true);
    try {
      const url = getApiUrl("/api/tracker");
      const body = {
        company_name: companyName.trim(),
        job_title: jobTitle.trim(),
        date_applied: `${dateApplied}T12:00:00.000Z`,
        status,
        source: source.trim() || null,
        notes: notes.trim() || null,
      };
      const res = await fetch(url, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error((data as { detail?: string }).detail ?? res.statusText);
      }
      onSuccess();
      onClose();
      setCompanyName("");
      setJobTitle("");
      setDateApplied(new Date().toISOString().slice(0, 10));
      setStatus("Applied");
      setSource("");
      setNotes("");
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Failed to add application");
    } finally {
      setSubmitting(false);
    }
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="add-application-title"
    >
      <div
        className="fixed inset-0 bg-black/50"
        aria-hidden="true"
        onClick={onClose}
      />
      <div className="relative z-10 w-full max-w-md rounded-lg border border-border bg-background p-6 shadow-lg">
        <h2 id="add-application-title" className="text-lg font-semibold text-foreground mb-4">
          Add application
        </h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {submitError && (
            <p className="rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {submitError}
            </p>
          )}
          <div>
            <label htmlFor="company_name" className="mb-1 block text-sm font-medium text-foreground">
              Company *
            </label>
            <input
              id="company_name"
              type="text"
              required
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              className={cn(
                "w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground",
                "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              )}
              placeholder="Acme Inc"
            />
          </div>
          <div>
            <label htmlFor="job_title" className="mb-1 block text-sm font-medium text-foreground">
              Job title *
            </label>
            <input
              id="job_title"
              type="text"
              required
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              className={cn(
                "w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground",
                "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              )}
              placeholder="Software Engineer"
            />
          </div>
          <div>
            <label htmlFor="date_applied" className="mb-1 block text-sm font-medium text-foreground">
              Date applied *
            </label>
            <input
              id="date_applied"
              type="date"
              required
              value={dateApplied}
              onChange={(e) => setDateApplied(e.target.value)}
              className={cn(
                "w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground",
                "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              )}
            />
          </div>
          <div>
            <label htmlFor="status" className="mb-1 block text-sm font-medium text-foreground">
              Status *
            </label>
            <select
              id="status"
              required
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className={cn(
                "w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground",
                "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              )}
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="source" className="mb-1 block text-sm font-medium text-foreground">
              Source
            </label>
            <input
              id="source"
              type="text"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className={cn(
                "w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground",
                "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              )}
              placeholder="LinkedIn, company website…"
            />
          </div>
          <div>
            <label htmlFor="notes" className="mb-1 block text-sm font-medium text-foreground">
              Notes
            </label>
            <textarea
              id="notes"
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className={cn(
                "w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground",
                "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              )}
              placeholder="Optional notes"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Adding…" : "Add application"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
