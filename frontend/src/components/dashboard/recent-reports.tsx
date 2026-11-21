import React from "react"
import { FileText, Clock, CheckCircle2, Loader2 } from "lucide-react"

export interface ReportItem {
  id: string
  company: string
  ticker: string
  period: string
  status: "Processed" | "Processing"
  lastUpdated: string
  pagesCount: number
}

const mockReports: ReportItem[] = [
  {
    id: "rep-1",
    company: "Tata Consultancy Services (TCS)",
    ticker: "TCS",
    period: "FY 2024–25",
    status: "Processed",
    lastUpdated: "Today, 10:45 AM",
    pagesCount: 336,
  },
  {
    id: "rep-2",
    company: "Infosys Limited",
    ticker: "INFY",
    period: "FY 2024–25",
    status: "Processed",
    lastUpdated: "Yesterday, 4:20 PM",
    pagesCount: 284,
  },
  {
    id: "rep-3",
    company: "HDFC Bank",
    ticker: "HDFCBANK",
    period: "FY 2024–25",
    status: "Processing",
    lastUpdated: "Just now",
    pagesCount: 312,
  },
  {
    id: "rep-4",
    company: "Reliance Industries",
    ticker: "RELIANCE",
    period: "FY 2023–24",
    status: "Processed",
    lastUpdated: "3 days ago",
    pagesCount: 418,
  },
]

export function RecentReports() {
  return (
    <div className="rounded-lg border border-border/70 bg-card p-6 shadow-xs">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold tracking-tight text-foreground">
            Recent Reports
          </h2>
          <p className="text-xs text-muted-foreground">
            Latest financial statements ingested and parsed for research.
          </p>
        </div>
        <span className="text-xs font-medium text-muted-foreground">
          {mockReports.length} records
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border/60 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <th className="pb-3 pl-1 font-semibold">Company</th>
              <th className="pb-3 px-4 font-semibold">Reporting Period</th>
              <th className="pb-3 px-4 font-semibold">Status</th>
              <th className="pb-3 pr-1 text-right font-semibold">Last Updated</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/40 text-foreground">
            {mockReports.map((report) => (
              <tr
                key={report.id}
                className="group transition-colors hover:bg-muted/30"
              >
                <td className="py-3.5 pl-1">
                  <div className="flex items-center gap-2.5">
                    <div className="flex size-7 shrink-0 items-center justify-center rounded-sm bg-muted/60 text-muted-foreground">
                      <FileText className="size-3.5 text-foreground/70" />
                    </div>
                    <div>
                      <div className="font-medium text-foreground">
                        {report.company}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {report.ticker} · {report.pagesCount} pages
                      </div>
                    </div>
                  </div>
                </td>
                <td className="py-3.5 px-4 font-mono text-xs text-foreground/90">
                  {report.period}
                </td>
                <td className="py-3.5 px-4">
                  {report.status === "Processed" ? (
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-600/20 bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-950/40 dark:text-emerald-400">
                      <CheckCircle2 className="size-3 text-emerald-600 dark:text-emerald-400" />
                      Processed
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/20 bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-800 dark:border-amber-500/30 dark:bg-amber-950/40 dark:text-amber-400">
                      <Loader2 className="size-3 animate-spin text-amber-600 dark:text-amber-400" />
                      Processing
                    </span>
                  )}
                </td>
                <td className="py-3.5 pr-1 text-right text-xs text-muted-foreground">
                  <span className="inline-flex items-center justify-end gap-1">
                    <Clock className="size-3" />
                    {report.lastUpdated}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

