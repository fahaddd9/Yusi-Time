"use client"

import Link from "next/link"
import { Button, buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export function FinalCTA() {
  return (
    <section className="py-24 bg-brand-navy relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-brand-orange/10 blur-[120px] pointer-events-none" />
      
      <div className="container mx-auto px-4 md:px-6 relative z-10 text-center space-y-8">
        <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white">
          Ready to take back your time?
        </h2>
        <p className="text-xl text-slate-300 max-w-2xl mx-auto">
          Join thousands of professionals who have ditched their bloated timesheets for Yusi Time.
        </p>
        
        <div className="pt-4">
          <Link href="/signup" className={cn(buttonVariants({ variant: "default", size: "lg" }), "bg-brand-orange hover:bg-brand-orange-hover text-white h-14 px-10 text-lg shadow-[0_0_20px_rgba(240,105,0,0.4)] hover:shadow-[0_0_40px_rgba(240,105,0,0.6)] transition-all flex items-center justify-center max-w-fit mx-auto")}>
            Start tracking for free
          </Link>
          <p className="mt-4 text-sm text-slate-400">
            Takes 30 seconds to set up. No credit card required.
          </p>
        </div>
      </div>
    </section>
  )
}
