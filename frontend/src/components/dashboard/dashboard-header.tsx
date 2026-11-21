"use client"

import React from "react"
import { Search, Bell, Menu } from "lucide-react"

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

      {/* Right Controls: Notifications & Profile */}
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

        {/* User profile */}
        <div className="flex items-center gap-2.5 pl-2 border-l border-border/70">
          <div className="flex size-8 shrink-0 items-center justify-center rounded-full border border-border/80 bg-muted/60 text-xs font-semibold text-foreground">
            DS
          </div>
          <div className="hidden flex-col text-left text-xs lg:flex">
            <span className="font-medium text-foreground leading-tight">
              Divy Saxena
            </span>
            <span className="text-[0.625rem] text-muted-foreground leading-tight">
              Research Analyst
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}
