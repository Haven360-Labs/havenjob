"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { StatusDropdown } from "@/components/dashboard/status-dropdown";
import { Button } from "@/components/ui/button";

type Application = {
  id: string;
  company_name: string;
  job_title: string;
  date_applied: string;
  status: string;
  source: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

function formatDateTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

export default function ApplicationDetailPage() {
  const params = useParams();
  const id = typeof params.id === "string" ? params.id : "";
  const [application, setApplication] = useState<Application | null>(null);
  const [loading, setLoading] = useState(!!id);
  const [error, setError] = useState<string | null>(!id ? "Invalid application id" : null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    apiFetch<Application>(`/api/tracker/${id}`)
      .then((data) => {
        if (!cancelled) setApplication(data);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load application");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const handleStatusChange = (applicationId: string, newStatus: string) => {
    setApplication((prev) =>
      prev && prev.id === applicationId ? { ...prev, status: newStatus } : prev
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Loading application…</p>
      </div>
    );
  }

  if (error || !application) {
    return (
      <div className="space-y-4">
        <div className="rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-destructive">
          <p>{error ?? "Application not found"}</p>
        </div>
        <Button variant="outline" asChild>
          <Link href="/dashboard/applications">Back to applications</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/dashboard/applications">← Back to applications</Link>
        </Button>
      </div>

      <div className="rounded-lg border border-border bg-card p-6">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">
              {application.job_title} at {application.company_name}
            </h1>
            <p className="mt-1 text-muted-foreground">
              Applied {formatDate(application.date_applied)}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Status:</span>
            <StatusDropdown
              applicationId={application.id}
              value={application.status}
              onStatusChange={handleStatusChange}
            />
          </div>
        </div>

        <dl className="mt-8 grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm font-medium text-muted-foreground">Company</dt>
            <dd className="mt-0.5 text-foreground">{application.company_name}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-muted-foreground">Job title</dt>
            <dd className="mt-0.5 text-foreground">{application.job_title}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-muted-foreground">Date applied</dt>
            <dd className="mt-0.5 text-foreground">{formatDate(application.date_applied)}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-muted-foreground">Source</dt>
            <dd className="mt-0.5 text-foreground">{application.source ?? "—"}</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-sm font-medium text-muted-foreground">Notes</dt>
            <dd className="mt-0.5 whitespace-pre-wrap text-foreground">
              {application.notes || "—"}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-muted-foreground">Created</dt>
            <dd className="mt-0.5 text-foreground">{formatDateTime(application.created_at)}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-muted-foreground">Last updated</dt>
            <dd className="mt-0.5 text-foreground">{formatDateTime(application.updated_at)}</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
