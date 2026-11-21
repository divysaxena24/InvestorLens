import React from "react"
import {
  FileText,
  Building2,
  TrendingUp,
  type LucideIcon,
} from "lucide-react"

interface MetricCardProps {
  title: string
  value: string | number
  contextLabel: string
  iconName: "reports" | "companies" | "insights"
  trendText?: string
}

const iconMap: Record<MetricCardProps["iconName"], LucideIcon> = {
  reports: FileText,
  companies: Building2,
  insights: TrendingUp,
}

export function MetricCard({
  title,
  value,
  contextLabel,
  iconName,
  trendText,
}: MetricCardProps) {
  const Icon = iconMap[iconName]

  return (
    <div className="flex flex-col justify-between rounded-lg border border-border/70 bg-card p-6 shadow-xs transition-shadow hover:shadow-sm">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {title}
        </span>
        <div className="flex size-9 items-center justify-center rounded-md border border-border/60 bg-muted/50 text-foreground/80">
          <Icon className="size-4.5 text-foreground/75" />
        </div>
      </div>

      <div className="mt-4 flex items-baseline gap-2">
        <span className="text-3xl font-semibold tracking-tight text-foreground">
          {value}
        </span>
        {trendText && (
          <span className="inline-flex items-center text-xs font-medium text-emerald-700">
            {trendText}
          </span>
        )}
      </div>

      <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
        {contextLabel}
      </p>
    </div>
  )
}
