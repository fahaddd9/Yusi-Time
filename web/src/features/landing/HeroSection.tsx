"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { Button, buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { ArrowRight, Play, LayoutDashboard } from "lucide-react"

export function HeroSection() {
  return (
    <section className="relative min-h-[90vh] flex items-center pt-24 pb-16 overflow-hidden bg-brand-navy">
      {/* Background styling matching the spec */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: "radial-gradient(circle, #ffffff 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-brand-orange/20 blur-[120px] pointer-events-none" />

      <div className="container mx-auto px-4 md:px-6 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-8 items-center">
          
          {/* Left: Copy & CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="space-y-8"
          >
            <div className="inline-flex items-center rounded-full border border-brand-orange/30 bg-brand-orange/10 px-3 py-1 text-sm text-brand-orange font-medium">
              <span className="flex h-2 w-2 rounded-full bg-brand-orange mr-2 animate-pulse" />
              Yusi Time v1.0 is here
            </div>

            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-white leading-[1.1]">
              <span className="block">Time tracking</span>
              <span className="block">that respects</span>
              <span className="block text-brand-orange">your focus.</span>
            </h1>

            <p className="text-lg md:text-xl text-slate-300 max-w-[500px] leading-relaxed">
              Ditch the clunky, ad-filled timers. Yusi Time is a minimalist, lightning-fast
              timesheet built for modern teams and freelancers who just want to get to work.
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              <Link href="/signup" className={cn(buttonVariants({ variant: "default", size: "lg" }), "bg-brand-orange hover:bg-brand-orange-hover text-white h-12 px-8 text-base shadow-[0_0_20px_rgba(240,105,0,0.3)] hover:shadow-[0_0_30px_rgba(240,105,0,0.5)] transition-all group flex items-center justify-center")}>
                Start tracking free
                <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link href="#demo" className={cn(buttonVariants({ variant: "outline", size: "lg" }), "h-12 px-8 text-base bg-white/5 border-white/10 text-white hover:bg-white/10 flex items-center justify-center")}>
                <Play className="w-4 h-4 mr-2" />
                See how it works
              </Link>
            </div>
            
            <p className="text-sm text-slate-400">
              No credit card required. Free for up to 5 users.
            </p>
          </motion.div>

          {/* Right: Abstract UI Preview */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="relative lg:h-[600px] flex items-center justify-center lg:justify-end"
          >
            {/* The main app card float animation */}
            <motion.div 
              animate={{ y: [-10, 10, -10] }}
              transition={{ repeat: Infinity, duration: 6, ease: "easeInOut" }}
              className="w-full max-w-[600px] rounded-2xl border border-white/10 bg-[#0C101A] shadow-2xl overflow-hidden"
            >
              {/* Browser chrome */}
              <div className="h-10 border-b border-white/10 bg-white/5 flex items-center px-4 gap-2">
                <div className="w-3 h-3 rounded-full bg-slate-600" />
                <div className="w-3 h-3 rounded-full bg-slate-600" />
                <div className="w-3 h-3 rounded-full bg-slate-600" />
              </div>
              
              {/* App UI mock */}
              <div className="p-6 space-y-6">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2 text-white font-semibold">
                    <LayoutDashboard className="w-5 h-5 text-brand-orange" />
                    Dashboard
                  </div>
                  <div className="text-sm text-slate-400">This Week: <span className="text-white font-mono">32:15:00</span></div>
                </div>

                {/* Fake active timer */}
                <div className="rounded-xl border border-brand-orange/30 bg-brand-orange/5 p-4 flex justify-between items-center">
                  <div className="space-y-1">
                    <div className="h-4 w-48 rounded bg-white/10" />
                    <div className="h-3 w-32 rounded bg-white/5" />
                  </div>
                  <div className="text-2xl font-mono font-bold text-brand-orange animate-pulse">
                    01:24:05
                  </div>
                </div>

                {/* Fake past entries */}
                <div className="space-y-3">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="rounded-lg border border-white/5 bg-white/5 p-3 flex justify-between items-center">
                      <div className="flex gap-4 items-center w-full">
                        <div className="h-2 w-2 rounded-full bg-brand-orange/50" />
                        <div className="space-y-2 flex-1">
                          <div className="h-3 w-1/3 rounded bg-white/10" />
                        </div>
                        <div className="text-sm font-mono text-slate-400">
                          0{i}:30:00
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          </motion.div>

        </div>
      </div>
    </section>
  )
}
