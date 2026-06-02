'use client'

/**
 * Settings layout — sidebar navigation within settings pages.
 *
 * Settings sub-nav:
 *   - Workspace (admin only for mutations, visible to all)
 *   - Members (all roles)
 *   - Profile (all roles)
 *   - Account (all roles)
 */

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Building2, Users, User, Shield } from 'lucide-react'
import { cn } from '@/lib/utils'

const settingsNav = [
  { href: '/settings/workspace', label: 'Workspace', icon: Building2 },
  { href: '/settings/members', label: 'Members', icon: Users },
  { href: '/settings/profile', label: 'Profile', icon: User },
]

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  return (
    <div className="flex h-full">
      {/* Settings sub-sidebar */}
      <aside className="w-52 border-r border-border bg-card/50 flex-shrink-0 p-3 space-y-0.5">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider px-2 py-1 mb-1">
          Settings
        </p>
        {settingsNav.map(({ href, label, icon: Icon }) => {
          const isActive = pathname.startsWith(href)
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'flex items-center gap-2.5 px-2 py-2 rounded-md text-sm transition-colors',
                isActive
                  ? 'bg-brand-orange/10 text-brand-orange font-medium'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted'
              )}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </Link>
          )
        })}
      </aside>

      {/* Settings content */}
      <div className="flex-1 overflow-y-auto">
        {children}
      </div>
    </div>
  )
}
