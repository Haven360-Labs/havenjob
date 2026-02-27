"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/applications", label: "Applications" },
  { href: "/dashboard/cover-letter", label: "Cover Letter" },
  { href: "/dashboard/chat", label: "Chat" },
  { href: "/dashboard/profile", label: "Profile" },
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen w-full">
      <aside
        className="flex w-56 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground"
        aria-label="Main navigation"
      >
        <div className="flex h-14 items-center gap-2 border-b border-sidebar-border px-4">
          <Link href="/dashboard" className="font-semibold text-sidebar-primary">
            HavenJob
          </Link>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-2" aria-label="Sidebar">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded-md px-3 py-2 text-sm font-medium transition-colors",
                pathname === item.href
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <div className="flex flex-1 flex-col min-w-0">
        <header
          className="flex h-14 shrink-0 items-center gap-4 border-b border-border bg-background px-6"
          aria-label="Page header"
        >
          <h1 className="text-lg font-semibold text-foreground">Dashboard</h1>
        </header>
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  );
}
