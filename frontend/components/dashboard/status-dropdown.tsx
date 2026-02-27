"use client";

import { useState } from "react";
import { getApiUrl } from "@/lib/api";
import { cn } from "@/lib/utils";

export const STATUS_OPTIONS = [
  "Applied",
  "Under Review",
  "Phone Screen",
  "Interview",
  "Offer",
  "Accepted",
  "Rejected",
  "Withdrawn",
] as const;

type StatusDropdownProps = {
  applicationId: string;
  value: string;
  onStatusChange: (applicationId: string, newStatus: string) => void;
  disabled?: boolean;
};

export function StatusDropdown({
  applicationId,
  value,
  onStatusChange,
  disabled = false,
}: StatusDropdownProps) {
  const [updating, setUpdating] = useState(false);

  async function handleChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const newStatus = e.target.value;
    if (newStatus === value) return;
    setUpdating(true);
    try {
      const url = getApiUrl(`/api/tracker/${applicationId}`);
      const res = await fetch(url, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error((data as { detail?: string }).detail ?? res.statusText);
      }
      onStatusChange(applicationId, newStatus);
    } catch {
      e.target.value = value;
    } finally {
      setUpdating(false);
    }
  }

  return (
    <select
      value={value}
      onChange={handleChange}
      disabled={disabled || updating}
      aria-label={`Status for application (current: ${value})`}
      className={cn(
        "inline-flex cursor-pointer items-center rounded-full border border-border bg-secondary px-2.5 py-0.5 text-xs font-medium text-secondary-foreground",
        "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        "hover:bg-secondary/80 disabled:cursor-not-allowed disabled:opacity-70"
      )}
    >
      {STATUS_OPTIONS.map((s) => (
        <option key={s} value={s}>
          {s}
        </option>
      ))}
    </select>
  );
}
