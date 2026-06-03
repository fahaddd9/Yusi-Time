import * as React from "react"
import { cn } from "@/lib/utils"

interface ProjectTagProps extends Omit<React.HTMLAttributes<HTMLDivElement>, "color"> {
  name: string
  color?: string | null
  clientName?: string | null
  size?: "sm" | "md" | "lg"
}

export function ProjectTag({ name, color, clientName, size = "sm", className, ...props }: ProjectTagProps) {
  const resolvedColor = color || "#CBD5E1"

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 rounded-full border shadow-sm w-fit max-w-full bg-background",
        size === "sm" && "px-2.5 py-0.5 text-xs",
        size === "md" && "px-3 py-1 text-sm",
        size === "lg" && "px-4 py-1.5 text-base",
        className
      )}
      {...props}
    >
      <div className="flex items-center gap-1.5 overflow-hidden">
        <div
          className={cn(
            "rounded-full shrink-0 shadow-inner",
            size === "sm" && "h-2 w-2",
            size === "md" && "h-2.5 w-2.5",
            size === "lg" && "h-3 w-3"
          )}
          style={{ backgroundColor: resolvedColor }}
        />
        <span className="font-medium truncate text-foreground">{name}</span>
      </div>
      {clientName && (
        <>
          <div className="h-3 w-px bg-border shrink-0 mx-0.5" />
          <span className="text-muted-foreground truncate">{clientName}</span>
        </>
      )}
    </div>
  )
}
