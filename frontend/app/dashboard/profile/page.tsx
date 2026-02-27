"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch, getApiUrl } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type WorkExperience = {
  id: string;
  company: string;
  role: string;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  description: string | null;
  display_order: number;
  created_at: string;
  updated_at: string;
};

type Project = {
  id: string;
  title: string;
  description: string;
  technologies: string[] | null;
  url: string | null;
  display_order: number;
  created_at: string;
  updated_at: string;
};

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

export default function ProfilePage() {
  const [workExperiences, setWorkExperiences] = useState<WorkExperience[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddWork, setShowAddWork] = useState(false);
  const [showAddProject, setShowAddProject] = useState(false);

  const fetchWork = useCallback(() => {
    return apiFetch<WorkExperience[]>("/api/ai/profile/work-experience").then(setWorkExperiences);
  }, []);
  const fetchProjects = useCallback(() => {
    return apiFetch<Project[]>("/api/ai/profile/projects").then(setProjects);
  }, []);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiFetch<WorkExperience[]>("/api/ai/profile/work-experience"),
      apiFetch<Project[]>("/api/ai/profile/projects"),
    ])
      .then(([we, proj]) => {
        if (!cancelled) {
          setWorkExperiences(we);
          setProjects(proj);
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load profile");
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
        <p className="text-muted-foreground">Loading profile…</p>
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

  return (
    <div className="space-y-10">
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-foreground">Work history</h2>
          <Button onClick={() => setShowAddWork((v) => !v)} variant={showAddWork ? "secondary" : "default"}>
            {showAddWork ? "Cancel" : "Add work experience"}
          </Button>
        </div>
        {showAddWork && (
          <AddWorkExperienceForm
            onSuccess={() => {
              fetchWork();
              setShowAddWork(false);
            }}
            onCancel={() => setShowAddWork(false)}
          />
        )}
        <ul className="mt-4 space-y-3">
          {workExperiences.length === 0 && !showAddWork && (
            <li className="text-muted-foreground text-sm">No work experience yet.</li>
          )}
          {workExperiences.map((we) => (
            <li
              key={we.id}
              className="rounded-lg border border-border bg-card p-4 text-foreground"
            >
              <p className="font-medium">{we.role} at {we.company}</p>
              <p className="text-sm text-muted-foreground">
                {formatDate(we.start_date)}
                {we.end_date ? ` – ${formatDate(we.end_date)}` : we.is_current ? " – Present" : ""}
              </p>
              {we.description && <p className="mt-1 text-sm">{we.description}</p>}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-foreground">Projects</h2>
          <Button onClick={() => setShowAddProject((v) => !v)} variant={showAddProject ? "secondary" : "default"}>
            {showAddProject ? "Cancel" : "Add project"}
          </Button>
        </div>
        {showAddProject && (
          <AddProjectForm
            onSuccess={() => {
              fetchProjects();
              setShowAddProject(false);
            }}
            onCancel={() => setShowAddProject(false)}
          />
        )}
        <ul className="mt-4 space-y-3">
          {projects.length === 0 && !showAddProject && (
            <li className="text-muted-foreground text-sm">No projects yet.</li>
          )}
          {projects.map((p) => (
            <li
              key={p.id}
              className="rounded-lg border border-border bg-card p-4 text-foreground"
            >
              <p className="font-medium">{p.title}</p>
              <p className="text-sm text-muted-foreground">{p.description}</p>
              {p.url && (
                <a href={p.url} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline mt-1 inline-block">
                  {p.url}
                </a>
              )}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function AddWorkExperienceForm({
  onSuccess,
  onCancel,
}: {
  onSuccess: () => void;
  onCancel: () => void;
}) {
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [isCurrent, setIsCurrent] = useState(false);
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setSubmitting(true);
    try {
      const url = getApiUrl("/api/ai/profile/work-experience");
      const res = await fetch(url, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company: company.trim(),
          role: role.trim(),
          start_date: startDate || undefined,
          end_date: endDate || null,
          is_current: isCurrent,
          description: description.trim() || null,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error((data as { detail?: string }).detail ?? res.statusText);
      }
      onSuccess();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed to add");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-border bg-muted/30 p-4 space-y-3">
      {err && <p className="text-sm text-destructive">{err}</p>}
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="we-company" className="block text-sm font-medium mb-1">Company *</label>
          <input
            id="we-company"
            required
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            className={cn("w-full rounded-md border border-input bg-background px-3 py-2 text-sm")}
          />
        </div>
        <div>
          <label htmlFor="we-role" className="block text-sm font-medium mb-1">Role *</label>
          <input
            id="we-role"
            required
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className={cn("w-full rounded-md border border-input bg-background px-3 py-2 text-sm")}
          />
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="we-start" className="block text-sm font-medium mb-1">Start date *</label>
          <input
            id="we-start"
            type="date"
            required
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className={cn("w-full rounded-md border border-input bg-background px-3 py-2 text-sm")}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">End date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            disabled={isCurrent}
            className={cn("w-full rounded-md border border-input bg-background px-3 py-2 text-sm")}
          />
          <label className="mt-1 flex items-center gap-2 text-sm">
            <input type="checkbox" checked={isCurrent} onChange={(e) => setIsCurrent(e.target.checked)} />
            Currently working here
          </label>
        </div>
      </div>
      <div>
        <label htmlFor="we-desc" className="block text-sm font-medium mb-1">Description</label>
        <textarea
          id="we-desc"
          rows={2}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className={cn("w-full rounded-md border border-input bg-background px-3 py-2 text-sm")}
        />
      </div>
      <div className="flex gap-2">
        <Button type="submit" disabled={submitting}>{submitting ? "Adding…" : "Add"}</Button>
        <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
      </div>
    </form>
  );
}

function AddProjectForm({
  onSuccess,
  onCancel,
}: {
  onSuccess: () => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [url, setUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setSubmitting(true);
    try {
      const apiUrl = getApiUrl("/api/ai/profile/projects");
      const res = await fetch(apiUrl, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title.trim(),
          description: description.trim(),
          url: url.trim() || null,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error((data as { detail?: string }).detail ?? res.statusText);
      }
      onSuccess();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed to add");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-border bg-muted/30 p-4 space-y-3">
      {err && <p className="text-sm text-destructive">{err}</p>}
      <div>
        <label htmlFor="proj-title" className="block text-sm font-medium mb-1">Title *</label>
        <input
          id="proj-title"
          required
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className={cn("w-full rounded-md border border-input bg-background px-3 py-2 text-sm")}
        />
      </div>
      <div>
        <label htmlFor="proj-desc" className="block text-sm font-medium mb-1">Description *</label>
        <textarea
          id="proj-desc"
          required
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className={cn("w-full rounded-md border border-input bg-background px-3 py-2 text-sm")}
        />
      </div>
      <div>
        <label htmlFor="proj-url" className="block text-sm font-medium mb-1">URL</label>
        <input
          id="proj-url"
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className={cn("w-full rounded-md border border-input bg-background px-3 py-2 text-sm")}
        />
      </div>
      <div className="flex gap-2">
        <Button type="submit" disabled={submitting}>{submitting ? "Adding…" : "Add"}</Button>
        <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
      </div>
    </form>
  );
}
