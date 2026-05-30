"use client"

import { useEffect, useState } from "react"
import { motion, useMotionValue, useTransform, animate } from "framer-motion"

function AnimatedCounter({ from, to, suffix = "", duration = 2 }: { from: number; to: number; suffix?: string; duration?: number }) {
  const count = useMotionValue(from)
  const rounded = useTransform(count, (latest) => Math.round(latest))
  const display = useTransform(rounded, (latest) => `${latest}${suffix}`)
  const [isInView, setIsInView] = useState(false)

  useEffect(() => {
    if (isInView) {
      const controls = animate(count, to, { duration, ease: "easeOut" })
      return controls.stop
    }
  }, [isInView, count, to, duration])

  return (
    <motion.span 
      onViewportEnter={() => setIsInView(true)}
      viewport={{ once: true, margin: "-50px" }}
    >
      {display}
    </motion.span>
  )
}

export function SocialProofStrip() {
  return (
    <section className="bg-brand-navy border-t border-white/5 py-12">
      <div className="container mx-auto px-4 md:px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center divide-x divide-white/10">
          <div className="space-y-2">
            <h3 className="text-3xl md:text-4xl font-bold text-white font-mono">
              <AnimatedCounter from={0} to={99} suffix=".9%" />
            </h3>
            <p className="text-sm text-slate-400 font-medium tracking-wide uppercase">Uptime SLA</p>
          </div>
          <div className="space-y-2">
            <h3 className="text-3xl md:text-4xl font-bold text-white font-mono">
              <AnimatedCounter from={0} to={50} suffix="ms" />
            </h3>
            <p className="text-sm text-slate-400 font-medium tracking-wide uppercase">Average Latency</p>
          </div>
          <div className="space-y-2">
            <h3 className="text-3xl md:text-4xl font-bold text-white font-mono">
              <AnimatedCounter from={0} to={0} suffix="s" />
            </h3>
            <p className="text-sm text-slate-400 font-medium tracking-wide uppercase">Setup Time</p>
          </div>
          <div className="space-y-2">
            <h3 className="text-3xl md:text-4xl font-bold text-white font-mono">
              <AnimatedCounter from={0} to={100} suffix="%" />
            </h3>
            <p className="text-sm text-slate-400 font-medium tracking-wide uppercase">Focus</p>
          </div>
        </div>
      </div>
    </section>
  )
}
