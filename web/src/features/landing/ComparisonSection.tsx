"use client"

import { CheckCircle2, X } from "lucide-react"

const comparisons = [
  { feature: "Time Tracking", yusi: true, clockify: true, generic: true },
  { feature: "No Required Fields on Start", yusi: true, clockify: false, generic: false },
  { feature: "Granular Role Permissions", yusi: true, clockify: true, generic: false },
  { feature: "Sub-50ms Navigation", yusi: true, clockify: false, generic: false },
  { feature: "Modern Dark Mode", yusi: true, clockify: true, generic: false },
  { feature: "Webhooks API", yusi: true, clockify: true, generic: false },
  { feature: "Free for Small Teams (up to 5)", yusi: true, clockify: true, generic: false },
  { feature: "No Ads or Upsell Popups", yusi: true, clockify: false, generic: true },
]

export function ComparisonSection() {
  return (
    <section className="py-24 bg-background">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground">
            Why choose Yusi Time?
          </h2>
          <p className="text-lg text-muted-foreground">
            See how we stack up against the bloated industry standards and generic tools.
          </p>
        </div>

        <div className="max-w-4xl mx-auto overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr>
                <th className="p-4 border-b border-border font-semibold text-foreground w-2/5">Feature</th>
                <th className="p-4 border-b border-border font-bold text-brand-orange text-center w-1/5 bg-brand-orange/5 rounded-t-lg">Yusi Time</th>
                <th className="p-4 border-b border-border font-semibold text-muted-foreground text-center w-1/5">Clockify</th>
                <th className="p-4 border-b border-border font-semibold text-muted-foreground text-center w-1/5">Generic Trackers</th>
              </tr>
            </thead>
            <tbody>
              {comparisons.map((row, i) => (
                <tr key={i} className="hover:bg-muted/50 transition-colors">
                  <td className="p-4 border-b border-border font-medium text-foreground">{row.feature}</td>
                  <td className="p-4 border-b border-border text-center bg-brand-orange/5">
                    {row.yusi ? <CheckCircle2 className="w-5 h-5 mx-auto text-brand-orange" /> : <X className="w-5 h-5 mx-auto text-muted-foreground" />}
                  </td>
                  <td className="p-4 border-b border-border text-center">
                    {row.clockify ? <CheckCircle2 className="w-5 h-5 mx-auto text-slate-400" /> : <X className="w-5 h-5 mx-auto text-slate-300" />}
                  </td>
                  <td className="p-4 border-b border-border text-center">
                    {row.generic ? <CheckCircle2 className="w-5 h-5 mx-auto text-slate-400" /> : <X className="w-5 h-5 mx-auto text-slate-300" />}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}
