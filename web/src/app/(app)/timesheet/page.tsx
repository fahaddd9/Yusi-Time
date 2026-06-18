'use client'
/**
 * Timesheet Grid Page — Implementation Plan §4.17 · Blueprint v2.0 D1.
 *
 * 7 sub-steps:
 * A. Week state (weekStart, day array)
 * B. Query: useTimeEntries for the week
 * C. Transform: group by project → task → day
 * D. Grid: header (today=orange circle), project groups, task rows, total row
 * E. Cell states: empty (+hover), draft (pencil-hover), pending (violet), approved (green)
 * F. AddEntry Sheet with live rounding preview (pure client-side)
 * G. Submit Week button: disabled + tooltip when no drafts. Entry list modal.
 */

import { useState, useMemo } from 'react'
import { ChevronLeft, ChevronRight, Plus, Pencil, Send } from 'lucide-react'
import { useWorkspaceStore } from '@/stores/workspace-store'
import { useTimeEntries, useCreateEntry, useUpdateEntry, useSubmitEntries } from '@/features/time-entries/hooks'
import { useWorkspace } from '@/features/settings/hooks'
import { useProjects, useTasks } from '@/features/projects/hooks'
import { formatDuration, cn } from '@/lib/utils'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { TimeEntry } from '@/features/time-entries/api'
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

// ─── Date helpers ─────────────────────────────────────────────────────────────

function addDays(date: Date, n: number): Date {
  const d = new Date(date)
  d.setDate(d.getDate() + n)
  return d
}

function toDateStr(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function toTimeString(d: Date): string {
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
}

function isSameDay(a: Date, b: Date): boolean {
  return toDateStr(a) === toDateStr(b)
}

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function getMondayOfWeek(date: Date): Date {
  const d = new Date(date)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day // shift sunday → -6
  d.setDate(d.getDate() + diff)
  d.setHours(0, 0, 0, 0)
  return d
}

// ─── Rounding preview (pure client-side, no API call) ─────────────────────────

function previewRounding(
  rawSeconds: number,
  workspace: { rounding_mode: string; rounding_interval_minutes: number | null } | undefined,
): { rounded: number; isActive: boolean; changed: boolean } {
  if (!workspace || workspace.rounding_mode === 'none' || !workspace.rounding_interval_minutes) {
    return { rounded: rawSeconds, isActive: false, changed: false }
  }
  const i = workspace.rounding_interval_minutes * 60
  const mode = workspace.rounding_mode
  const r =
    mode === 'nearest'
      ? Math.round(rawSeconds / i) * i
      : mode === 'up'
        ? Math.ceil(rawSeconds / i) * i
        : Math.floor(rawSeconds / i) * i
  return { rounded: r, isActive: true, changed: r !== rawSeconds }
}

// ─── Transform: group by project → task → day ─────────────────────────────────

interface DayCell {
  entry: TimeEntry
  seconds: number
  status: TimeEntry['status']
}

interface TaskRow {
  taskId: string | null
  taskName: string | null
  days: Record<string, DayCell | null> // date string → cell
}

interface ProjectGroup {
  projectId: string
  projectName: string
  projectColor: string | null
  tasks: TaskRow[]
}

function transformEntries(entries: TimeEntry[], weekDays: Date[]): ProjectGroup[] {
  const dayKeys = weekDays.map(toDateStr)
  const grouped: Record<string, Record<string, { task: TaskRow; project: Omit<ProjectGroup, 'tasks'> }>> = {}

  for (const entry of entries) {
    if (!entry.start_time || !entry.duration_seconds) continue
    const day = toDateStr(new Date(entry.start_time))
    if (!dayKeys.includes(day)) continue

    const pKey = entry.project_id
    const tKey = entry.task_id ?? '__no_task__'

    if (!grouped[pKey]) {
      grouped[pKey] = {}
    }
    if (!grouped[pKey][tKey]) {
      grouped[pKey][tKey] = {
        project: {
          projectId: entry.project_id,
          projectName: entry.project_name,
          projectColor: entry.project_color,
        },
        task: {
          taskId: entry.task_id,
          taskName: entry.task_name,
          days: Object.fromEntries(dayKeys.map((k) => [k, null])),
        },
      }
    }
    // Sum durations for multiple entries
    const existing = grouped[pKey][tKey].task.days[day]
    grouped[pKey][tKey].task.days[day] = {
      entry, // keeps the most recent entry for editing
      seconds: (existing?.seconds ?? 0) + entry.duration_seconds,
      status: entry.status === 'running' ? 'running' : (existing?.status === 'running' ? 'running' : entry.status),
    }
  }

  // Properly build result
  return Object.entries(grouped).map(([pId, taskMap]) => {
    const firstTask = Object.values(taskMap)[0]
    return {
      projectId: pId,
      projectName: firstTask.project.projectName,
      projectColor: firstTask.project.projectColor,
      tasks: Object.values(taskMap).map((t) => t.task),
    }
  })
}

// ─── Cell component ───────────────────────────────────────────────────────────

interface CellProps {
  cell: DayCell | null
  onAdd: () => void
  onEdit: (entry: TimeEntry) => void
}

function TimesheetCell({ cell, onAdd, onEdit }: CellProps) {
  if (!cell) {
    return (
      <button
        onClick={onAdd}
        className={cn(
          'group w-full h-10 flex items-center justify-center rounded-lg border border-dashed border-transparent',
          'hover:border-[#F06900]/40 hover:bg-[#FFF0E6]/60 dark:hover:bg-orange-900/10 transition-all',
          'text-muted-foreground/40 hover:text-[#F06900]',
        )}
        aria-label="Add entry"
      >
        <Plus className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
      </button>
    )
  }

  const statusStyles: Record<string, string> = {
    draft: 'bg-muted/60 border-transparent hover:border-border',
    running: 'bg-[#FFF0E6]/80 border-[#F06900]/20 dark:bg-orange-900/15',
    pending: 'bg-[hsl(var(--status-pending-muted))] border-[hsl(var(--status-pending))]/20',
    approved: 'bg-[hsl(var(--status-approved-muted))] border-[hsl(var(--status-approved))]/20',
  }
  const dotStyles: Record<string, string> = {
    pending: 'bg-[hsl(var(--status-pending))]',
    approved: 'bg-[hsl(var(--status-approved))]',
  }

  const isEditable = cell.status === 'draft'

  return (
    <button
      onClick={() => isEditable && onEdit(cell.entry)}
      disabled={!isEditable}
      className={cn(
        'group relative w-full h-10 flex items-center justify-center rounded-lg border text-xs font-mono font-medium transition-all',
        statusStyles[cell.status] ?? statusStyles.draft,
        isEditable && 'cursor-pointer hover:shadow-sm',
        !isEditable && 'cursor-default',
      )}
      title={!isEditable ? 'Entry is locked' : 'Edit entry'}
    >
      {/* Status dot for pending/approved */}
      {dotStyles[cell.status] && (
        <span
          className={cn(
            'absolute top-1 right-1 w-1.5 h-1.5 rounded-full',
            dotStyles[cell.status],
          )}
        />
      )}
      <span>{formatDuration(cell.seconds)}</span>
      {isEditable && (
        <Pencil className="absolute right-1.5 bottom-1 w-2.5 h-2.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
      )}
    </button>
  )
}

// ─── Add / Edit Entry Sheet (simplified inline panel) ─────────────────────────

interface AddEntrySheetProps {
  day: Date
  projectId?: string
  taskId?: string | null
  onClose: () => void
  workspaceId: string
  workspace: any
}

function AddEntrySheet({ day, projectId, taskId, onClose, workspaceId, workspace }: AddEntrySheetProps) {
  const [startStr, setStartStr] = useState('09:00')
  const [endStr, setEndStr] = useState('10:00')
  const [description, setDescription] = useState('')
  const [selProjectId, setSelProjectId] = useState<string>(projectId ?? '')
  const [selTaskId, setSelTaskId] = useState<string>(taskId ?? 'none')
  
  const createEntry = useCreateEntry(workspaceId)
  const { data: projectsData } = useProjects()
  const projects = projectsData?.data ?? []
  
  const { data: tasksData } = useTasks(selProjectId || undefined)
  const tasks = selProjectId ? (tasksData?.data ?? []) : []
  
  const selectedProject = projects.find(p => p.id === selProjectId)

  const rawSeconds = useMemo(() => {
    const [sh, sm] = startStr.split(':').map(Number)
    const [eh, em] = endStr.split(':').map(Number)
    const raw = (eh * 60 + em - (sh * 60 + sm)) * 60
    return Math.max(0, raw)
  }, [startStr, endStr])

  const preview = useMemo(
    () => previewRounding(rawSeconds, workspace),
    [rawSeconds, workspace],
  )

  const handleSave = async () => {
    const [sh, sm] = startStr.split(':').map(Number)
    const [eh, em] = endStr.split(':').map(Number)
    const start = new Date(day)
    start.setHours(sh, sm, 0, 0)
    const end = new Date(day)
    end.setHours(eh, em, 0, 0)

    await createEntry.mutateAsync({
      project_id: selProjectId,
      task_id: selTaskId === 'none' ? undefined : selTaskId,
      description: description.trim() || undefined,
      start_time: start.toISOString(),
      end_time: end.toISOString(),
    })
    onClose()
  }

  return (
    <Sheet open={true} onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" className="w-[400px] sm:w-[540px] flex flex-col p-6 overflow-y-auto">
        <SheetHeader>
          <SheetTitle>
            Add Time Entry
            <span className="block text-sm font-normal text-muted-foreground mt-1">
              {day.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
            </span>
          </SheetTitle>
        </SheetHeader>

        <div className="flex flex-col gap-5 mt-6">
          {/* Project & Task Selection */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Project <span className="text-[#FE6900]">*</span></label>
              <Select value={selProjectId} onValueChange={(val) => { setSelProjectId(val ?? ''); setSelTaskId('none'); }}>
                <SelectTrigger className="w-full focus:ring-[#F06900]">
                  <SelectValue placeholder="Select project...">
                    {selectedProject ? (
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: selectedProject.color ?? '#ccc' }} />
                        {selectedProject.name}
                      </div>
                    ) : 'Select project...'}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {projects.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: p.color ?? '#ccc' }} />
                        {p.name}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Task</label>
              <Select value={selTaskId} onValueChange={(val) => setSelTaskId(val ?? 'none')} disabled={!selProjectId || tasks.length === 0}>
                <SelectTrigger className="w-full focus:ring-[#F06900]">
                  <SelectValue placeholder="No task">
                    {selTaskId !== 'none' && tasks.find(t => t.id === selTaskId) 
                      ? tasks.find(t => t.id === selTaskId)?.name 
                      : 'No task'}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No task</SelectItem>
                  {tasks.map((t) => (
                    <SelectItem key={t.id} value={t.id}>
                      {t.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Start</label>
            <input
              type="time"
              value={startStr}
              onChange={(e) => setStartStr(e.target.value)}
              className="w-full text-sm px-2 py-1.5 rounded-lg border border-input bg-background focus:outline-none focus:ring-1 focus:ring-[#F06900]"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">End</label>
            <input
              type="time"
              value={endStr}
              onChange={(e) => setEndStr(e.target.value)}
              className="w-full text-sm px-2 py-1.5 rounded-lg border border-input bg-background focus:outline-none focus:ring-1 focus:ring-[#F06900]"
            />
          </div>
        </div>

        <div>
          <label className="text-xs text-muted-foreground mb-1 block">
            Description {workspace?.mandatory_description && <span className="text-[#FE6900]">*</span>}
          </label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What did you work on?"
            className="w-full text-sm px-3 py-2 rounded-lg border border-input bg-background focus:outline-none focus:ring-1 focus:ring-[#F06900]"
          />
        </div>

        {/* Live rounding preview */}
        <div className="text-xs bg-muted/50 rounded-lg px-3 py-2 flex items-center justify-between">
          <span className="text-muted-foreground">Duration</span>
          <span className="font-mono font-medium">
            <span className={preview.changed ? 'opacity-50 line-through' : ''}>
              {formatDuration(rawSeconds)}
            </span>
            {preview.isActive && (
              <span className={cn("ml-1.5", preview.changed ? "text-[#FE6900]" : "text-muted-foreground opacity-70")}>
                → {formatDuration(preview.rounded)}
              </span>
            )}
          </span>
        </div>
        </div>

        <div className="flex gap-3 mt-auto pt-6 border-t border-border/50">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 text-sm rounded-lg border border-border hover:bg-muted transition-colors font-medium"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={rawSeconds <= 0 || !selProjectId || createEntry.isPending}
            className="flex-1 py-2.5 text-sm rounded-lg bg-[#FE6900] text-white hover:bg-[#D95E00] disabled:opacity-40 disabled:cursor-not-allowed transition-colors font-medium shadow-sm"
          >
            {createEntry.isPending ? 'Saving…' : 'Save Entry'}
          </button>
        </div>
      </SheetContent>
    </Sheet>
  )
}

// ─── Edit Entry Sheet ─────────────────────────────────────────────────────────

interface EditEntrySheetProps {
  entry: TimeEntry
  onClose: () => void
  workspaceId: string
  workspace: any
}

function EditEntrySheet({ entry, onClose, workspaceId, workspace }: EditEntrySheetProps) {
  const [startStr, setStartStr] = useState(() => toTimeString(new Date(entry.start_time)))
  const [endStr, setEndStr] = useState(() => toTimeString(new Date(entry.end_time || entry.start_time)))
  const [description, setDescription] = useState(entry.description || '')
  const [selProjectId, setSelProjectId] = useState<string>(entry.project_id)
  const [selTaskId, setSelTaskId] = useState<string>(entry.task_id ?? 'none')
  
  const updateEntry = useUpdateEntry(workspaceId)
  const { data: projectsData } = useProjects()
  const projects = projectsData?.data ?? []
  
  const { data: tasksData } = useTasks(selProjectId || undefined)
  const tasks = selProjectId ? (tasksData?.data ?? []) : []
  
  const selectedProject = projects.find(p => p.id === selProjectId)

  const rawSeconds = useMemo(() => {
    const [sh, sm] = startStr.split(':').map(Number)
    const [eh, em] = endStr.split(':').map(Number)
    const raw = (eh * 60 + em - (sh * 60 + sm)) * 60
    return Math.max(0, raw)
  }, [startStr, endStr])

  const preview = useMemo(
    () => previewRounding(rawSeconds, workspace),
    [rawSeconds, workspace],
  )

  const handleSave = async () => {
    const [sh, sm] = startStr.split(':').map(Number)
    const [eh, em] = endStr.split(':').map(Number)
    const start = new Date(entry.start_time)
    start.setHours(sh, sm, 0, 0)
    const end = new Date(entry.start_time)
    end.setHours(eh, em, 0, 0)

    await updateEntry.mutateAsync({
      entryId: entry.id,
      payload: {
        project_id: selProjectId,
        task_id: selTaskId === 'none' ? null : selTaskId,
        description: description.trim() || null,
        start_time: start.toISOString(),
        end_time: end.toISOString(),
      }
    })
    onClose()
  }

  return (
    <Sheet open={true} onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" className="w-[400px] sm:w-[540px] flex flex-col p-6 overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Edit Entry</SheetTitle>
        </SheetHeader>

        <div className="flex flex-col gap-6 mt-8 flex-1">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Project</label>
              <Select value={selProjectId} onValueChange={(val) => { setSelProjectId(val || ''); setSelTaskId('none') }}>
                <SelectTrigger className="w-full focus:ring-[#F06900]">
                  <SelectValue placeholder="Select project...">
                    {selectedProject ? (
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: selectedProject.color ?? '#ccc' }} />
                        {selectedProject.name}
                      </div>
                    ) : 'Select project...'}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {projects.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: p.color ?? '#ccc' }} />
                        {p.name}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Task</label>
              <Select value={selTaskId} onValueChange={(val) => setSelTaskId(val ?? 'none')} disabled={!selProjectId || tasks.length === 0}>
                <SelectTrigger className="w-full focus:ring-[#F06900]">
                  <SelectValue placeholder="No task">
                    {selTaskId !== 'none' && tasks.find(t => t.id === selTaskId) 
                      ? tasks.find(t => t.id === selTaskId)?.name 
                      : 'No task'}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No task</SelectItem>
                  {tasks.map((t) => (
                    <SelectItem key={t.id} value={t.id}>
                      {t.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Start</label>
            <input
              type="time"
              value={startStr}
              onChange={(e) => setStartStr(e.target.value)}
              className="w-full text-sm px-2 py-1.5 rounded-lg border border-input bg-background focus:outline-none focus:ring-1 focus:ring-[#F06900]"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">End</label>
            <input
              type="time"
              value={endStr}
              onChange={(e) => setEndStr(e.target.value)}
              className="w-full text-sm px-2 py-1.5 rounded-lg border border-input bg-background focus:outline-none focus:ring-1 focus:ring-[#F06900]"
            />
          </div>
        </div>

        <div>
          <label className="text-xs text-muted-foreground mb-1 block">
            Description {workspace?.mandatory_description && <span className="text-[#FE6900]">*</span>}
          </label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What did you work on?"
            className="w-full text-sm px-3 py-2 rounded-lg border border-input bg-background focus:outline-none focus:ring-1 focus:ring-[#F06900]"
          />
        </div>

        {/* Live rounding preview */}
        <div className="text-xs bg-muted/50 rounded-lg px-3 py-2 flex items-center justify-between">
          <span className="text-muted-foreground">Duration</span>
          <span className="font-mono font-medium">
            {formatDuration(rawSeconds)}
          </span>
        </div>
        {preview && preview.changed && (
          <div className="text-xs bg-muted/50 rounded-lg px-3 py-2 flex items-center justify-between mt-[-16px]">
            <span className="text-muted-foreground">Rounded ({workspace?.rounding_interval_minutes}m {workspace?.rounding_mode})</span>
            <span className="font-mono font-medium text-[#F06900]">
              {formatDuration(preview.rounded)}
            </span>
          </div>
        )}
        </div>

        <div className="mt-auto pt-6 flex items-center gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2.5 text-sm rounded-lg bg-muted text-foreground hover:bg-muted/80 transition-colors font-medium"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={rawSeconds <= 0 || !selProjectId || updateEntry.isPending}
            className="flex-1 py-2.5 text-sm rounded-lg bg-[#FE6900] text-white hover:bg-[#D95E00] disabled:opacity-40 disabled:cursor-not-allowed transition-colors font-medium shadow-sm"
          >
            {updateEntry.isPending ? 'Saving…' : 'Save Changes'}
          </button>
        </div>
      </SheetContent>
    </Sheet>
  )
}


// ─── Main Page ────────────────────────────────────────────────────────────────

export default function TimesheetPage() {
  const { activeWorkspaceId } = useWorkspaceStore()
  const { data: workspace } = useWorkspace(activeWorkspaceId)

  const [weekStart, setWeekStart] = useState<Date>(() => getMondayOfWeek(new Date()))
  const [addSheet, setAddSheet] = useState<{ day: Date; projectId?: string; taskId?: string | null } | null>(null)
  const [editEntry, setEditEntry] = useState<TimeEntry | null>(null)

  const weekEnd = addDays(weekStart, 6)
  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i))
  const today = new Date()

  const { data: entriesData, isLoading } = useTimeEntries({
    workspace_id: activeWorkspaceId ?? '',
    limit: 200,
    date_from: toDateStr(weekStart),
    date_to: toDateStr(weekEnd),
  })

  const entries = entriesData?.data ?? []

  const groups = useMemo(() => {
    return transformEntries(entries, weekDays)
  }, [entries, weekStart]) // eslint-disable-line react-hooks/exhaustive-deps

  // Day totals
  const dayTotals = useMemo(() => {
    return weekDays.map((day) => {
      const key = toDateStr(day)
      return entries
        .filter((e) => toDateStr(new Date(e.start_time)) === key && e.duration_seconds)
        .reduce((sum, e) => sum + (e.duration_seconds ?? 0), 0)
    })
  }, [entries, weekStart]) // eslint-disable-line react-hooks/exhaustive-deps

  const weekTotal = dayTotals.reduce((a, b) => a + b, 0)

  const submitEntries = useSubmitEntries(activeWorkspaceId ?? '')
  const [showSubmit, setShowSubmit] = useState(false)

  const draftCount = entries.filter((e) => e.status === 'draft').length
  const canSubmit = draftCount > 0

  const goBack = () => setWeekStart((d) => addDays(d, -7))
  const goForward = () => setWeekStart((d) => addDays(d, 7))
  const goToday = () => setWeekStart(getMondayOfWeek(new Date()))

  const weekLabel = `${weekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} – ${weekEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`

  return (
    <div className="space-y-4 max-w-full">
      {/* ── Header bar ── */}
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold tracking-tight flex-shrink-0">Timesheet</h1>

        <div className="flex items-center gap-1 ml-auto">
          <button
            onClick={goBack}
            className="p-1.5 rounded-lg hover:bg-muted transition-colors"
            aria-label="Previous week"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={goToday}
            className="px-2.5 py-1 text-xs rounded-lg hover:bg-muted border border-border transition-colors"
          >
            Today
          </button>
          <button
            onClick={goForward}
            className="p-1.5 rounded-lg hover:bg-muted transition-colors"
            aria-label="Next week"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
          <span className="text-sm text-muted-foreground ml-2 min-w-[180px]">{weekLabel}</span>
        </div>

        {/* Submit Week button */}
        <button
          id="submit-week-button"
          disabled={!canSubmit}
          onClick={() => canSubmit && setShowSubmit(true)}
          title={!canSubmit ? 'No draft entries to submit' : `Submit ${draftCount} draft ${draftCount === 1 ? 'entry' : 'entries'}`}
          className={cn(
            'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
            canSubmit
              ? 'bg-[hsl(var(--status-pending))] text-white hover:opacity-90'
              : 'bg-muted text-muted-foreground cursor-not-allowed opacity-50',
          )}
        >
          <Send className="w-3.5 h-3.5" />
          Submit Week
          {canSubmit && (
            <span className="ml-1 bg-white/20 text-white rounded-full px-1.5 py-0.5 text-[10px] font-bold">
              {draftCount}
            </span>
          )}
        </button>
      </div>

      {/* ── Grid ── */}
      <div className="bg-card border border-border rounded-xl overflow-x-auto">
        <table className="w-full min-w-[700px] text-sm">
          {/* Header row */}
          <thead>
            <tr className="border-b border-border">
              <th className="text-left px-4 py-3 font-medium text-muted-foreground w-48 text-xs uppercase tracking-wider">
                Project / Task
              </th>
              {weekDays.map((day, i) => {
                const isToday = isSameDay(day, today)
                return (
                  <th key={i} className="px-2 py-3 text-center w-[90px]">
                    <div className="flex flex-col items-center gap-0.5">
                      <span className="text-[10px] font-medium text-muted-foreground uppercase">
                        {DAY_LABELS[i]}
                      </span>
                      <span
                        className={cn(
                          'w-6 h-6 flex items-center justify-center rounded-full text-xs font-semibold',
                          isToday
                            ? 'bg-[#F06900] text-white'
                            : 'text-foreground',
                        )}
                      >
                        {day.getDate()}
                      </span>
                    </div>
                  </th>
                )
              })}
              <th className="px-2 py-3 text-center w-20 text-xs uppercase tracking-wider font-medium text-muted-foreground">
                Total
              </th>
            </tr>
          </thead>

          <tbody>
            {isLoading ? (
              // Loading skeleton rows
              [1, 2, 3].map((i) => (
                <tr key={i} className="border-b border-border last:border-0">
                  <td className="px-4 py-3">
                    <div className="h-4 bg-muted rounded animate-pulse w-3/4" />
                  </td>
                  {weekDays.map((_, j) => (
                    <td key={j} className="px-2 py-2">
                      <div className="h-10 bg-muted rounded-lg animate-pulse" />
                    </td>
                  ))}
                  <td className="px-2 py-2">
                    <div className="h-10 bg-muted rounded-lg animate-pulse" />
                  </td>
                </tr>
              ))
            ) : groups.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-4 py-16 text-center text-muted-foreground text-sm">
                  No time tracked this week.{' '}
                  <button
                    onClick={() => setAddSheet({ day: isSameDay(weekStart, today) ? today : weekStart })}
                    className="text-[#F06900] hover:underline"
                  >
                    Add an entry
                  </button>
                </td>
              </tr>
            ) : (
              groups.map((group) => (
                <>
                  {/* Project label row */}
                  <tr key={`${group.projectId}-header`} className="bg-muted/30">
                    <td colSpan={9} className="px-4 py-1.5">
                      <div className="flex items-center gap-2">
                        <span
                          className="inline-block w-2 h-2 rounded-full"
                          style={{ backgroundColor: group.projectColor ?? '#6B7280' }}
                        />
                        <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                          {group.projectName}
                        </span>
                      </div>
                    </td>
                  </tr>

                  {/* Task rows */}
                  {group.tasks.map((task) => {
                    const rowTotal = weekDays.reduce(
                      (sum, day) => sum + (task.days[toDateStr(day)]?.seconds ?? 0),
                      0,
                    )
                    return (
                      <tr
                        key={`${group.projectId}-${task.taskId}`}
                        className="border-b border-border/50 last:border-0 hover:bg-muted/20 transition-colors"
                      >
                        <td className="px-4 py-2 text-xs text-muted-foreground">
                          {task.taskName ?? (
                            <span className="italic opacity-60">No task</span>
                          )}
                        </td>
                        {weekDays.map((day) => (
                          <td key={toDateStr(day)} className="px-2 py-2">
                            <TimesheetCell
                              cell={task.days[toDateStr(day)]}
                              onAdd={() => setAddSheet({ day, projectId: group.projectId, taskId: task.taskId })}
                              onEdit={(entry) => setEditEntry(entry)}
                            />
                          </td>
                        ))}
                        <td className="px-2 py-2">
                          <div className="h-10 flex items-center justify-center font-mono text-xs font-medium text-muted-foreground">
                            {rowTotal > 0 ? formatDuration(rowTotal) : '—'}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </>
              ))
            )}

            {/* Total row */}
            {!isLoading && groups.length > 0 && (
              <tr className="border-t border-border bg-muted/30 font-semibold">
                <td className="px-4 py-2.5 text-xs uppercase tracking-wider text-muted-foreground">
                  Total
                </td>
                {dayTotals.map((seconds, i) => (
                  <td key={i} className="px-2 py-2.5 text-center font-mono text-xs">
                    {seconds > 0 ? (
                      <span className={cn(isSameDay(weekDays[i], today) && 'text-[#F06900] font-bold')}>
                        {formatDuration(seconds)}
                      </span>
                    ) : (
                      <span className="text-muted-foreground/40">—</span>
                    )}
                  </td>
                ))}
                <td className="px-2 py-2.5 text-center font-mono text-xs text-[#F06900] font-bold">
                  {weekTotal > 0 ? formatDuration(weekTotal) : '—'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* ── Add Entry Sheet ── */}
      {addSheet && activeWorkspaceId && (
        <AddEntrySheet
          day={addSheet.day}
          projectId={addSheet.projectId}
          taskId={addSheet.taskId}
          onClose={() => setAddSheet(null)}
          workspaceId={activeWorkspaceId}
          workspace={workspace}
        />
      )}

      {editEntry && activeWorkspaceId && (
        <EditEntrySheet
          entry={editEntry}
          onClose={() => setEditEntry(null)}
          workspaceId={activeWorkspaceId}
          workspace={workspace}
        />
      )}

      {/* ── Submit Week Confirmation Dialog ── */}
      <AlertDialog open={showSubmit} onOpenChange={setShowSubmit}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Submit {draftCount} {draftCount === 1 ? 'entry' : 'entries'} for approval?</AlertDialogTitle>
            <AlertDialogDescription>
              The following entries will be marked as <strong>Pending</strong> and sent for approval.
              You will not be able to edit them until they are reviewed.
              <ul className="mt-2 space-y-1 text-xs text-left max-h-40 overflow-y-auto">
                {entries
                  .filter((e) => e.status === 'draft')
                  .map((e) => (
                    <li key={e.id} className="flex items-center gap-2">
                      <span
                        className="w-2 h-2 rounded-full flex-shrink-0"
                        style={{ backgroundColor: e.project_color ?? '#6B7280' }}
                      />
                      <span className="font-medium">{e.project_name}</span>
                      {e.description && <span className="text-muted-foreground truncate">&mdash; {e.description}</span>}
                      <span className="ml-auto font-mono">{formatDuration(e.duration_seconds ?? 0)}</span>
                    </li>
                  ))}
              </ul>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-[hsl(var(--status-pending))] text-white hover:opacity-90"
              onClick={async () => {
                const draftIds = entries.filter((e) => e.status === 'draft').map((e) => e.id)
                await submitEntries.mutateAsync(draftIds)
                setShowSubmit(false)
              }}
              disabled={submitEntries.isPending}
            >
              {submitEntries.isPending ? 'Submitting…' : `Submit ${draftCount} ${draftCount === 1 ? 'Entry' : 'Entries'}`}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
