"use client"

import React, { useState } from "react"
import { UploadCloud, Sparkles, RefreshCw } from "lucide-react"
import { DashboardSidebar } from "@/components/dashboard/dashboard-sidebar"
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { MetricCard } from "@/components/dashboard/metric-card"
import { RecentReports } from "@/components/dashboard/recent-reports"
import { FinancialInsights } from "@/components/dashboard/financial-insights"

export default function DashboardPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="flex min-h-screen bg-muted/30 text-foreground">
      {/* Desktop Sidebar */}
      <div className="hidden md:flex md:w-64 md:flex-col md:shrink-0">
        <DashboardSidebar />
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div
            className="fixed inset-0 bg-foreground/20 backdrop-blur-xs transition-opacity"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />
          <div className="relative flex w-64 max-w-xs flex-1 flex-col bg-card">
            <DashboardSidebar />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <DashboardHeader onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

        <main className="flex-1 overflow-y-auto px-4 py-6 sm:px-8 sm:py-8">
          <div className="mx-auto flex max-w-7xl flex-col gap-6">
            {/* Overview Banner Section */}
            <div className="flex flex-col gap-4 rounded-lg border border-border/70 bg-card p-6 shadow-xs sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-semibold tracking-tight text-foreground sm:text-2xl">
                    Financial Research Workspace
                  </h1>
                  <span className="hidden items-center gap-1 rounded-sm border border-emerald-600/20 bg-emerald-50 px-2 py-0.5 text-[0.625rem] font-semibold uppercase tracking-wider text-emerald-800 sm:inline-flex dark:border-emerald-500/30 dark:bg-emerald-950/40 dark:text-emerald-400">
                    <Sparkles className="size-2.5" />
                    Verified RAG
                  </span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground sm:text-sm">
                  Review extracted corporate disclosures, verify ratios against source document pages, and ask grounded financial research questions.
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2.5 shrink-0">
                <button
                  type="button"
                  aria-label="Refresh workspace"
                  className="inline-flex size-9 items-center justify-center rounded-md border border-border/70 bg-muted/20 text-muted-foreground transition-colors hover:bg-muted/50 hover:text-foreground"
                >
                  <RefreshCw className="size-3.5" />
                </button>
                <button
                  type="button"
                  className="inline-flex items-center gap-2 rounded-md bg-foreground px-4 py-2 text-xs font-semibold uppercase tracking-wider text-background shadow-xs transition-opacity hover:opacity-90"
                >
                  <UploadCloud className="size-3.5" />
                  <span>Upload Report</span>
                </button>
              </div>
            </div>

            {/* Three Metric Cards */}
            <section aria-label="Key Performance Indicators" className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <MetricCard
                title="Reports Analyzed"
                value="12"
                contextLabel="Comprehensive 10-K & Integrated Annual Reports ingested"
                iconName="reports"
                trendText="+2 this month"
              />
              <MetricCard
                title="Companies Tracked"
                value="8"
                contextLabel="Active portfolio enterprises with parsed financial disclosures"
                iconName="companies"
                trendText="Enterprise BFSI & IT"
              />
              <MetricCard
                title="Insights Generated"
                value="36"
                contextLabel="Audit-verified observations backed by cited PDF page provenance"
                iconName="insights"
                trendText="100% Citation Grounded"
              />
            </section>

            {/* Recent Reports Table */}
            <section aria-label="Recent Reports">
              <RecentReports />
            </section>

            {/* Financial Insights Cards */}
            <section aria-label="Financial Insights">
              <FinancialInsights />
            </section>
          </div>
        </main>
      </div>
    </div>
  )
}
