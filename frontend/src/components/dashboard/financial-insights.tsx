import React from "react"
import { Sparkles, ArrowUpRight, Scale, Percent } from "lucide-react"

interface InsightItem {
  id: string
  title: string
  metric: string
  observation: string
  source: string
  type: "revenue" | "margin" | "leverage"
}

const mockInsights: InsightItem[] = [
  {
    id: "ins-1",
    title: "Revenue Growth Trajectory",
    metric: "+6.8% YoY",
    observation:
      "TCS demonstrated resilient growth led by international digital transformation and cloud modernizations, offset by selective BFSI discretionary tightening.",
    source: "TCS FY 2024–25 Standalone Statements",
    type: "revenue",
  },
  {
    id: "ins-2",
    title: "Operating Margin Expansion",
    metric: "24.3% Operating Margin",
    observation:
      "Disciplined execution and operational efficiencies sustained margins at 24.3%, representing an expansion over the previous fiscal period.",
    source: "Letter from the CEO & Financial Highlights",
    type: "margin",
  },
  {
    id: "ins-3",
    title: "Prudent Debt & Coverage Health",
    metric: "0.1 Debt-to-Equity · 23.5 DSCR",
    observation:
      "Consistently low debt-to-equity ratio of 0.1 with debt service coverage ratio at 23.5× reflects a conservative balance sheet and strong liquidity buffers.",
    source: "Note 25: Additional Regulatory Information",
    type: "leverage",
  },
]

export function FinancialInsights() {
  return (
    <div className="rounded-lg border border-border/70 bg-card p-6 shadow-xs">
      <div className="mb-4 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold tracking-tight text-foreground">
              Financial Insights
            </h2>
            <span className="inline-flex items-center gap-1 rounded-sm border border-emerald-600/20 bg-emerald-50 px-1.5 py-0.5 text-[0.625rem] font-semibold uppercase tracking-wider text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-950/40 dark:text-emerald-400">
              <Sparkles className="size-2.5" />
              Sample Observations
            </span>
          </div>
          <p className="text-xs text-muted-foreground">
            Deterministic observations derived from parsed report disclosures.
          </p>
        </div>
        <p className="text-[0.6875rem] text-muted-foreground italic">
          * Illustrative mock insights for validation testing
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {mockInsights.map((insight) => {
          return (
            <div
              key={insight.id}
              className="flex flex-col justify-between rounded-md border border-border/60 bg-muted/20 p-4 transition-colors hover:border-border hover:bg-muted/40"
            >
              <div>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span className="font-semibold uppercase tracking-wider text-[0.625rem]">
                    {insight.title}
                  </span>
                  {insight.type === "revenue" && (
                    <ArrowUpRight className="size-3.5 text-emerald-600" />
                  )}
                  {insight.type === "margin" && (
                    <Percent className="size-3.5 text-emerald-600" />
                  )}
                  {insight.type === "leverage" && (
                    <Scale className="size-3.5 text-emerald-600" />
                  )}
                </div>

                <div className="mt-2 text-sm font-semibold tracking-tight text-foreground">
                  {insight.metric}
                </div>

                <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                  {insight.observation}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-border/50 text-[0.6875rem] text-muted-foreground/80 font-mono">
                {insight.source}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

