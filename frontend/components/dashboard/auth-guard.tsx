"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getApiUrl } from "@/lib/api";

type UserMe = { onboarding_completed: boolean };

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [status, setStatus] = useState<"loading" | "authenticated" | "unauthenticated">("loading");

  useEffect(() => {
    let cancelled = false;
    fetch(getApiUrl("/api/users/me"), { credentials: "include" })
      .then(async (res) => {
        if (cancelled) return;
        if (res.status === 401) {
          setStatus("unauthenticated");
          return;
        }
        if (!res.ok) {
          setStatus("unauthenticated");
          return;
        }
        const data = (await res.json()) as UserMe;
        if (!data.onboarding_completed && pathname !== "/dashboard/onboarding") {
          router.replace("/dashboard/onboarding");
          return;
        }
        setStatus("authenticated");
      })
      .catch(() => {
        if (!cancelled) setStatus("unauthenticated");
      });
    return () => {
      cancelled = true;
    };
  }, [pathname, router]);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace("/login");
    }
  }, [status, router]);

  if (status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">Loading…</p>
      </div>
    );
  }

  if (status === "unauthenticated") {
    return null;
  }

  return <>{children}</>;
}
