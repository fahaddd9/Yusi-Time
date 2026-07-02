"use client"

import { useState, useRef, useCallback } from "react"
import { format, subDays } from "date-fns"
import { 
  FilterBar, 
  useDetailedReport, 
  DetailedReportParams,
  useSavedViews,
  useCreateSavedView,
  useDeleteSavedView
} from "@/features/reports"
import { useWorkspaceStore } from "@/stores/workspace-store"
import { useWorkspaces, useWorkspace, useWorkspaceMembers, useMe } from "@/features/settings/hooks"
import { useProjects, useClients, useTasks } from "@/features/projects/hooks"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { DropdownMenu, DropdownMenuContent, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { Loader2, MoreVertical, Play, Clock, DollarSign, FileSearch, ArrowUp, ArrowDown, ArrowUpDown } from "lucide-react"
import { DuplicateMenuItem } from "@/components/shared/DuplicateMenuItem"
import { useStartTimer } from "@/features/time-entries/hooks"
import { tokenStore } from "@/lib/token-store"

// Format seconds into HH:MM:SS
function formatDuration(seconds: number) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function getStatusBadge(status: string) {
  switch (status) {
    case 'approved':
      return <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400">Approved</span>
    case 'pending':
      return <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-brand-orange/10 text-brand-orange dark:bg-brand-orange/20 dark:text-brand-orange">Pending</span>
    case 'rejected':
      return <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">Rejected</span>
    case 'draft':
    default:
      return <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400">Draft</span>
  }
}

export default function DetailedReportPage() {
  const { activeWorkspaceId } = useWorkspaceStore()
  const { data: workspaces } = useWorkspaces()
  const { data: workspaceDetail } = useWorkspace(activeWorkspaceId)
  const activeWorkspace = workspaces?.find(w => w.id === activeWorkspaceId)
  
  const isViewer = activeWorkspace?.role === 'viewer'
  const isAdminOrManager = activeWorkspace?.role === 'admin' || activeWorkspace?.role === 'manager'
  const isWorkspaceBillable = workspaceDetail?.is_billable ?? false
  const showFinancials = !isViewer && isWorkspaceBillable

  const { data: me } = useMe()
  const currentUserId = me?.id

  const { data: projectsData } = useProjects({})
  const projects = projectsData?.data || []
  const { data: clients = [] } = useClients()
  const { data: members = [] } = useWorkspaceMembers(activeWorkspaceId!)

  const [filters, setFilters] = useState<DetailedReportParams>({
    workspace_id: activeWorkspaceId || "",
    date_from: format(subDays(new Date(), 7), "yyyy-MM-dd"),
    date_to: format(new Date(), "yyyy-MM-dd"),
    limit: 50,
    sort_by: "date",
    sort_order: "desc"
  })

  // Fetch tasks only if a project is selected
  const { data: tasksResponse } = useTasks(filters.project_id)
  const tasks = tasksResponse?.data || []

  if (activeWorkspaceId && filters.workspace_id !== activeWorkspaceId) {
    setFilters(f => ({ ...f, workspace_id: activeWorkspaceId }))
  }

  const handleSort = (column: string) => {
    setFilters(prev => {
      const isSameColumn = prev.sort_by === column
      const newOrder = isSameColumn && prev.sort_order === 'desc' ? 'asc' : 'desc'
      return { ...prev, sort_by: column, sort_order: newOrder, cursor: undefined }
    })
  }

  const renderSortIcon = (column: string) => {
    if (filters.sort_by !== column) return <ArrowUpDown className="w-3 h-3 ml-1 opacity-0 group-hover:opacity-40 transition-opacity" />
    return filters.sort_order === 'asc' ? <ArrowUp className="w-3 h-3 ml-1 text-brand-orange" /> : <ArrowDown className="w-3 h-3 ml-1 text-brand-orange" />
  }

  const { data: reportData, isLoading, isFetching } = useDetailedReport(filters)
  const { data: savedViews = [] } = useSavedViews(activeWorkspaceId!)
  const createView = useCreateSavedView()
  const deleteView = useDeleteSavedView()

  // Pagination observer
  const observer = useRef<IntersectionObserver | null>(null)
  const lastElementRef = useCallback((node: HTMLTableRowElement | null) => {
    if (isLoading || isFetching) return
    if (observer.current) observer.current.disconnect()
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && reportData?.next_cursor) {
        setFilters(f => ({ ...f, cursor: reportData.next_cursor || undefined }))
      }
    })
    if (node) observer.current.observe(node)
  }, [isLoading, isFetching, reportData?.next_cursor])

  const handleExportCsv = async () => {
    if (!activeWorkspaceId) return
    try {
      const url = new URL(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1'}/reports/detailed/export`)
      Object.entries(filters).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== 'all' && k !== 'cursor') url.searchParams.append(k, String(v))
      })
      const token = tokenStore.getAccessToken()
      const res = await fetch(url.toString(), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: 'include'
      })
      if (!res.ok) throw new Error('Export failed')
      const blob = await res.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = `yusi-time-detailed-report-${format(new Date(), 'yyyy-MM-dd')}.csv`
      document.body.appendChild(a)
      a.click()
      a.remove()
    } catch (e) {
      console.error(e)
    }
  }

  const startTimerMutation = useStartTimer(activeWorkspaceId!)
  const handleContinueEntry = (entry: any) => {
    startTimerMutation.mutate({
      project_id: entry.project_id,
      task_id: entry.task_id,
      description: entry.description,
      billable: entry.billable
    })
  }

  return (
    <div className="space-y-6">
      <FilterBar 
        filters={filters as any}
        onChange={(newFilters) => {
          // Reset cursor on filter change
          setFilters({ ...newFilters as DetailedReportParams, cursor: undefined })
        }}
        showBillable={isWorkspaceBillable}
        showMemberFilter={isAdminOrManager}
        showTaskFilter={true}
        projects={projects.map((p: any) => ({ id: p.id, name: p.name }))}
        clients={((clients as any)?.data || []).map((c: any) => ({ id: c.id, name: c.name }))}
        users={((members as any)?.items || []).map((m: any) => ({ id: m.user_id, name: m.full_name }))}
        tasks={tasks.map((t: any) => ({ id: t.id, name: t.name }))}
        savedViews={savedViews.filter(v => v.report_type === 'detailed')}
        onSaveView={async (name, savedFilters) => {
          await createView.mutateAsync({ 
            workspaceId: activeWorkspaceId!, 
            data: { name, report_type: 'detailed', filters: savedFilters } 
          })
        }}
        onSelectView={(view) => setFilters({ ...(view.filters as any), workspace_id: activeWorkspaceId!, cursor: undefined })}
        onDeleteView={(id) => deleteView.mutate({ workspaceId: activeWorkspaceId!, viewId: id })}
        onExportCsv={handleExportCsv}
      />

      {/* Metrics */}
      {!isLoading && reportData?.summary && (
        <div className="flex flex-wrap gap-5">
          <Card className="w-full sm:w-[300px] relative overflow-hidden group shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1 border-neutral-200/60 dark:border-neutral-800 bg-white dark:bg-neutral-900">
            <div className="absolute top-0 left-0 w-1 h-full bg-brand-orange" />
            <div className="absolute -top-2 -right-2 p-4 opacity-5 group-hover:opacity-10 transition-opacity duration-300">
              <Clock className="w-24 h-24 text-brand-orange" />
            </div>
            <div className="p-6 relative z-10">
              <p className="text-sm font-semibold text-neutral-500 uppercase tracking-wider mb-2">Total Hours</p>
              <p className="text-4xl font-bold font-mono text-neutral-900 dark:text-white">
                {reportData.summary.total_hours.toFixed(2)}
              </p>
            </div>
          </Card>
          
          {showFinancials && (
            <Card className="w-full sm:w-[300px] relative overflow-hidden group shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1 border-neutral-200/60 dark:border-neutral-800 bg-white dark:bg-neutral-900">
              <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500" />
              <div className="absolute -top-2 -right-2 p-4 opacity-5 group-hover:opacity-10 transition-opacity duration-300">
                <DollarSign className="w-24 h-24 text-emerald-500" />
              </div>
              <div className="p-6 relative z-10">
                <p className="text-sm font-semibold text-neutral-500 uppercase tracking-wider mb-2">Billable Amount</p>
                <p className="text-4xl font-bold font-mono text-emerald-600 dark:text-emerald-500">
                  ${reportData.summary.total_billable_amount || '0.00'}
                </p>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Table */}
      <Card className="border-neutral-200/50 dark:border-neutral-800/50 shadow-sm overflow-hidden rounded-lg bg-white dark:bg-neutral-950">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent border-neutral-200/50 dark:border-neutral-800/50">
                <TableHead 
                  className="text-[11px] font-semibold tracking-widest text-neutral-400 uppercase py-3 h-10 cursor-pointer hover:text-neutral-700 dark:hover:text-neutral-200 transition-colors group"
                  onClick={() => handleSort('date')}
                >
                  <div className="flex items-center">Date {renderSortIcon('date')}</div>
                </TableHead>
                <TableHead className="text-[11px] font-semibold tracking-widest text-neutral-400 uppercase py-3 h-10">User</TableHead>
                <TableHead 
                  className="text-[11px] font-semibold tracking-widest text-neutral-400 uppercase py-3 h-10 cursor-pointer hover:text-neutral-700 dark:hover:text-neutral-200 transition-colors group"
                  onClick={() => handleSort('project')}
                >
                  <div className="flex items-center">Project / Task {renderSortIcon('project')}</div>
                </TableHead>
                <TableHead className="text-[11px] font-semibold tracking-widest text-neutral-400 uppercase py-3 h-10">Description</TableHead>
                <TableHead className="text-[11px] font-semibold tracking-widest text-neutral-400 uppercase py-3 h-10">Status</TableHead>
                <TableHead 
                  className="text-[11px] font-semibold tracking-widest text-neutral-400 uppercase py-3 h-10 cursor-pointer hover:text-neutral-700 dark:hover:text-neutral-200 transition-colors group"
                  onClick={() => handleSort('duration')}
                >
                  <div className="flex items-center justify-end">Duration {renderSortIcon('duration')}</div>
                </TableHead>
                {showFinancials && (
                  <>
                    <TableHead className="text-right text-[11px] font-semibold tracking-widest text-neutral-400 uppercase py-3 h-10">Rate</TableHead>
                    <TableHead 
                      className="text-[11px] font-semibold tracking-widest text-neutral-400 uppercase py-3 h-10 cursor-pointer hover:text-neutral-700 dark:hover:text-neutral-200 transition-colors group"
                      onClick={() => handleSort('amount')}
                    >
                      <div className="flex items-center justify-end">Amount {renderSortIcon('amount')}</div>
                    </TableHead>
                  </>
                )}
                {/* Viewers cannot create/duplicate entries — hide Actions column entirely */}
                {!isViewer && (
                  <TableHead className="text-center w-16 text-[11px] font-semibold tracking-widest text-neutral-400 uppercase py-3 h-10">Actions</TableHead>
                )}
              </TableRow>
            </TableHeader>
            <TableBody>
              {reportData?.data.map((row, idx) => {
                const isLast = idx === reportData.data.length - 1
                return (
                  <TableRow key={row.id} ref={isLast ? lastElementRef : null} className="hover:bg-neutral-50 dark:hover:bg-neutral-900/50 transition-colors duration-200 border-b border-neutral-100 dark:border-neutral-800/30">
                    <TableCell className="whitespace-nowrap font-medium text-neutral-700 dark:text-neutral-300 py-3 text-sm">{format(new Date(row.start_time), "MMM d, yyyy")}</TableCell>
                    <TableCell className="py-3 text-sm">
                      <div className="flex items-center gap-2">
                         <span className="font-medium text-neutral-700 dark:text-neutral-300">{row.user_name}</span>
                      </div>
                    </TableCell>
                    <TableCell className="py-3 text-sm">
                      <div className="font-medium text-neutral-800 dark:text-neutral-200">{row.project_name || 'No Project'}</div>
                      {row.task_name && <div className="text-[11px] text-neutral-500 mt-0.5">{row.task_name}</div>}
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate py-3 text-neutral-600 dark:text-neutral-400 text-sm">{row.description || '-'}</TableCell>
                    <TableCell className="py-3">{getStatusBadge(row.status)}</TableCell>
                    <TableCell className="text-right font-mono font-medium text-neutral-900 dark:text-neutral-100 py-3 text-sm">
                      {row.duration_seconds ? formatDuration(row.duration_seconds) : '-'}
                    </TableCell>
                    {showFinancials && (
                      <>
                        <TableCell className="text-right font-mono text-neutral-500 dark:text-neutral-400 py-3 text-sm">
                          {row.hourly_rate_cents ? `$${(row.hourly_rate_cents / 100).toFixed(2)}` : '-'}
                        </TableCell>
                        <TableCell className="text-right font-mono font-medium text-neutral-900 dark:text-neutral-100 py-3 text-sm">
                          {row.billable_amount_cents ? `$${(row.billable_amount_cents / 100).toFixed(2)}` : '-'}
                        </TableCell>
                      </>
                    )}
                    {!isViewer && (
                      <TableCell className="text-center py-3">
                        <DropdownMenu>
                          <DropdownMenuTrigger>
                            <Button variant="ghost" size="icon" className="h-7 w-7 text-neutral-400 hover:text-neutral-900 dark:hover:text-white">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <button 
                              className="w-full flex items-center px-2 py-1.5 text-sm hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-sm"
                              onClick={() => handleContinueEntry(row)}
                            >
                              <Play className="w-4 h-4 mr-2" /> Continue
                            </button>
                            {/* DR-31: Only show Duplicate if the entry belongs to the current user, or if Admin/Manager */}
                            {(isAdminOrManager || row.user_id === currentUserId) && (
                              <DuplicateMenuItem 
                                entryId={row.id} 
                                entryStatus={row.status} 
                                workspaceId={activeWorkspaceId!} 
                              />
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    )}
                  </TableRow>
                )
              })}
              {isLoading && (
                <TableRow>
                  <TableCell colSpan={isViewer ? (showFinancials ? 7 : 5) : (showFinancials ? 8 : 6)} className="text-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-neutral-400" />
                  </TableCell>
                </TableRow>
              )}
              {!isLoading && reportData?.data.length === 0 && (
                <TableRow>
                  <TableCell colSpan={isViewer ? (showFinancials ? 7 : 5) : (showFinancials ? 8 : 6)} className="h-[250px] text-center">
                    <div className="flex flex-col items-center justify-center text-muted-foreground">
                      <FileSearch className="w-12 h-12 mb-4 opacity-20" />
                      <p className="text-sm">No detailed entries found for this period.</p>
                    </div>
                  </TableCell>
                </TableRow>
              )}
              {isFetching && !isLoading && (
                <TableRow>
                  <TableCell colSpan={isViewer ? (showFinancials ? 7 : 5) : (showFinancials ? 8 : 6)} className="text-center py-4">
                    <Loader2 className="w-4 h-4 animate-spin mx-auto text-neutral-400" />
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </Card>
    </div>
  )
}
