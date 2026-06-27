'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  CalendarClock,
  FolderOpen,
  BarChart3,
  CheckSquare,
  Settings,
  ChevronRight,
  FileText,
  TrendingUp,
  Calendar,
  LogOut,
  ChevronDown,
  Crown
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'

interface SidebarProps {
  userRole: string
  userName: string
  userEmail: string
  userAvatarUrl?: string | null
  workspaceName: string
  isSuperAdmin?: boolean
  onLogout?: () => void
  isMobile?: boolean
  onNavClick?: () => void
}

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['admin', 'manager', 'member', 'viewer'] },
  { href: '/timesheet', label: 'Timesheet', icon: CalendarClock, roles: ['admin', 'manager', 'member', 'viewer'] },
  { href: '/projects', label: 'Projects', icon: FolderOpen, roles: ['admin', 'manager', 'member', 'viewer'] },
  { href: '/approvals', label: 'Approvals', icon: CheckSquare, roles: ['admin', 'manager'] }, // PRD §4: Approvals absent for member/viewer
  { href: '/settings', label: 'Settings', icon: Settings, roles: ['admin', 'manager', 'member', 'viewer'] },
]

const reportSubItems = [
  { href: '/reports/summary', label: 'Summary', icon: BarChart3 },
  { href: '/reports/detailed', label: 'Detailed', icon: FileText },
  { href: '/reports/weekly', label: 'Weekly', icon: Calendar },
]

import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'

export function Sidebar({
  userRole,
  userName,
  userEmail,
  userAvatarUrl,
  workspaceName,
  workspaces = [],
  activeWorkspaceId,
  onWorkspaceChange,
  isSuperAdmin,
  onLogout,
  isMobile,
  onNavClick
}: SidebarProps & { workspaces?: any[], activeWorkspaceId?: string, onWorkspaceChange?: (id: string) => void }) {
  const pathname = usePathname()
  const [reportsOpen, setReportsOpen] = useState(pathname.startsWith('/reports'))

  const visibleNavItems = navItems.filter((item) => item.roles.includes(userRole))
  const isReportsActive = pathname.startsWith('/reports')

  const initials = userName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  return (
    <aside className={cn(
      "bg-[hsl(var(--sidebar-background))] flex flex-col flex-shrink-0 h-full border-r border-sidebar-border transition-all duration-300",
      isMobile ? "w-60" : "w-14 lg:w-60 group"
    )}>
      {/* SKILL §6.2 - Logo area */}
      <div className={cn(
        "flex flex-col gap-2 px-3 pt-4 pb-3 border-b border-sidebar-border",
        !isMobile && "lg:px-4"
      )}>
        {/* SKILL §1.1 — logo: always use SVG file, never recreate in code */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img 
          src="/logo-dark.svg" 
          alt="Yusi Time" 
          className={cn("h-8 w-auto flex-shrink-0 dark:block self-center")} 
        />
        
        {/* Workspace Switcher */}
        {!isMobile && (
          <div className="hidden lg:block w-full -mx-1">
            <DropdownMenu>
              <DropdownMenuTrigger className="w-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-lg">
                <div className="flex items-center justify-between hover:bg-white/5 transition-all duration-200 rounded-xl cursor-pointer px-3 py-2 w-full border border-transparent hover:border-sidebar-border/50 group">
                  <span className="text-[15px] font-medium text-sidebar-foreground group-hover:text-white transition-colors truncate max-w-[150px] text-left">{workspaceName}</span>
                  <ChevronDown className="w-4 h-4 text-sidebar-foreground/60 flex-shrink-0 ml-1 group-hover:text-white transition-colors" />
                </div>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-[200px] bg-card border-border shadow-lg z-50">
                {workspaces.map((ws) => (
                  <DropdownMenuItem
                    key={ws.id}
                    onClick={() => {
                      onWorkspaceChange?.(ws.id)
                      onNavClick?.()
                    }}
                    className={cn(
                      "cursor-pointer text-sm py-2 px-3",
                      ws.id === activeWorkspaceId ? "bg-primary/10 text-primary font-medium" : "text-foreground"
                    )}
                  >
                    <span className="truncate">{ws.name}</span>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5 overflow-x-hidden">
        {/* Section Labels */}
        <div className={cn("px-3 pt-4 pb-2", !isMobile && "hidden lg:block")}>
          <span className="text-[11px] font-bold tracking-[0.15em] text-sidebar-foreground/50 uppercase">Workspace</span>
        </div>

        {visibleNavItems.slice(0, 3).map((item) => {
          const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href))
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavClick}
              className={cn(
                isActive
                  ? "relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-[14px] bg-brand-orange/15 text-brand-orange font-semibold shadow-sm transition-all duration-200 before:absolute before:left-0 before:top-1/2 before:-translate-y-1/2 before:w-1 before:h-[60%] before:bg-brand-orange before:rounded-r-full"
                  : "group flex items-center gap-3 px-3 py-2.5 rounded-xl text-[14px] text-sidebar-foreground hover:bg-white/5 hover:text-white active:scale-[0.98] transition-all duration-200",
                !isMobile && "justify-center lg:justify-start"
              )}
            >
              <item.icon className={cn("w-5 h-5 flex-shrink-0 transition-transform duration-300 group-hover:scale-110", isActive && "text-brand-orange")} />
              <span className={cn("truncate", !isMobile && "hidden lg:inline")}>{item.label}</span>
            </Link>
          )
        })}

        {/* Reports sub-navigation */}
        <div>
          <button
            onClick={() => setReportsOpen((o) => !o)}
            className={cn(
              isReportsActive
                ? "relative w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-[14px] bg-brand-orange/15 text-brand-orange font-semibold shadow-sm transition-all duration-200 before:absolute before:left-0 before:top-1/2 before:-translate-y-1/2 before:w-1 before:h-[60%] before:bg-brand-orange before:rounded-r-full"
                : "group w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-[14px] text-sidebar-foreground hover:bg-white/5 hover:text-white active:scale-[0.98] transition-all duration-200",
              !isMobile && "justify-center lg:justify-start"
            )}
          >
            <TrendingUp className={cn("w-5 h-5 flex-shrink-0 transition-transform duration-300 group-hover:scale-110", isReportsActive && "text-brand-orange")} />
            <span className={cn("flex-1 text-left truncate", !isMobile && "hidden lg:inline")}>Reports</span>
            <ChevronRight
              className={cn(
                'w-4 h-4 transition-transform duration-200 flex-shrink-0',
                reportsOpen ? 'rotate-90' : '',
                !isMobile && "hidden lg:inline"
              )}
            />
          </button>

          <div
            className={cn(
              "grid transition-all duration-200 ease-in-out",
              reportsOpen ? "grid-rows-[1fr] opacity-100 mt-0.5" : "grid-rows-[0fr] opacity-0"
            )}
          >
            <div className="overflow-hidden">
              <div className={cn(
                "space-y-0.5",
                isMobile ? "ml-[20px] pl-0 border-l border-sidebar-border" : "lg:ml-[20px] lg:pl-0 lg:border-l lg:border-sidebar-border mt-1"
              )}>
                {reportSubItems.map((sub) => {
                  const isActive = pathname === sub.href
                  return (
                    <Link
                      key={sub.href}
                      href={sub.href}
                      onClick={onNavClick}
                      className={cn(
                        isActive
                          ? "relative flex items-center gap-3 px-3 py-2 rounded-xl text-[13px] bg-brand-orange/15 text-brand-orange font-semibold transition-all duration-200 before:absolute before:left-0 before:top-1/2 before:-translate-y-1/2 before:w-[3px] before:h-1/2 before:bg-brand-orange before:rounded-r-full"
                          : "group flex items-center gap-3 px-3 py-2 rounded-xl text-[13px] text-sidebar-foreground hover:bg-white/5 hover:text-white active:scale-[0.98] transition-all duration-200",
                        isMobile ? "pl-5" : "justify-center lg:justify-start lg:pl-5"
                      )}
                    >
                      <sub.icon className={cn("w-[18px] h-[18px] flex-shrink-0 transition-transform duration-300 group-hover:scale-110", !isMobile && "hidden lg:inline", isActive && "text-brand-orange")} />
                      <span className={cn("truncate", !isMobile && "hidden lg:inline")}>{sub.label}</span>
                    </Link>
                  )
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Approvals + Settings */}
        <div className={cn("px-3 pt-5 pb-2 mt-2", !isMobile && "hidden lg:block")}>
          <span className="text-[11px] font-bold tracking-[0.15em] text-sidebar-foreground/50 uppercase">Settings</span>
        </div>
        {visibleNavItems.slice(3).map((item) => {
          const isActive = pathname.startsWith(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavClick}
              className={cn(
                isActive
                  ? "relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-[14px] bg-brand-orange/15 text-brand-orange font-semibold shadow-sm transition-all duration-200 before:absolute before:left-0 before:top-1/2 before:-translate-y-1/2 before:w-1 before:h-[60%] before:bg-brand-orange before:rounded-r-full"
                  : "group flex items-center gap-3 px-3 py-2.5 rounded-xl text-[14px] text-sidebar-foreground hover:bg-white/5 hover:text-white active:scale-[0.98] transition-all duration-200",
                !isMobile && "justify-center lg:justify-start"
              )}
            >
              <item.icon className={cn("w-5 h-5 flex-shrink-0 transition-transform duration-300 group-hover:scale-110", isActive && "text-brand-orange")} />
              <span className={cn("truncate", !isMobile && "hidden lg:inline")}>{item.label}</span>
            </Link>
          )
        })}
      </nav>

      {/* Super Admin Link */}
      {isSuperAdmin && (
        <div className="px-2">
          <div className="mx-3 my-2 border-t border-sidebar-border" />
          <Link
            href="/superadmin"
            onClick={onNavClick}
            className={cn(
              "group flex items-center gap-3 px-3 py-2.5 rounded-xl text-[14px] text-sidebar-foreground hover:bg-white/5 hover:text-white active:scale-[0.98] transition-all duration-200",
              !isMobile && "justify-center lg:justify-start"
            )}
          >
            <Crown className="w-5 h-5 flex-shrink-0 text-brand-orange transition-transform duration-300 group-hover:scale-110" />
            <span className={cn("flex-1 truncate", !isMobile && "hidden lg:inline")}>Super Admin</span>
            <span className={cn("ml-auto text-[9px] bg-orange-950/60 text-primary border border-primary/30 px-1.5 py-0.5 rounded font-bold", !isMobile && "hidden lg:inline")}>
              SA
            </span>
          </Link>
        </div>
      )}

      {/* Sidebar Footer */}
      <div className={cn(
        "border-t border-sidebar-border px-3 py-3 flex items-center gap-2",
        !isMobile && "justify-center lg:justify-start"
      )}>
        <Avatar className="w-7 h-7 flex-shrink-0">
          {userAvatarUrl && <AvatarImage src={userAvatarUrl} alt={userName} />}
          <AvatarFallback className="bg-primary/20 text-primary text-[10px] font-semibold">
            {initials}
          </AvatarFallback>
        </Avatar>
        <div className={cn("flex flex-col min-w-0 transition-all", !isMobile && "hidden lg:flex")}>
          <span className="text-[14px] font-semibold text-sidebar-foreground truncate leading-tight group-hover:text-white transition-colors cursor-default">{userName || userEmail.split('@')[0]}</span>
          <span className="text-[11px] text-sidebar-foreground/60 uppercase tracking-wider">{userRole}</span>
        </div>
        <div className={cn("flex items-center gap-1.5 ml-auto", !isMobile && "hidden lg:flex")}>
          <div className="hover:bg-white/10 p-1.5 rounded-lg transition-colors cursor-pointer text-sidebar-foreground hover:text-white group" onClick={(e) => { e.preventDefault() }}>
            <ThemeToggle className="h-4 w-4" />
          </div>
          {onLogout && (
            <button
              onClick={onLogout}
              className="p-1.5 rounded-lg text-sidebar-foreground hover:bg-white/10 hover:text-white transition-colors group"
              title="Log out"
            >
              <LogOut className="w-[18px] h-[18px] transition-transform duration-300 group-hover:scale-110 text-brand-orange/80 group-hover:text-brand-orange" />
            </button>
          )}
        </div>
      </div>
    </aside>
  )
}
