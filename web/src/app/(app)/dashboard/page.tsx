'use client'
/**
 * Dashboard Page — Implementation Plan §4.16 · Blueprint v2.0 C1.
 *
 * 8 steps per Blueprint:
 * 1. Stat cards: Total Hours, Billable Hours, Billable Amount (hidden from Viewer), Active Projects
 * 2. Skeletons matching card shapes
 * 3. Billable Amount card: absent for Viewer role
 * 4. Top Projects chart (Recharts, orange bars)
 * 5. Quick Start section
 * 6. Last 5 entries with entry status badges
 * 7. Locked rows: edit/delete opacity-30 cursor-not-allowed
 * 8. Continue ▶ button (absent on pending/approved)
 */

import { useState, useEffect } from 'react'
import { useWorkspaceStore } from '@/stores/workspace-store'
import { useTimeEntries, useCurrentTimer, useStartTimer } from '@/features/time-entries/hooks'
import { useWorkspaces } from '@/features/settings/hooks'
import { useMe } from '@/features/settings/hooks'
import { formatDuration, formatMoney, cn } from '@/lib/utils'
import { ThemeToggle } from '@/components/ThemeToggle'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import {
  Clock,
  DollarSign,
  FolderOpen,
  TrendingUp,
  Play,
  Pencil,
  Trash2,
  Lock,
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

// ─── Skeleton ─────────────────────────────────────────────────────────────────

function StatCardSkeleton() {
  return (
    <div className="bg-card border border-border rounded-xl p-5 space-y-3 animate-pulse">
      <div className="h-3.5 bg-muted rounded w-1/2" />
      <div className="h-8 bg-muted rounded w-3/4" />
      <div className="h-3 bg-muted rounded w-1/3" />
    </div>
  )
}

function RecentEntrySkeleton() {
  return (
    <div className="flex items-center gap-3 py-3 border-b border-border last:border-0 animate-pulse">
      <div className="h-3 bg-muted rounded flex-1" />
      <div className="h-3 bg-muted rounded w-16" />
      <div className="h-3 bg-muted rounded w-12" />
    </div>
  )
}

// ─── Stat Card ────────────────────────────────────────────────────────────────

interface StatCardProps {
  title: string
  value: string
  subtitle?: string
  icon: React.ReactNode
  accent?: boolean
}

function StatCard({ title, value, subtitle, icon, accent }: StatCardProps) {
  return (
    <div
      className={cn(
        'bg-card border border-border rounded-xl p-5 flex flex-col gap-2 transition-shadow hover:shadow-md',
        accent && 'border-[#F06900]/30 bg-gradient-to-br from-[#FFF0E6]/60 to-card dark:from-orange-900/10',
      )}
    >
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{title}</p>
        <span
          className={cn(
            'p-1.5 rounded-lg',
            accent ? 'bg-[#FFF0E6] text-[#F06900] dark:bg-orange-900/20' : 'bg-muted text-muted-foreground',
          )}
        >
          {icon}
        </span>
      </div>
      <p className={cn('text-2xl font-bold tracking-tight', accent && 'text-[#F06900]')}>
        {value}
      </p>
      {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
    </div>
  )
}

// ─── Running Timer Card ───────────────────────────────────────────────────────

function formatElapsed(totalSeconds: number) {
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  const s = totalSeconds % 60
  return [h, m, s].map((v) => String(v).padStart(2, '0')).join(':')
}

function RunningTimerCard({ entry }: { entry: any }) {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    if (!entry?.start_time) return
    const start = new Date(entry.start_time).getTime()
    const update = () => setElapsed(Math.floor((Date.now() - start) / 1000))
    update()
    const int = setInterval(update, 1000)
    return () => clearInterval(int)
  }, [entry?.start_time])

  return (
    <div className="bg-card border border-[#F06900]/30 rounded-xl p-5 flex flex-col gap-2 transition-shadow hover:shadow-md bg-gradient-to-br from-[#FFF0E6]/60 to-card dark:from-orange-900/10">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Running Timer</p>
        <span className="p-1.5 rounded-lg bg-[#FFF0E6] text-[#F06900] dark:bg-orange-900/20">
          <Clock className="w-4 h-4" />
        </span>
      </div>
      <p className="text-2xl font-bold tracking-tight text-[#F06900] font-mono">
        {formatElapsed(elapsed)}
      </p>
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground truncate">
        <span className="w-2 h-2 rounded-full bg-[#F06900] animate-pulse flex-shrink-0" />
        <span className="truncate">{entry.project_name || 'No project'}</span>
      </div>
    </div>
  )
}

// ─── Status badge ─────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    draft: 'bg-[hsl(var(--status-draft-muted))] text-[hsl(var(--status-draft))]',
    running: 'bg-[#FFF0E6] text-[#F06900] dark:bg-orange-900/20',
    pending: 'bg-[hsl(var(--status-pending-muted))] text-[hsl(var(--status-pending))]',
    approved: 'bg-[hsl(var(--status-approved-muted))] text-[hsl(var(--status-approved))]',
  }
  return (
    <span className={cn('px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase', map[status] ?? map.draft)}>
      {status}
    </span>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const { activeWorkspaceId } = useWorkspaceStore()
  const { data: user } = useMe()
  const { data: workspaces } = useWorkspaces()

  const activeWorkspace = workspaces?.find((w: any) => w.id === activeWorkspaceId)
  const userRole = activeWorkspace?.role ?? 'member'
  const isViewer = userRole === 'viewer'

  // Fetch last 30 days of entries for stats
  const today = new Date()
  const thirtyDaysAgo = new Date(today)
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)

  const { data: entriesData, isLoading } = useTimeEntries({
    workspace_id: activeWorkspaceId ?? '',
    limit: 200,
    date_from: thirtyDaysAgo.toISOString().split('T')[0],
    date_to: today.toISOString().split('T')[0],
  })

  const { data: currentEntry } = useCurrentTimer(activeWorkspaceId)

  const entries = entriesData?.data ?? []

  // ── Stats ──────────────────────────────────────────────────────────────────
  const completedEntries = entries.filter((e) => e.status !== 'running')
  const totalSeconds = completedEntries.reduce((sum, e) => sum + (e.duration_seconds ?? 0), 0)
  const billableSeconds = completedEntries
    .filter((e) => e.billable)
    .reduce((sum, e) => sum + (e.duration_seconds ?? 0), 0)
  const billableCents = !isViewer
    ? completedEntries
        .filter((e) => e.billable && e.billable_amount)
        .reduce((sum, e) => sum + parseFloat(e.billable_amount ?? '0') * 100, 0)
    : 0
  const activeProjects = new Set(entries.map((e) => e.project_id)).size

  // ── Top projects chart data ────────────────────────────────────────────────
  const projectMap: Record<string, { name: string; seconds: number; color: string | null }> = {}
  completedEntries.forEach((e) => {
    if (!projectMap[e.project_id]) {
      projectMap[e.project_id] = { name: e.project_name, seconds: 0, color: e.project_color }
    }
    projectMap[e.project_id].seconds += e.duration_seconds ?? 0
  })
  const chartData = Object.values(projectMap)
    .sort((a, b) => b.seconds - a.seconds)
    .slice(0, 6)
    .map((p) => ({ name: p.name, hours: +(p.seconds / 3600).toFixed(1), color: p.color }))

  // ── Recent entries (last 5) ────────────────────────────────────────────────
  const recentEntries = completedEntries.slice(0, 5)

  const isLocked = (entry: (typeof entries)[0]) => {
    return entry.status === 'pending' || entry.status === 'approved'
  }

  // ── Continue button logic ──────────────────────────────────────────────────
  const startTimer = useStartTimer(activeWorkspaceId ?? '')
  const [switchEntry, setSwitchEntry] = useState<(typeof entries)[0] | null>(null)

  const handleContinue = async (entry: (typeof entries)[0], force: boolean) => {
    await startTimer.mutateAsync({
      project_id: entry.project_id,
      task_id: entry.task_id ?? undefined,
      description: entry.description ?? undefined,
      billable: entry.billable,
      force,
    })
    setSwitchEntry(null)
  }

  const onContinueClick = (entry: (typeof entries)[0]) => {
    if (currentEntry) {
      // A timer is already running — show switch confirmation
      setSwitchEntry(entry)
    } else {
      handleContinue(entry, false)
    }
  }

    return (
    <>
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Last 30 days · {activeWorkspace?.name ?? 'Your workspace'}
          </p>
        </div>
        <ThemeToggle />
      </div>

      {/* ── Stat Cards ── */}
      <div className={cn('grid gap-4', isViewer ? 'grid-cols-1 sm:grid-cols-3' : 'grid-cols-2 sm:grid-cols-4')}>
        {isLoading ? (
          <>
            <StatCardSkeleton />
            <StatCardSkeleton />
            {!isViewer && <StatCardSkeleton />}
            <StatCardSkeleton />
          </>
        ) : (
          <>
            <StatCard
              title="Total Hours"
              value={formatDuration(totalSeconds)}
              subtitle="All tracked time"
              icon={<Clock className="w-4 h-4" />}
            />
            <StatCard
              title="Billable Hours"
              value={formatDuration(billableSeconds)}
              subtitle={`${totalSeconds > 0 ? Math.round((billableSeconds / totalSeconds) * 100) : 0}% of total`}
              icon={<TrendingUp className="w-4 h-4" />}
            />
            {/* Billable Amount: hidden from Viewer (Blueprint C1 step 3) */}
            {!isViewer && (
              <StatCard
                title="Billable Amount"
                value={formatMoney(Math.round(billableCents))}
                subtitle="Earned this period"
                icon={<DollarSign className="w-4 h-4" />}
                accent
              />
            )}
            {/* Active Projects or Running Timer */}
            {currentEntry ? (
              <RunningTimerCard entry={currentEntry} />
            ) : (
              <StatCard
                title="Active Projects"
                value={String(activeProjects)}
                subtitle="Projects tracked"
                icon={<FolderOpen className="w-4 h-4" />}
              />
            )}
          </>
        )}
      </div>

      {/* ── Two column: Chart + Recent ── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Top Projects Chart */}
        <div className="lg:col-span-3 bg-card border border-border rounded-xl p-5">
          <h2 className="text-sm font-semibold mb-4">Top Projects</h2>
          {isLoading ? (
            <div className="h-48 bg-muted rounded animate-pulse" />
          ) : chartData.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">
              No tracked time yet
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 16 }}>
                <XAxis
                  type="number"
                  tickFormatter={(v: number) => `${v}h`}
                  tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={90}
                  tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  cursor={{ fill: 'hsl(var(--muted))', opacity: 0.4 }}
                  formatter={(v: unknown) => [`${Number(v).toFixed(1)}h`, 'Hours']}
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    fontSize: '12px',
                    color: 'hsl(var(--foreground))',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                  }}
                />
                <Bar dataKey="hours" radius={[0, 4, 4, 0]} maxBarSize={20} animationDuration={1000}>
                  {chartData.map((entry, i) => (
                    <Cell
                      key={i}
                      fill={entry.color ?? '#FE6900'}
                      className="transition-opacity hover:opacity-80 duration-300"
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Recent Entries */}
        <div className="lg:col-span-2 bg-card border border-border rounded-xl p-5">
          <h2 className="text-sm font-semibold mb-4">Recent Entries</h2>
          {isLoading ? (
            <div className="space-y-1">
              {[1, 2, 3, 4, 5].map((i) => <RecentEntrySkeleton key={i} />)}
            </div>
          ) : recentEntries.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground text-sm gap-2">
              <Clock className="w-8 h-8 opacity-30" />
              <p>No entries yet.<br />Start a timer to track time.</p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {recentEntries.map((entry) => {
                const locked = isLocked(entry)
                return (
                  <div
                    key={entry.id}
                    className="group flex items-start gap-2 py-2.5 first:pt-0 last:pb-0"
                  >
                    {/* Color dot */}
                    <span
                      className="mt-1 inline-block w-2 h-2 rounded-full flex-shrink-0"
                      style={{ backgroundColor: entry.project_color ?? '#6B7280' }}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium truncate">{entry.project_name}</p>
                      {entry.description && (
                        <p className="text-[11px] text-muted-foreground truncate">{entry.description}</p>
                      )}
                      <div className="flex items-center gap-2 mt-0.5">
                        <StatusBadge status={entry.status} />
                        <span className="text-[11px] text-muted-foreground font-mono">
                          {formatDuration(entry.duration_seconds ?? 0)}
                        </span>
                      </div>
                    </div>
                    {/* Actions */}
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      {/* Continue: only for draft entries (Blueprint C1 step 8) */}
                      {entry.status === 'draft' && (
                        <button
                          id={`entry-continue-${entry.id}`}
                          title="Continue this entry"
                          onClick={() => onContinueClick(entry)}
                          disabled={startTimer.isPending}
                          className="p-1 rounded text-muted-foreground hover:text-[#F06900] hover:bg-[#FFF0E6] dark:hover:bg-orange-900/20 transition-colors disabled:opacity-40"
                        >
                          <Play className="w-3 h-3 fill-current" />
                        </button>
                      )}
                      {/* Edit / Delete: locked rows dimmed (Blueprint C1 step 7) */}
                      <button
                        id={`entry-edit-${entry.id}`}
                        title={locked ? 'Entry is locked' : 'Edit'}
                        className={cn(
                          'p-1 rounded text-muted-foreground hover:text-foreground hover:bg-muted transition-colors',
                          locked && 'opacity-30 cursor-not-allowed',
                        )}
                        disabled={locked}
                      >
                        <Pencil className="w-3 h-3" />
                      </button>
                      <button
                        id={`entry-delete-${entry.id}`}
                        title={locked ? 'Entry is locked' : 'Delete'}
                        className={cn(
                          'p-1 rounded text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors',
                          locked && 'opacity-30 cursor-not-allowed',
                        )}
                        disabled={locked}
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>

    {/* ── Switch Timer Dialog (Continue button) ── */}
    <AlertDialog open={!!switchEntry} onOpenChange={(o) => !o && setSwitchEntry(null)}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Switch active timer?</AlertDialogTitle>
          <AlertDialogDescription>
            A timer is already running for <strong>{currentEntry?.project_name}</strong>. Starting this entry will stop the current timer and save its tracked time.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            className="bg-[#F06900] text-white hover:bg-[#D95E00]"
            onClick={() => switchEntry && handleContinue(switchEntry, true)}
          >
            Stop &amp; Continue
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
    </>
  )
}
