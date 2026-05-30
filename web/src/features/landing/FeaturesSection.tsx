"use client"

import { motion } from "framer-motion"
import { Timer, LayoutDashboard, Users, Fingerprint, Webhook, Zap } from "lucide-react"

const features = [
  {
    title: "One-Click Timer",
    description: "Start tracking time instantly. No required fields, no popups blocking your flow. Fill in the details later.",
    icon: Timer,
  },
  {
    title: "Clean Dashboard",
    description: "See exactly where your time goes without drowning in data. Elegant visualizations that make sense instantly.",
    icon: LayoutDashboard,
  },
  {
    title: "Team Management",
    description: "Invite your team, set hourly rates, and manage roles with granular permissions (Admin, Manager, Member, Viewer).",
    icon: Users,
  },
  {
    title: "Role-Based Access",
    description: "Keep financial data secure. Viewers can only see their own time, while managers can oversee projects and approvals.",
    icon: Fingerprint,
  },
  {
    title: "Webhooks API",
    description: "Connect Yusi Time to your favorite tools. Trigger external actions when a timer starts, stops, or an entry is approved.",
    icon: Webhook,
  },
  {
    title: "Lightning Fast",
    description: "Built on Next.js App Router and FastAPI. Everything is optimized for speed, so you never wait for a page to load.",
    icon: Zap,
  },
]

export function FeaturesSection() {
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  }

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  }

  return (
    <section className="py-24 bg-background">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground">
            Everything you need. Nothing you don't.
          </h2>
          <p className="text-lg text-muted-foreground">
            Yusi Time strips away the clutter of traditional time trackers, leaving only the essential tools your team needs to stay productive.
          </p>
        </div>

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-100px" }}
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-8"
        >
          {features.map((feature, i) => (
            <motion.div key={i} variants={item} className="bg-card border border-border p-8 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-brand-orange/10 flex items-center justify-center mb-6">
                <feature.icon className="w-6 h-6 text-brand-orange" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-3">{feature.title}</h3>
              <p className="text-muted-foreground leading-relaxed">{feature.description}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
