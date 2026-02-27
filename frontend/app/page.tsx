import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-muted/30 p-4">
      <main className="max-w-lg text-center space-y-8">
        <h1 className="text-3xl font-semibold tracking-tight text-foreground">
          HavenJob
        </h1>
        <p className="text-muted-foreground">
          Track applications, build your profile, and get AI-powered cover letters and career help.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/login"
            className="inline-flex h-11 items-center justify-center rounded-md bg-primary px-6 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Log in
          </Link>
          <Link
            href="/signup"
            className="inline-flex h-11 items-center justify-center rounded-md border border-input bg-background px-6 text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors"
          >
            Sign up
          </Link>
        </div>
      </main>
    </div>
  );
}
