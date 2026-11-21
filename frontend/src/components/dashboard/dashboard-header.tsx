"use client"

import React, { Suspense } from "react"
import { Search, Bell, Menu } from "lucide-react"
import { SignInButton, SignUpButton, SignOutButton, Show, UserButton } from "@clerk/nextjs"

interface DashboardHeaderProps {
  onToggleSidebar?: () => void
}

export function DashboardHeader({ onToggleSidebar }: DashboardHeaderProps) {
  return (
    <header className="sticky top-0 z-10 flex h-16 w-full items-center justify-between border-b border-border/70 bg-card/95 px-4 backdrop-blur-xs sm:px-8">
      {/* Breadcrumb / Heading */}
      <div className="flex items-center gap-3">
        {onToggleSidebar && (
          <button
            type="button"
            onClick={onToggleSidebar}
            aria-label="Toggle navigation"
            className="flex size-9 items-center justify-center rounded-md border border-border/60 bg-muted/20 text-muted-foreground hover:bg-muted/50 hover:text-foreground md:hidden"
          >
            <Menu className="size-4.5" />
          </button>
        )}
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5 text-[0.6875rem] font-medium text-muted-foreground">
            <span>Workspace</span>
            <span>/</span>
            <span className="text-foreground/90">Financial Overview</span>
          </div>
          <h1 className="text-sm font-semibold tracking-tight text-foreground sm:text-base">
            Dashboard
          </h1>
        </div>
      </div>

      {/* Center Search Input */}
      <div className="mx-4 hidden max-w-md flex-1 md:block">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <input
            type="search"
            placeholder="Search reports, companies, or metrics (e.g. TCS FY25)..."
            className="h-9 w-full rounded-md border border-border/70 bg-muted/20 pl-9 pr-3 text-xs text-foreground placeholder:text-muted-foreground/80 focus:border-ring focus:bg-card focus:outline-hidden"
          />
        </div>
      </div>

      {/* Right Controls: Notifications & Profile / Auth */}
      <div className="flex items-center gap-3">
        {/* Notification bell */}
        <button
          type="button"
          aria-label="View notifications"
          className="relative flex size-9 items-center justify-center rounded-md border border-border/60 bg-muted/20 text-muted-foreground transition-colors hover:bg-muted/50 hover:text-foreground"
        >
          <Bell className="size-4" />
          <span className="absolute right-2 top-2 size-1.5 rounded-full bg-emerald-600" />
        </button>

        {/* User auth controls */}
        <div className="flex items-center gap-2.5 pl-2 border-l border-border/70">
          <Suspense fallback={<div className="size-8 rounded-full bg-muted/60 animate-pulse" />}>
            <Show when="signed-out">
              <SignInButton mode="modal">
                <button
                  type="button"
                  className="rounded-md border border-border/70 bg-muted/30 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-foreground hover:bg-muted/60"
                >
                  Sign In
                </button>
              </SignInButton>
              <SignUpButton mode="modal">
                <button
                  type="button"
                  className="rounded-md bg-foreground px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-background hover:opacity-90"
                >
                  Sign Up
                </button>
              </SignUpButton>
            </Show>
            <Show when="signed-in">
              <SignOutButton>
                <button
                  type="button"
                  className="rounded-md border border-border/70 bg-muted/20 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground transition-colors hover:bg-muted/50 hover:text-foreground"
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
  )
}
