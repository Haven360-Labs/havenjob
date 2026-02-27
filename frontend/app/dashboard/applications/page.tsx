"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import Link from "next/link";
import { AddApplicationModal } from "@/components/dashboard/add-application-modal";
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
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addModalOpen, setAddModalOpen] = useState(false);

  const refetch = useCallback(() => {
    setLoading(true);
    setError(null);
    apiFetch<Application[]>("/api/tracker")
      .then((data) => setApplications(data))
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load applications"))
      .finally(() => setLoading(false));
  }, []);

  const handleStatusChange = useCallback((applicationId: string, newStatus: string) => {
    setApplications((prev) =>
      prev.map((a) => (a.id === applicationId ? { ...a, status: newStatus } : a))
    );
  }, []);

  useEffect(() => {
    let cancelled = false;
    apiFetch<Application[]>("/api/tracker")
      .then((data) => {
        if (!cancelled) setApplications(data);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load applications");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Loading applications…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-destructive">
        <p>{error}</p>
      </div>
    );
  }

  if (applications.length === 0) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-muted-foreground">No applications yet. Add one to get started.</p>
          <Button onClick={() => setAddModalOpen(true)}>Add application</Button>
        </div>
        <AddApplicationModal
          open={addModalOpen}
          onClose={() => setAddModalOpen(false)}
          onSuccess={refetch}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setAddModalOpen(true)}>Add application</Button>
      </div>
      <AddApplicationModal
        open={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        onSuccess={refetch}
      />
      <div className="overflow-x-auto rounded-md border border-border">
      <table className="w-full min-w-[600px] text-left text-sm">
        <thead className="border-b border-border bg-muted/50">
          <tr>
            <th className="px-4 py-3 font-medium text-foreground">Company</th>
            <th className="px-4 py-3 font-medium text-foreground">Job title</th>
            <th className="px-4 py-3 font-medium text-foreground">Date applied</th>
            <th className="px-4 py-3 font-medium text-foreground">Status</th>
            <th className="px-4 py-3 font-medium text-foreground">Source</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {applications.map((app) => (
            <tr key={app.id} className="hover:bg-muted/30">
              <td className="px-4 py-3">
                <Link
                  href={`/dashboard/applications/${app.id}`}
                  className="font-medium text-foreground underline-offset-4 hover:underline"
                >
                  {app.company_name}
                </Link>
              </td>
              <td className="px-4 py-3 text-foreground">{app.job_title}</td>
              <td className="px-4 py-3 text-muted-foreground">{formatDate(app.date_applied)}</td>
              <td className="px-4 py-3">
                <StatusDropdown
                  applicationId={app.id}
                  value={app.status}
                  onStatusChange={handleStatusChange}
                />
              </td>
              <td className="px-4 py-3 text-muted-foreground">{app.source ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    </div>
  );
}
