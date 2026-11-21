
import Link from "next/link";
import { Suspense } from "react";
import { SignInButton, SignUpButton, SignOutButton, Show, UserButton } from "@clerk/nextjs";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col">
      <header className="flex h-16 items-center justify-between border-b border-border bg-white px-8">
        <h1 className="text-xl font-bold tracking-tight text-primary">
          InvestorLens
        </h1>

        <div className="flex items-center gap-4">
          <span className="hidden text-sm text-muted sm:inline">
            Financial Research Intelligence
          </span>

          <div className="flex items-center gap-2">
            <Suspense fallback={<div className="h-8 w-20 animate-pulse rounded-md bg-slate-100" />}>
              <Show when="signed-out">
                <SignInButton mode="modal">
                  <button
                    type="button"
                    className="rounded-lg border border-border px-3.5 py-1.5 text-xs font-semibold text-primary transition-colors hover:bg-slate-50"
                  >
                    Sign In
                  </button>
                </SignInButton>
                <SignUpButton mode="modal">
                  <button
                    type="button"
                    className="rounded-lg bg-primary px-3.5 py-1.5 text-xs font-semibold text-white transition-opacity hover:opacity-90"
                  >
                    Sign Up
                  </button>
                </SignUpButton>
              </Show>

              <Show when="signed-in">
                <Link
                  href="/dashboard"
                  className="rounded-lg bg-primary px-3.5 py-1.5 text-xs font-semibold text-white transition-opacity hover:opacity-90"
                >
                  Dashboard
                </Link>
                <SignOutButton>
                  <button
                    type="button"
                    className="rounded-lg border border-border px-3.5 py-1.5 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-50"
                  >
                    Log Out
                  </button>
                </SignOutButton>
                <UserButton
                  appearance={{
                    elements: {
                      userButtonAvatarBox: "size-8",
                    },
                  }}
                />
              </Show>
            </Suspense>
          </div>
        </div>
      </header>

      <section className="flex flex-1 items-center justify-center px-6 py-20">
        <div className="max-w-3xl text-center">
          <span className="mb-5 inline-block rounded-full bg-blue-50 px-4 py-2 text-sm font-medium text-primary">
            AI-Powered Financial Intelligence
          </span>

          <h2 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-6xl">
            Understand financial reports.
            <span className="text-primary"> Make sense of the numbers.</span>
          </h2>

          <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-muted">
            Analyze annual reports, extract financial metrics, explore
            company performance, and ask questions backed by document
            evidence.
          </p>

          <div className="mt-10 flex justify-center gap-4">
            <Suspense fallback={<div className="h-11 w-36 animate-pulse rounded-lg bg-slate-200" />}>
              <Show when="signed-out">
                <SignInButton mode="modal">
                  <button
                    type="button"
                    className="rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90"
                  >
                    Sign In to Get Started
                  </button>
                </SignInButton>
              </Show>
              <Show when="signed-in">
                <Link
                  href="/dashboard"
                  className="rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90"
                >
                  Go to Dashboard
                </Link>
              </Show>
            </Suspense>
          </div>
        </div>
      </section>

      <footer className="border-t border-border bg-white px-8 py-5 text-center text-sm text-muted">
        InvestorLens · Financial research powered by AI
      </footer>
    </main>
  );
}
