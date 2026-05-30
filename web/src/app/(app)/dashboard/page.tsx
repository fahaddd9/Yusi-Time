import { ThemeToggle } from "@/components/ThemeToggle"
import { Button, buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import Link from "next/link"

export default function DashboardPage() {
  return (
    <div className="p-8 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-brand-navy dark:text-white">
            Dashboard
          </h1>
          <p className="text-muted-foreground mt-1">
            Welcome to Yusi Time. This layout will be built in Phase 4.
          </p>
        </div>
        <ThemeToggle />
      </div>

      <div className="bg-card border border-border p-6 rounded-xl shadow-sm space-y-4">
        <h2 className="text-lg font-semibold">Authentication Successful 🎉</h2>
        <p className="text-sm text-foreground-3">
          You are seeing this page because you have a valid JWT access token in memory, 
          and a valid refresh token cookie in your browser.
        </p>
        <div className="pt-4 flex gap-4">
          <Link href="/settings" className={buttonVariants({ variant: "outline" })}>
            Settings
          </Link>
          <Link href="/" className={cn(buttonVariants({ variant: "default" }), "bg-brand-orange hover:bg-brand-orange-hover")}>
            Back to Home
          </Link>
        </div>
      </div>
    </div>
  )
}
