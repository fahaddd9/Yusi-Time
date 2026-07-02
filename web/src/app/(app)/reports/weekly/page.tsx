"use client"

import { useState } from "react"
import { format, subDays, parseISO, isSameMonth, addDays } from "date-fns"
import { tokenStore } from "@/lib/token-store"
import { 
  FilterBar, 
  useWeeklyReport, 
  WeeklyReportParams,
  useSavedViews,
  useCreateSavedView,
  useDeleteSavedView
} from "@/features/reports"
import { useWorkspaceStore } from "@/stores/workspace-store"
import { useWorkspaces, useWorkspace, useWorkspaceMembers } from "@/features/settings/hooks"
import { useProjects } from "@/features/projects/hooks"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Loader2, Clock, DollarSign, CalendarSearch, ChevronLeft, ChevronRight } from "lucide-react"

interface WeekGroup {
  label: string;
  days: string[];
  isCurrentWeek: boolean;
}

function getWeekGroups(days: string[]): WeekGroup[] {
  if (!days || days.length === 0) return []
  
  const weeks: WeekGroup[] = []
  let currentWeekDays: string[] = []
  
  for (const dayStr of days) {
    const d = parseISO(dayStr)
    // If it's Monday ('1') and we have accumulated days, push the previous week chunk
    if (format(d, 'i') === '1' && currentWeekDays.length > 0) {
      weeks.push({ label: '', days: currentWeekDays, isCurrentWeek: false })
      currentWeekDays = []
    }
    currentWeekDays.push(dayStr)
  }
  if (currentWeekDays.length > 0) {
    weeks.push({ label: '', days: currentWeekDays, isCurrentWeek: false })
  }
  
  const nowStr = format(new Date(), 'yyyy-MM-dd')
  
  return weeks.map(w => {
    const firstDay = parseISO(w.days[0])
    const lastDay = parseISO(w.days[w.days.length - 1])
    
    const sameMonth = isSameMonth(firstDay, lastDay)
    const label = sameMonth 
      ? `${format(firstDay, 'MMM d')} – ${format(lastDay, 'd')}`
      : `${format(firstDay, 'MMM d')} – ${format(lastDay, 'MMM d')}`
      
    return {
      label,
      days: w.days,
      isCurrentWeek: w.days.includes(nowStr)
    }
  })
}

export default function WeeklyReportPage() {
  const { activeWorkspaceId } = useWorkspaceStore()
  const { data: workspaces } = useWorkspaces()
  const { data: workspaceDetail } = useWorkspace(activeWorkspaceId)
  const activeWorkspace = workspaces?.find(w => w.id === activeWorkspaceId)
  
  const isViewer = activeWorkspace?.role === 'viewer'
  const isAdminOrManager = activeWorkspace?.role === 'admin' || activeWorkspace?.role === 'manager'
  const isWorkspaceBillable = workspaceDetail?.is_billable ?? false
  const showFinancials = !isViewer && isWorkspaceBillable

  const { data: projectsData } = useProjects({})
  const projects = projectsData?.data || []
  const { data: members = [] } = useWorkspaceMembers(activeWorkspaceId!)

  const [filters, setFilters] = useState<WeeklyReportParams>({
    workspace_id: activeWorkspaceId || "",
    date_from: format(subDays(new Date(), 6), "yyyy-MM-dd"), // 7 days inclusive
    date_to: format(new Date(), "yyyy-MM-dd"),
  })

  if (activeWorkspaceId && filters.workspace_id !== activeWorkspaceId) {
    setFilters(f => ({ ...f, workspace_id: activeWorkspaceId }))
  }

  const { data: reportData, isLoading } = useWeeklyReport(filters)
  const { data: savedViews = [] } = useSavedViews(activeWorkspaceId!)
  const createView = useCreateSavedView()
  const deleteView = useDeleteSavedView()

  const handleExportCsv = async () => {
    if (!activeWorkspaceId) return
    try {
      const url = new URL(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1'}/reports/weekly/export`)
      Object.entries(filters).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== 'all') url.searchParams.append(k, String(v))
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
      a.download = `weekly-report-${format(new Date(), 'yyyy-MM-dd')}.csv`
      document.body.appendChild(a)
      a.click()
      a.remove()
    } catch (e) {
      console.error(e)
    }
  }

  const handlePrevPeriod = () => {
    const diff = (parseISO(filters.date_to).getTime() - parseISO(filters.date_from).getTime()) / (1000 * 60 * 60 * 24) + 1
    const daysToShift = Math.round(diff)
    setFilters(f => ({
      ...f,
      date_from: format(subDays(parseISO(f.date_from), daysToShift), 'yyyy-MM-dd'),
      date_to: format(subDays(parseISO(f.date_to), daysToShift), 'yyyy-MM-dd')
    }))
  }

  const handleNextPeriod = () => {
    const diff = (parseISO(filters.date_to).getTime() - parseISO(filters.date_from).getTime()) / (1000 * 60 * 60 * 24) + 1
    const daysToShift = Math.round(diff)
    setFilters(f => ({
      ...f,
      date_from: format(addDays(parseISO(f.date_from), daysToShift), 'yyyy-MM-dd'),
      date_to: format(addDays(parseISO(f.date_to), daysToShift), 'yyyy-MM-dd')
    }))
  }

  const weeks = getWeekGroups(reportData?.days || [])

  return (
    <div className="space-y-6">
      {/* Note: Weekly report in API Spec v1.1 takes user_id, project_id, billable. NO group_by, NO client_id */}
      <FilterBar 
        filters={filters as any}
        onChange={(newFilters) => setFilters(newFilters as WeeklyReportParams)}
        showBillable={isWorkspaceBillable}
        showMemberFilter={isAdminOrManager}
        projects={projects.map((p: any) => ({ id: p.id, name: p.name }))}
        users={((members as any)?.items || []).map((m: any) => ({ id: m.user_id, name: m.full_name }))}
        savedViews={savedViews.filter(v => v.report_type === 'weekly')}
        onSaveView={async (name, savedFilters) => {
          await createView.mutateAsync({ 
            workspaceId: activeWorkspaceId!, 
            data: { name, report_type: 'weekly', filters: savedFilters } 
          })
        }}
        onSelectView={(view) => setFilters({ ...(view.filters as any), workspace_id: activeWorkspaceId! })}
        onDeleteView={(id) => deleteView.mutate({ workspaceId: activeWorkspaceId!, viewId: id })}
        onExportCsv={handleExportCsv}
      />

      {/* Metrics */}
      {!isLoading && reportData?.totals && (
        <div className="flex flex-wrap gap-5">
          <Card className="w-full sm:w-[300px] relative overflow-hidden group shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1 border-neutral-200/60 dark:border-neutral-800 bg-white dark:bg-neutral-900">
            <div className="absolute top-0 left-0 w-1 h-full bg-brand-orange" />
            <div className="absolute -top-2 -right-2 p-4 opacity-5 group-hover:opacity-10 transition-opacity duration-300">
              <Clock className="w-24 h-24 text-brand-orange" />
            </div>
            <div className="p-6 relative z-10">
              <p className="text-sm font-semibold text-neutral-500 uppercase tracking-wider mb-2">Total Hours</p>
              <p className="text-4xl font-bold font-mono text-neutral-900 dark:text-white">
                {reportData.totals.grand_total_hours.toFixed(2)}
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
                <p className="text-sm font-semibold text-neutral-500 uppercase tracking-wider mb-2">Total Billable</p>
                <p className="text-4xl font-bold font-mono text-emerald-600 dark:text-emerald-500">
                  ${reportData.totals.grand_total_billable_amount || '0.00'}
                </p>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Pagination Controls */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-neutral-800 dark:text-neutral-200">
          Weekly Breakdown
        </h2>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handlePrevPeriod}>
            <ChevronLeft className="w-4 h-4 mr-1" />
            Previous
          </Button>
          <div className="px-3 text-sm font-medium text-neutral-600 dark:text-neutral-400">
            {format(parseISO(filters.date_from), 'MMM d')} - {format(parseISO(filters.date_to), 'MMM d, yyyy')}
          </div>
          <Button variant="outline" size="sm" onClick={handleNextPeriod}>
            Next
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      </div>

      {/* Table */}
      <Card className="border-neutral-200/50 dark:border-neutral-800/50 shadow-sm overflow-hidden rounded-lg bg-white dark:bg-neutral-950">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent border-neutral-200/50 dark:border-neutral-800/50">
                <TableHead className="w-[220px] text-[11px] font-semibold tracking-widest text-neutral-400 uppercase py-3 h-10">Member</TableHead>
                {weeks.map((week, i) => (
                  <TableHead key={i} className={`text-center min-w-[150px] py-3 h-10 ${week.isCurrentWeek ? 'bg-brand-orange/5 dark:bg-brand-orange/10 border-b-2 border-brand-orange/50' : ''}`}>
                    <div className="text-[10px] font-medium text-neutral-400 uppercase tracking-widest leading-none">
                      {week.isCurrentWeek ? 'Current Week' : `Week ${i + 1}`}
                    </div>
                    <div className="font-semibold text-neutral-700 dark:text-neutral-300 text-xs mt-1">{week.label}</div>
                  </TableHead>
                ))}
                <TableHead className="text-right border-l border-neutral-200/50 dark:border-neutral-800/50 font-semibold text-[11px] tracking-widest text-neutral-400 uppercase py-3 h-10">Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-12">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-neutral-400" />
                  </TableCell>
                </TableRow>
              ) : reportData?.rows.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="h-[250px] text-center">
                    <div className="flex flex-col items-center justify-center text-muted-foreground">
                      <CalendarSearch className="w-12 h-12 mb-4 opacity-20" />
                      <p className="text-sm">No data found for this period.</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                <>
                  {reportData?.rows.map((row: any) => (
                    <TableRow key={row.user_id} className="hover:bg-neutral-50 dark:hover:bg-neutral-900/50 transition-colors duration-200 border-b border-neutral-100 dark:border-neutral-800/30">
                      <TableCell className="py-3">
                        <div className="flex items-center gap-3">
                          <Avatar className="h-7 w-7 border border-neutral-200 dark:border-neutral-800">
                            <AvatarImage src={row.avatar_url || ''} />
                            <AvatarFallback className="text-[10px] bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 font-medium">{row.user_name.substring(0, 2).toUpperCase()}</AvatarFallback>
                          </Avatar>
                          <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300 truncate max-w-[150px]">{row.user_name}</span>
                        </div>
                      </TableCell>
                      {weeks.map((week, i) => {
                        let weekTotal = 0;
                        let weekBillable = 0;
                        let weekAmount = 0;
                        for (const day of week.days) {
                           const cell = row.days[day]
                           if (cell) {
                              weekTotal += cell.total_hours;
                              weekBillable += cell.billable_hours || 0;
                              weekAmount += parseFloat(cell.billable_amount || "0");
                           }
                        }
                        
                        if (weekTotal === 0) {
                          return <TableCell key={i} className={`text-center text-neutral-300 dark:text-neutral-700 font-mono py-3 text-sm ${week.isCurrentWeek ? 'bg-brand-orange/5 dark:bg-brand-orange/10' : ''}`}>—</TableCell>
                        }
                        
                        return (
                          <TableCell key={i} className={`text-center font-mono py-3 align-middle ${week.isCurrentWeek ? 'bg-brand-orange/5 dark:bg-brand-orange/10' : ''}`}>
                            <div className="flex flex-col gap-1 text-center py-1">
                              <div className="font-semibold font-mono text-neutral-900 dark:text-neutral-100 text-[13px]">{weekTotal.toFixed(2)}h</div>
                              {showFinancials && weekBillable > 0 && (
                                <>
                                  <div className="text-[11px] font-mono text-neutral-500 dark:text-neutral-400 font-medium">{weekBillable.toFixed(2)}h billable</div>
                                  <div className="text-[11px] font-mono text-emerald-600 dark:text-emerald-500 font-medium">${weekAmount.toFixed(2)}</div>
                                </>
                              )}
                            </div>
                          </TableCell>
                        )
                      })}
                      <TableCell className="text-right font-mono border-l border-neutral-200/50 dark:border-neutral-800/50 py-3 align-middle">
                        <div className="flex flex-col gap-1 text-right py-1">
                          <div className="font-semibold font-mono text-neutral-900 dark:text-neutral-100 text-sm">{row.total_hours.toFixed(2)}h</div>
                          {showFinancials && (row.billable_hours || 0) > 0 && (
                            <>
                              <div className="text-[11px] font-mono text-neutral-500 dark:text-neutral-400 font-medium">{(row.billable_hours || 0).toFixed(2)}h billable</div>
                              <div className="text-sm font-mono font-semibold text-emerald-600 dark:text-emerald-500 mt-1">${(parseFloat(row.total_billable_amount || "0")).toFixed(2)}</div>
                            </>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                  
                  {/* Totals Row */}
                  <TableRow className="hover:bg-transparent border-t border-neutral-200/50 dark:border-neutral-800/50 bg-neutral-50/50 dark:bg-neutral-900/30">
                    <TableCell className="font-semibold text-[11px] text-neutral-500 tracking-widest uppercase py-4">Total</TableCell>
                    {weeks.map((week, i) => {
                      let colTotal = 0;
                      let colBillable = 0;
                      let colAmount = 0;
                      for (const day of week.days) {
                         const cell = reportData?.totals.by_day[day]
                         if (cell) {
                            colTotal += cell.total_hours;
                            if (cell.billable_hours) colBillable += cell.billable_hours;
                            if (cell.billable_amount) colAmount += parseFloat(cell.billable_amount);
                         }
                      }
                      
                      if (colTotal === 0) {
                        return <TableCell key={i} className={`text-center font-mono font-medium text-neutral-900 dark:text-neutral-100 py-4 text-sm ${week.isCurrentWeek ? 'bg-brand-orange/5 dark:bg-brand-orange/10' : ''}`}>—</TableCell>
                      }

                      return (
                        <TableCell key={i} className={`text-center font-mono py-4 align-middle ${week.isCurrentWeek ? 'bg-brand-orange/5 dark:bg-brand-orange/10' : ''}`}>
                          <div className="flex flex-col gap-1 text-center py-1">
                            <div className="font-bold text-neutral-900 dark:text-neutral-100 text-[13px]">{colTotal.toFixed(2)}h</div>
                            {showFinancials && colBillable > 0 && (
                              <>
                                <div className="text-[11px] text-neutral-500 dark:text-neutral-400 font-medium">{colBillable.toFixed(2)}h billable</div>
                                <div className="text-[11px] text-emerald-600 dark:text-emerald-500 font-medium">${colAmount.toFixed(2)}</div>
                              </>
                            )}
                          </div>
                        </TableCell>
                      )
                    })}
                    <TableCell className="text-right font-mono border-l border-neutral-200/50 dark:border-neutral-800/50 py-4 align-middle">
                      <div className="flex flex-col gap-1 text-right py-1">
                        <div className="font-bold text-neutral-900 dark:text-white text-base">{reportData?.totals.grand_total_hours.toFixed(2)}h</div>
                        {showFinancials && ((reportData?.totals as any).grand_total_billable_hours || 0) > 0 && (
                          <>
                            <div className="text-[11px] text-neutral-500 dark:text-neutral-400 font-medium">{((reportData?.totals as any).grand_total_billable_hours || 0).toFixed(2)}h billable</div>
                            <div className="text-[12px] text-emerald-600 dark:text-emerald-500 font-medium">${reportData?.totals.grand_total_billable_amount || '0.00'}</div>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                </>
              )}
            </TableBody>
          </Table>
        </div>
      </Card>
    </div>
  )
}
