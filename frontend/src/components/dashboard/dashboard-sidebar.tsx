"use client"

import React from "react"
import Link from "next/link"
import {
  LayoutDashboard,
  FileText,
  Building2,
  Bot,
  Settings,
  ShieldCheck,
  TrendingUp,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface NavItem {
  label: string
  href: string
  icon: React.ElementType
  active?: boolean
  badge?: string
}

const mainNavItems: NavItem[] = [
  {
    label: "Overview",
    href: "/dashboard",
    icon: LayoutDashboard,
    active: true,
  },
  {
    label: "Reports",
    href: "/dashboard",
    icon: FileText,
  },
  {
    label: "Companies",
    href: "/dashboard",
    icon: Building2,
  },
  {
    label: "AI Analyst",
    href: "/dashboard",
    icon: Bot,
    badge: "Beta",
  },
]

export function DashboardSidebar() {
  return (
    <aside className="flex h-full w-64 flex-col border-r border-border/70 bg-card">
      {/* Brand Header */}
      <div className="flex h-16 items-center gap-2.5 border-b border-border/70 px-6">
        <div className="flex size-7 items-center justify-center rounded-sm bg-foreground text-background">
          <TrendingUp className="size-4" />
        </div>
        <div className="flex flex-col">
          <span className="font-heading text-sm font-semibold tracking-wider uppercase text-foreground">
            InvestorLens
          </span>
          <span className="text-[0.625rem] text-muted-foreground tracking-tight">
            Financial Research Intelligence
          </span>
        </div>
      </div>

      {/* Main Navigation */}
      <div className="flex-1 overflow-y-auto px-3 py-4">
        <div className="px-3 pb-2 text-[0.625rem] font-semibold uppercase tracking-wider text-muted-foreground/80">
          Navigation
        </div>
        <nav className="space-y-1">
          {mainNavItems.map((item) => {
            const Icon = item.icon
            return (
              <Link
                key={item.label}
                href={item.href}
                className={cn(
                  "group flex items-center justify-between rounded-md px-3 py-2 text-xs font-medium transition-colors",
                  item.active
                    ? "bg-foreground text-background shadow-xs"
                    : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                )}
              >
                <div className="flex items-center gap-2.5">
                  <Icon
                    className={cn(
                      "size-4 shrink-0 transition-colors",
                      item.active
                        ? "text-background"
                        : "text-muted-foreground group-hover:text-foreground"
                    )}
                  />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span
                    className={cn(
                      "rounded-sm px-1.5 py-0.2 text-[0.625rem] font-medium tracking-wide uppercase",
                      item.active
                        ? "bg-background/20 text-background"
                        : "border border-border/80 bg-muted/40 text-muted-foreground"
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            )
          })}
        </nav>
      </div>

      {/* Footer / Settings */}
      <div className="border-t border-border/70 p-3">
        <div className="rounded-md border border-border/50 bg-muted/20 p-2.5 mb-2">
          <div className="flex items-center gap-2 text-xs font-medium text-foreground/80">
            <ShieldCheck className="size-3.5 text-emerald-700" />
            <span>Deterministic RAG</span>
          </div>
          <p className="mt-1 text-[0.625rem] leading-tight text-muted-foreground">
            Document evidence grounded with 384-dim dense vectors.
          </p>
        </div>

        <Link
          href="/dashboard"
          className="flex items-center gap-2.5 rounded-md px-3 py-2 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted/60 hover:text-foreground"
        >
          <Settings className="size-4 shrink-0 text-muted-foreground" />
          <span>Settings</span>
        </Link>
      </div>
    </aside>
  )
}

