"use client";

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { motion } from 'framer-motion'

const settingsNav = [
  { href: '/settings/profile', label: 'Profile' },
  { href: '/settings/workspace', label: 'Workspace' },
  { href: '/settings/members', label: 'Members' },
  { href: '/settings/clients', label: 'Clients' },
  { href: '/settings/tags', label: 'Tags' },
]

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  return (
    <div className="flex flex-col min-h-full">
      {/* Settings Header & Nav */}
      <div className="flex-shrink-0 border-b border-border/60 pb-0">
        <h1 className="text-3xl font-semibold text-foreground mb-6">Settings</h1>
        <div className="flex items-center gap-6 overflow-x-auto no-scrollbar">
          {settingsNav.map(({ href, label }) => {
            const isActive = pathname.startsWith(href)
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  'relative flex items-center gap-2 pb-4 text-sm font-medium transition-colors whitespace-nowrap outline-none focus-visible:ring-2 focus-visible:ring-brand-orange/50 rounded-sm',
                  isActive ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'
                )}
              >
                {label}
                {isActive && (
                  <motion.div
                    layoutId="active-tab-indicator"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-brand-orange rounded-t-full"
                    transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                  />
                )}
              </Link>
            )
          })}
        </div>
      </div>

      {/* Settings content */}
      <div className="flex-1 py-8">
        <div className="max-w-4xl mx-auto w-full">
          {children}
        </div>
      </div>
    </div>
  )
}
