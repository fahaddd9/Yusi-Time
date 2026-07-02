"use client"

import { useState, useMemo } from "react"
import { format, subDays, startOfMonth, subMonths, startOfYear } from "date-fns"
import { tokenStore } from "@/lib/token-store"
import { 
  FilterBar, 
  useSummaryReport, 
  SummaryReportParams,
  useSavedViews,
  useCreateSavedView,
  useDeleteSavedView,
  reportsApi
} from "@/features/reports"
import { useWorkspaceStore } from "@/stores/workspace-store"
import { useWorkspaces, useWorkspace, useWorkspaceMembers } from "@/features/settings/hooks"
import { useProjects, useClients } from "@/features/projects/hooks"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, Cell } from "recharts"
import { Loader2, Clock, DollarSign, Target, FileText, ArrowUpRight } from "lucide-react"

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white/80 dark:bg-neutral-950/80 backdrop-blur-xl border border-neutral-200/50 dark:border-neutral-800/50 p-4 rounded-xl shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        <p className="font-semibold text-neutral-900 dark:text-white mb-3 text-sm">{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center justify-between gap-6 text-sm mb-2 last:mb-0">
            <div className="flex items-center gap-2">
              <div 
                className="w-2.5 h-2.5 rounded-full shadow-sm" 
                style={{ 
                  background: entry.dataKey === 'nonBillable' ? 'hsl(var(--border-strong))' : (entry.payload.color || 'hsl(var(--primary))')
                }} 
              />
              <span className="text-neutral-600 dark:text-neutral-400 font-medium">{entry.name}</span>
            </div>
            <span className="font-mono font-bold text-neutral-900 dark:text-white">
              {Number(entry.value).toFixed(2)}<span className="text-neutral-400 text-xs ml-0.5">h</span>
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};
import { Skeleton } from "@/components/ui/skeleton"
import { AlertCircle } from "lucide-react"

export default function SummaryReportPage() {
  const { activeWorkspaceId } = useWorkspaceStore()
  const { data: workspaces } = useWorkspaces()
  const { data: workspaceDetail } = useWorkspace(activeWorkspaceId)
  const activeWorkspace = workspaces?.find(w => w.id === activeWorkspaceId)
  
  const isViewer = activeWorkspace?.role === 'viewer'
  const isAdminOrManager = activeWorkspace?.role === 'admin' || activeWorkspace?.role === 'manager'
  const isWorkspaceBillable = workspaceDetail?.is_billable ?? false
  const showFinancials = !isViewer && isWorkspaceBillable

  // Data for filters
  const { data: projectsData } = useProjects({})
  const projects = projectsData?.data || []
  const { data: clients = [] } = useClients()
  const { data: members = [] } = useWorkspaceMembers(activeWorkspaceId!)

  const [filters, setFilters] = useState<SummaryReportParams>({
    workspace_id: activeWorkspaceId || "",
    group_by: "project",
    date_from: format(subDays(new Date(), 7), "yyyy-MM-dd"), // default This Week roughly
    date_to: format(new Date(), "yyyy-MM-dd"),
  })

  // Ensure workspace_id is set when activeWorkspaceId loads
  if (activeWorkspaceId && filters.workspace_id !== activeWorkspaceId) {
    setFilters(f => ({ ...f, workspace_id: activeWorkspaceId }))
  }

  const { data: reportData, isLoading, isError } = useSummaryReport(filters)
  const { data: savedViews = [] } = useSavedViews(activeWorkspaceId!)
  const createView = useCreateSavedView()
  const deleteView = useDeleteSavedView()

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!reportData?.data) return []
    const COLORS = [
      'hsl(var(--primary))', 
      'hsl(var(--success))', 
      'hsl(var(--warning))', 
      'hsl(var(--destructive))', 
      'hsl(var(--secondary-foreground))'
    ];
    return reportData.data.map((row, index) => {
      let barColor = COLORS[index % COLORS.length];
      if (filters.group_by === 'project' && row.group_key) {
        const project = projects.find(p => p.id === row.group_key);
        if (project && project.color) {
          barColor = project.color;
        }
      }
      return {
        name: row.group_label || 'Uncategorized',
        hours: row.total_hours,
        billable: row.billable_hours || 0,
        nonBillable: row.non_billable_hours,
        color: barColor
      };
    })
  }, [reportData, filters.group_by, projects])

  const handleExportCsv = async () => {
    if (!activeWorkspaceId) return
    try {
      // Instead of relying on a blob URL pattern via apiClient generic get,
      // it's often easier to just trigger a download directly or fetch blob.
      const url = new URL(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1'}/reports/summary/export`)
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
      a.download = `summary-report-${format(new Date(), 'yyyy-MM-dd')}.csv`
      document.body.appendChild(a)
      a.click()
      a.remove()
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className="space-y-6">
      <FilterBar 
        filters={filters}
        onChange={(newFilters) => setFilters(newFilters as SummaryReportParams)}
        showGroupBy
        showBillable={isWorkspaceBillable}
        showMemberFilter={isAdminOrManager}
        projects={projects.map((p: any) => ({ id: p.id, name: p.name }))}
        clients={((clients as any)?.data || []).map((c: any) => ({ id: c.id, name: c.name }))}
        users={((members as any)?.items || []).map((m: any) => ({ id: m.user_id, name: m.full_name }))}
        savedViews={savedViews.filter(v => v.report_type === 'summary')}
        onSaveView={async (name, savedFilters) => {
          await createView.mutateAsync({ 
            workspaceId: activeWorkspaceId!, 
            data: { name, report_type: 'summary', filters: savedFilters } 
          })
        }}
        onSelectView={(view) => setFilters({ ...(view.filters as any), workspace_id: activeWorkspaceId! })}
        onDeleteView={(id) => deleteView.mutate({ workspaceId: activeWorkspaceId!, viewId: id })}
        onExportCsv={handleExportCsv}
      />

      {isError ? (
        <div className="flex flex-col items-center justify-center p-12 bg-red-50/50 dark:bg-red-950/20 rounded-2xl border border-red-100 dark:border-red-900/30">
          <AlertCircle className="w-10 h-10 text-red-500 mb-4" />
          <h3 className="text-lg font-semibold text-red-700 dark:text-red-400">Failed to load report</h3>
          <p className="text-red-600/80 dark:text-red-500/80 mt-1">There was an error fetching the summary data.</p>
        </div>
      ) : isLoading ? (
        <div className="space-y-8 animate-in fade-in duration-500">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {[...Array(showFinancials ? 4 : 2)].map((_, i) => (
              <Skeleton key={i} className="h-32 w-full rounded-2xl bg-neutral-100 dark:bg-neutral-800/50" />
            ))}
          </div>
          <Skeleton className="h-[250px] w-full rounded-2xl bg-neutral-100 dark:bg-neutral-800/50" />
          <Skeleton className="h-[300px] w-full rounded-2xl bg-neutral-100 dark:bg-neutral-800/50" />
        </div>
      ) : (
        <>
          <div className="flex flex-wrap gap-5 mb-8">
            <Card className="w-full sm:w-[300px] relative overflow-hidden group shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1 border-neutral-200/60 dark:border-neutral-800 bg-white dark:bg-neutral-900">
              <div className="absolute top-0 left-0 w-1 h-full bg-brand-orange" />
              <div className="absolute -top-2 -right-2 p-4 opacity-5 group-hover:opacity-10 transition-opacity duration-300">
                <Clock className="w-24 h-24 text-brand-orange" />
              </div>
              <div className="p-6 relative z-10">
                <p className="text-sm font-semibold text-neutral-500 uppercase tracking-wider mb-2">Total Hours</p>
                <p className="text-4xl font-bold font-mono text-neutral-900 dark:text-white">
                  {reportData?.summary.total_hours.toFixed(2)}h
                </p>
              </div>
            </Card>
            
            {showFinancials && (
              <>
                <Card className="w-full sm:w-[300px] relative overflow-hidden group shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1 border-neutral-200/60 dark:border-neutral-800 bg-white dark:bg-neutral-900">
                  <div className="absolute top-0 left-0 w-1 h-full bg-brand-orange" />
                  <div className="absolute -top-2 -right-2 p-4 opacity-5 group-hover:opacity-10 transition-opacity duration-300">
                    <Target className="w-24 h-24 text-brand-orange" />
                  </div>
                  <div className="p-6 relative z-10">
                    <p className="text-sm font-semibold text-neutral-500 uppercase tracking-wider mb-2">Billable Hours</p>
                    <p className="text-4xl font-bold font-mono text-brand-orange">
                      {reportData?.data.reduce((acc, row) => acc + (row.billable_hours || 0), 0).toFixed(2)}h
                    </p>
                  </div>
                </Card>

                <Card className="w-full sm:w-[300px] relative overflow-hidden group shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1 border-neutral-200/60 dark:border-neutral-800 bg-white dark:bg-neutral-900">
                  <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500" />
                  <div className="absolute -top-2 -right-2 p-4 opacity-5 group-hover:opacity-10 transition-opacity duration-300">
                    <DollarSign className="w-24 h-24 text-emerald-500" />
                  </div>
                  <div className="p-6 relative z-10">
                    <p className="text-sm font-semibold text-neutral-500 uppercase tracking-wider mb-2">Billable Amount</p>
                    <p className="text-4xl font-bold font-mono text-emerald-600 dark:text-emerald-500">
                      ${reportData?.summary.total_billable_amount || '0.00'}
                    </p>
                  </div>
                </Card>
              </>
            )}

            <Card className="w-full sm:w-[300px] relative overflow-hidden group shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1 border-neutral-200/60 dark:border-neutral-800 bg-white dark:bg-neutral-900">
              <div className="absolute top-0 left-0 w-1 h-full bg-neutral-400" />
              <div className="absolute -top-2 -right-2 p-4 opacity-5 group-hover:opacity-10 transition-opacity duration-300">
                <FileText className="w-24 h-24 text-neutral-500" />
              </div>
              <div className="p-6 relative z-10">
                <p className="text-sm font-semibold text-neutral-500 uppercase tracking-wider mb-2">Entry Count</p>
                <p className="text-4xl font-bold font-mono text-neutral-900 dark:text-white">
                  {reportData?.data.reduce((acc, row) => acc + row.entry_count, 0)}
                </p>
              </div>
            </Card>
          </div>

          {/* Chart */}
          {chartData.length > 0 && (
            <Card className="mb-8 border-neutral-200/40 dark:border-neutral-800/40 bg-white/30 dark:bg-neutral-950/30 backdrop-blur-xl shadow-sm rounded-2xl overflow-hidden animate-in fade-in duration-700 delay-500">
              <CardContent className="p-8">
                <div style={{ height: Math.max(200, chartData.length * 50) }} className="w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} layout="vertical" margin={{ top: 0, right: 30, left: 10, bottom: 0 }} barSize={20}>
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e5e5e5" className="dark:stroke-neutral-800" verticalCoordinatesGenerator={(props) => [props.width / 4, props.width / 2, props.width * 3 / 4]} />
                      <XAxis type="number" axisLine={false} tickLine={false} tick={{ fill: '#9ca3af', fontSize: 12, fontWeight: 500 }} />
                      <YAxis dataKey="name" type="category" width={160} axisLine={false} tickLine={false} tick={{ fill: '#6b7280', fontSize: 13, fontWeight: 500 }} />
                      <Tooltip content={<CustomTooltip />} cursor={false} />
                      
                      <Bar 
                        dataKey={showFinancials ? "billable" : "hours"} 
                        name={showFinancials ? "Billable Hours" : "Total Hours"} 
                        stackId="a" 
                        radius={showFinancials ? [4, 0, 0, 4] : [4, 4, 4, 4]} 
                        animationDuration={1500} 
                        animationEasing="ease-out" 
                        activeBar={(props: any) => {
                          const { x, y, width, height, fill } = props;
                          return (
                            <rect 
                              x={x} 
                              y={y - 2} 
                              width={width} 
                              height={height + 2} 
                              fill={fill} 
                              rx={4} 
                              className="drop-shadow-md brightness-110"
                            />
                          );
                        }}
                      >
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                      {showFinancials && (
                        <Bar 
                          dataKey="nonBillable" 
                          name="Non-Billable" 
                          stackId="a" 
                          radius={[0, 4, 4, 0]} 
                          animationDuration={1500} 
                          animationEasing="ease-out"
                          activeBar={(props: any) => {
                            const { x, y, width, height, fill } = props;
                            return (
                              <rect 
                                x={x} 
                                y={y - 2} 
                                width={width} 
                                height={height + 2} 
                                fill={fill} 
                                rx={4} 
                                className="drop-shadow-md brightness-110"
                              />
                            );
                          }}
                        >
                          {chartData.map((entry, index) => (
                            <Cell key={`cell-non-${index}`} fill="hsl(var(--border-strong))" />
                          ))}
                        </Bar>
                      )}
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Table */}
          <Card className="border-neutral-200/40 dark:border-neutral-800/40 shadow-sm overflow-hidden rounded-2xl bg-white/50 dark:bg-neutral-950/50 backdrop-blur-xl animate-in fade-in slide-in-from-bottom-4 duration-700 delay-700">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-neutral-200/50 dark:border-neutral-800/50">
                  <TableHead className="w-[40%] uppercase text-[11px] font-semibold tracking-widest text-neutral-400 py-3 h-10">{filters.group_by || 'Group'}</TableHead>
                  <TableHead className="text-right text-[11px] font-semibold tracking-widest text-neutral-400 uppercase py-3 h-10">TOTAL HOURS</TableHead>
                  {showFinancials && (
                    <>
                      <TableHead className="text-right text-[11px] font-semibold tracking-widest text-neutral-400 uppercase py-3 h-10">BILLABLE HOURS</TableHead>
                      <TableHead className="text-right text-[11px] font-semibold tracking-widest text-neutral-400 uppercase py-3 h-10">TOTAL AMOUNT</TableHead>
                    </>
                  )}
                </TableRow>
              </TableHeader>
              <TableBody>
                {reportData?.data.map((row, idx) => (
                  <TableRow key={row.group_key || idx} className="hover:bg-neutral-50 dark:hover:bg-neutral-900/50 transition-colors duration-200 border-b border-neutral-100 dark:border-neutral-800/30">
                    <TableCell className="font-medium text-neutral-700 dark:text-neutral-300 py-3 text-sm">{row.group_label || 'Uncategorized'}</TableCell>
                    <TableCell className="text-right font-mono font-medium text-neutral-900 dark:text-neutral-100 py-3 text-sm">{row.total_hours.toFixed(2)}h</TableCell>
                    {showFinancials && (
                      <>
                        <TableCell className="text-right font-mono text-neutral-500 dark:text-neutral-400 py-3 text-sm">{row.billable_hours?.toFixed(2)}h</TableCell>
                        <TableCell className="text-right font-mono font-medium text-neutral-900 dark:text-neutral-100 py-3 text-sm">${row.total_billable_amount || '0.00'}</TableCell>
                      </>
                    )}
                  </TableRow>
                ))}
                {reportData && reportData.data.length > 0 && (
                  <TableRow className="hover:bg-transparent border-t-2 border-neutral-200/50 dark:border-neutral-800/50 bg-neutral-50/50 dark:bg-neutral-900/30">
                    <TableCell className="font-semibold text-[11px] text-neutral-500 tracking-widest uppercase py-4">Total</TableCell>
                    <TableCell className="text-right font-mono font-bold text-neutral-900 dark:text-white py-4 text-sm">{reportData.summary.total_hours.toFixed(2)}h</TableCell>
                    {showFinancials && (
                      <>
                        <TableCell className="text-right font-mono font-bold text-neutral-900 dark:text-white py-4 text-sm">
                          {reportData.data.reduce((acc, row) => acc + (row.billable_hours || 0), 0).toFixed(2)}h
                        </TableCell>
                        <TableCell className="text-right font-mono font-bold text-neutral-900 dark:text-white py-4 text-sm">
                          ${reportData.summary.total_billable_amount || '0.00'}
                        </TableCell>
                      </>
                    )}
                  </TableRow>
                )}
                {reportData?.data.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={showFinancials ? 4 : 2} className="h-[200px] text-center">
                      <div className="flex flex-col items-center justify-center text-muted-foreground">
                        <FileText className="w-10 h-10 mb-3 opacity-20" />
                        <p>No data found for this period.</p>
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Card>
        </>
      )}
    </div>
  )
}
