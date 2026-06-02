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
        "flex flex-col gap-3 px-3 py-4 border-b border-sidebar-border h-[5.5rem] justify-center overflow-hidden",
        !isMobile && "items-center lg:items-start lg:px-4"
      )}>
        {/* SKILL §1.1 — logo: always use SVG file, never recreate in code */}
        <img 
          src="/logo-dark.svg" 
          alt="Yusi Time" 
          className={cn("h-8 w-auto flex-shrink-0 dark:block")} 
        />
        
        {/* Workspace Switcher */}
        {!isMobile && (
          <div className="hidden lg:block w-full -mx-1">
            <DropdownMenu>
              <DropdownMenuTrigger className="w-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-lg">
                <div className="flex items-center justify-between hover:bg-sidebar-accent transition-colors duration-150 rounded-lg cursor-pointer px-2 py-1.5 w-full">
                  <span className="text-caption text-sidebar-foreground/60 truncate max-w-[150px] text-left">{workspaceName}</span>
                  <ChevronDown className="w-3 h-3 text-sidebar-foreground/60 flex-shrink-0 ml-1" />
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
        <div className={cn("px-2 pt-3 pb-1", !isMobile && "hidden lg:block")}>
          <span className="text-label uppercase tracking-wider text-sidebar-foreground/40">Workspace</span>
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
                  // SKILL §6.2 — active nav item EXACT CLASS STRING
                  ? "flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm bg-primary/10 text-white font-medium border-l-[2.5px] border-primary pl-[10px] shadow-[inset_0_0_0_0.5px_rgba(254,105,0,0.12)] transition-all duration-150"
                  // SKILL §6.2 — inactive nav item EXACT CLASS STRING
                  : "flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm text-sidebar-foreground hover:bg-sidebar-accent hover:text-white active:scale-[0.98] transition-all duration-150",
                !isMobile && "justify-center lg:justify-start"
              )}
            >
              <item.icon className="w-4 h-4 flex-shrink-0" />
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
                ? "w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm bg-primary/10 text-white font-medium border-l-[2.5px] border-primary pl-[10px] shadow-[inset_0_0_0_0.5px_rgba(254,105,0,0.12)] transition-all duration-150"
                : "w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm text-sidebar-foreground hover:bg-sidebar-accent hover:text-white active:scale-[0.98] transition-all duration-150",
              !isMobile && "justify-center lg:justify-start"
            )}
          >
            <TrendingUp className="w-4 h-4 flex-shrink-0" />
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
                          ? "flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm bg-primary/10 text-white font-medium border-l-[2.5px] border-primary pl-[10px] shadow-[inset_0_0_0_0.5px_rgba(254,105,0,0.12)] transition-all duration-150"
                          : "flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm text-sidebar-foreground hover:bg-sidebar-accent hover:text-white active:scale-[0.98] transition-all duration-150",
                        isMobile ? "pl-5" : "justify-center lg:justify-start lg:pl-5"
                      )}
                    >
                      <sub.icon className={cn("w-4 h-4 flex-shrink-0", !isMobile && "hidden lg:inline")} />
                      <span className={cn("truncate", !isMobile && "hidden lg:inline")}>{sub.label}</span>
                    </Link>
                  )
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Approvals + Settings */}
        <div className={cn("px-2 pt-3 pb-1 mt-2", !isMobile && "hidden lg:block")}>
          <span className="text-label uppercase tracking-wider text-sidebar-foreground/40">Settings</span>
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
                  ? "flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm bg-primary/10 text-white font-medium border-l-[2.5px] border-primary pl-[10px] shadow-[inset_0_0_0_0.5px_rgba(254,105,0,0.12)] transition-all duration-150"
                  : "flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm text-sidebar-foreground hover:bg-sidebar-accent hover:text-white active:scale-[0.98] transition-all duration-150",
                !isMobile && "justify-center lg:justify-start"
              )}
            >
              <item.icon className="w-4 h-4 flex-shrink-0" />
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
              "flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm text-sidebar-foreground hover:bg-sidebar-accent hover:text-white transition-all duration-150",
              !isMobile && "justify-center lg:justify-start"
            )}
          >
            <Crown className="w-4 h-4 flex-shrink-0 text-primary" />
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
        <div className={cn("flex-1 min-w-0", !isMobile && "hidden lg:block")}>
          <p className="text-caption text-sidebar-foreground/60 truncate">{userName}</p>
        </div>
        <div className={cn("flex items-center gap-1", !isMobile && "hidden lg:flex")}>
          <ThemeToggle className="h-7 w-7 text-sidebar-foreground hover:text-foreground hover:bg-sidebar-accent" />
          {onLogout && (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-sidebar-foreground/40 hover:text-destructive hover:bg-sidebar-accent transition-colors"
              onClick={onLogout}
              aria-label="Log out"
              title="Log out"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>
    </aside>
  )
}
