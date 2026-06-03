import * as React from "react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

type StatusType = "active" | "archived" | "completed" | "pending" | string

interface StatusBadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  status: StatusType
}

export function StatusBadge({ status, className, ...props }: StatusBadgeProps) {
  const getStatusColor = (s: string) => {
    switch (s.toLowerCase()) {
      case "active":
        return "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/20"
      case "archived":
        return "bg-slate-500/15 text-slate-700 dark:text-slate-400 border-slate-500/20"
      case "completed":
        return "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/20"
      case "pending":
        return "bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/20"
      default:
        return "bg-slate-100 text-slate-800 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700"
    }
  }

  const getDotColor = (s: string) => {
    switch (s.toLowerCase()) {
      case "active":
        return "bg-emerald-500"
      case "archived":
        return "bg-slate-500"
      case "completed":
        return "bg-blue-500"
      case "pending":
        return "bg-amber-500"
      default:
        return "bg-slate-500"
    }
  }

  return (
    <Badge
      variant="outline"
      className={cn("capitalize gap-1.5 font-medium px-2 py-0.5", getStatusColor(status), className)}
      {...props}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full shrink-0", getDotColor(status))} />
      <span className="truncate">{status}</span>
    </Badge>
  )
}
