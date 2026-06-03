import * as React from "react"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { Check } from "lucide-react"

const DEFAULT_COLORS = [
  "#FE6900", // Yusi Orange
  "#252F50", // Yusi Navy
  "#EF4444", // Red
  "#3B82F6", // Blue
  "#10B981", // Emerald
  "#F59E0B", // Amber
  "#8B5CF6", // Violet
  "#EC4899", // Pink
  "#64748B", // Slate
]

interface ColorPickerProps {
  color?: string | null
  onChange: (color: string) => void
  disabled?: boolean
}

export function ColorPicker({ color, onChange, disabled }: ColorPickerProps) {
  return (
    <Popover>
      <PopoverTrigger
        render={
          <Button
            type="button"
            variant="outline"
            className="w-full justify-start text-left font-normal"
            disabled={disabled}
          />
        }
      >
        <div className="flex items-center gap-2">
          <div
            className="h-4 w-4 rounded-full border border-border/50 shadow-inner"
            style={{ backgroundColor: color || "#CBD5E1" }}
          />
          <span>{color || "Select color"}</span>
        </div>
      </PopoverTrigger>
      <PopoverContent className="w-64 p-3" align="start">
        <div className="flex flex-col gap-3">
          <p className="text-sm font-medium">Theme Colors</p>
          <div className="grid grid-cols-5 gap-2">
            {DEFAULT_COLORS.map((c) => (
              <button
                key={c}
                type="button"
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-md border shadow-sm transition-all hover:scale-110",
                  color === c ? "ring-2 ring-primary ring-offset-2" : "border-border/50"
                )}
                style={{ backgroundColor: c }}
                onClick={() => onChange(c)}
              >
                {color === c && <Check className="h-4 w-4 text-white" style={{ mixBlendMode: "difference" }} />}
              </button>
            ))}
          </div>
          <div className="space-y-1.5 mt-2">
            <p className="text-xs text-muted-foreground">Custom Color</p>
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={color || "#FE6900"}
                onChange={(e) => onChange(e.target.value)}
                className="h-8 w-8 cursor-pointer rounded overflow-hidden p-0 border-0"
              />
              <input
                type="text"
                value={color || ""}
                onChange={(e) => onChange(e.target.value)}
                className="flex h-8 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="#000000"
              />
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}
