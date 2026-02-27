"use client";

import { useState } from "react";
import { getApiUrl } from "@/lib/api";
import { Button } from "@/components/ui/button";

const TONE_OPTIONS = [
  { value: "formal", label: "Formal" },
  { value: "conversational", label: "Conversational" },
  { value: "enthusiastic", label: "Enthusiastic" },
] as const;

export default function CoverLetterPage() {
  const [jobDescription, setJobDescription] = useState("");
  const [tone, setTone] = useState<string>("formal");
  const [coverLetter, setCoverLetter] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    const jd = jobDescription.trim();
    if (!jd) {
      setError("Please paste a job description.");
      return;
    }
    setError(null);
    setLoading(true);
    setCoverLetter(null);
    try {
      const res = await fetch(getApiUrl("/api/ai/cover-letter"), {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_description: jd, tone }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail ?? "Failed to generate cover letter");
      }
      setCoverLetter(data.cover_letter ?? "");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to generate cover letter");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">Cover Letter</h2>
        <p className="text-muted-foreground">
          Paste a job description and generate a tailored cover letter from your profile.
        </p>
      </div>

      <section className="rounded-lg border border-border bg-card p-6">
        <h3 className="text-lg font-semibold text-foreground">Job description</h3>
        <p className="text-sm text-muted-foreground mt-1">
          Paste the full or partial job description. The more context, the better the letter.
        </p>
        <div className="mt-4 space-y-4">
          <div>
            <label htmlFor="jd" className="block text-sm font-medium text-foreground mb-1">
              Job description
            </label>
            <textarea
              id="jd"
              placeholder="Paste job description here..."
              value={jobDescription}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setJobDescription(e.target.value)}
              rows={8}
              className="w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-sm resize-y disabled:opacity-50"
              disabled={loading}
            />
          </div>
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label htmlFor="tone" className="block text-sm font-medium text-foreground mb-1">
                Tone
              </label>
              <select
                id="tone"
                value={tone}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setTone(e.target.value)}
                disabled={loading}
                className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm w-[180px] disabled:opacity-50"
              >
                {TONE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <Button onClick={handleGenerate} disabled={loading}>
              {loading ? "Generating…" : "Generate cover letter"}
            </Button>
          </div>
          {error && (
            <p className="text-sm text-destructive" role="alert">
              {error}
            </p>
          )}
        </div>
      </section>

      {coverLetter !== null && (
        <section className="rounded-lg border border-border bg-card p-6">
          <h3 className="text-lg font-semibold text-foreground">Generated cover letter</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Review and copy to use in your application.
          </p>
          <div className="mt-4 rounded-md border bg-muted/30 p-4">
            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-foreground">
              {coverLetter || "(No content)"}
            </pre>
          </div>
        </section>
      )}
    </div>
  );
}
