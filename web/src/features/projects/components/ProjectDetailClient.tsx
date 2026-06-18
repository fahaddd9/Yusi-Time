"use client"

import { useState, useMemo } from "react"
import { useProject, useArchiveProject, useUpdateProject, useDeleteProject } from "@/features/projects/hooks"
import { useTimeEntries } from "@/features/time-entries/hooks"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import { format, parseISO } from "date-fns"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { ProjectTag } from "@/components/ui/project-tag"
import { StatusBadge } from "@/components/ui/status-badge"
import { ChevronLeft, Edit2, Archive, Lock } from "lucide-react"
import Link from "next/link"
import { TaskTable } from "./TaskTable"
import { CreateProjectDialog } from "./CreateProjectDialog"
import { Progress } from "@/components/ui/progress"
import { useWorkspaceStore } from "@/stores/workspace-store"
import { useWorkspaces } from "@/features/settings/hooks"
import { useRouter } from "next/navigation"
import { toast } from "sonner"

export function ProjectDetailClient({ projectId }: { projectId: string }) {
  const { data: project, isLoading } = useProject(projectId)
  const archiveProject = useArchiveProject()
  const updateProject = useUpdateProject()
  const deleteProject = useDeleteProject()
  const router = useRouter()
  const { activeWorkspaceId } = useWorkspaceStore()
  const { data: workspaces } = useWorkspaces()
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)

  const { data: entriesData } = useTimeEntries({
    workspace_id: activeWorkspaceId ?? '',
    project_id: projectId,
    limit: 100
  })

  const chartData = useMemo(() => {
    if (!entriesData?.data || entriesData.data.length === 0) return []
    const daily: Record<string, number> = {}
    entriesData.data.forEach(entry => {
      const date = entry.start_time.split('T')[0]
      daily[date] = (daily[date] || 0) + (entry.duration_seconds || 0)
    })
    
    return Object.entries(daily)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, seconds]) => ({
        date: format(parseISO(date), 'MMM d'),
        hours: Number((seconds / 3600).toFixed(2))
      }))
  }, [entriesData])

  const totalHoursLogged = useMemo(() => {
    if (!entriesData?.data) return 0
    const totalSeconds = entriesData.data.reduce((acc, entry) => acc + (entry.duration_seconds || 0), 0)
    return totalSeconds / 3600
  }, [entriesData])

  if (isLoading) {
    return <div className="p-8 flex justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-orange"></div></div>
  }

  if (!project) {
    return <div className="p-8 text-muted-foreground">Project not found</div>
  }

  const callerRole = workspaces?.find((w) => w.id === activeWorkspaceId)?.role ?? 'viewer'
  const isManagerOrAdmin = callerRole === 'admin' || callerRole === 'manager'
  const isViewer = callerRole === 'viewer'

  const pct = project.budget_hours && project.budget_hours > 0 
    ? (totalHoursLogged / project.budget_hours) * 100 
    : 0;
  
  const safePct = isNaN(pct) ? 0 : pct;
  
  let progressColor = "[&_[data-slot=progress-indicator]]:bg-brand-orange";
  if (safePct >= 100) progressColor = "[&_[data-slot=progress-indicator]]:bg-destructive";
  else if (safePct >= 80) progressColor = "[&_[data-slot=progress-indicator]]:bg-warning";

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/projects" className="hover:text-foreground flex items-center transition-colors">
          <ChevronLeft className="w-4 h-4" />
          Projects
        </Link>
      </div>

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex flex-col">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full shadow-inner" style={{ backgroundColor: project.color || '#FE6900' }} />
            <h1 className="text-2xl font-bold tracking-tight text-foreground">{project.name}</h1>
            <StatusBadge status={project.status as any} />
            {project.visibility === 'private' && (
              <div className="flex items-center text-[11px] font-medium bg-muted px-2 py-0.5 rounded text-muted-foreground">
                <Lock className="w-3 h-3 mr-1" />
                Private
              </div>
            )}
          </div>
          <div className="text-sm text-muted-foreground mt-1 ml-6">
            Client: {project.client_name || "None"}
          </div>
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          {isManagerOrAdmin && project.status === "archived" && (
            <Button 
              variant="outline" 
              onClick={() => updateProject.mutate({ id: project.id, data: { status: "active" } as any })}
              disabled={updateProject.isPending}
            >
              <Archive className="w-4 h-4 mr-2" />
              {updateProject.isPending ? "Unarchiving..." : "Unarchive"}
            </Button>
          )}
          {isManagerOrAdmin && project.status !== "archived" && (
            <Button 
              variant="outline" 
              onClick={() => archiveProject.mutate(project.id)}
              disabled={archiveProject.isPending}
            >
              <Archive className="w-4 h-4 mr-2" />
              Archive
            </Button>
          )}
        </div>
      </div>

      {!isViewer && (
        <div className="bg-card border border-border p-5 rounded-xl shadow-sm space-y-3">
          <div className="flex justify-between items-center text-sm">
            <span className="text-muted-foreground">Budget Progress</span>
            <span className="font-mono font-medium">
              {totalHoursLogged.toFixed(2)}h / {project.budget_hours ? `${project.budget_hours}h` : 'No budget'}
            </span>
          </div>
          {project.budget_hours ? (
            <>
              <Progress className={progressColor} value={Math.min(safePct, 100)} />
              {safePct >= 100 && (
                <div className="text-xs text-destructive font-medium mt-1">
                  Budget exceeded
                </div>
              )}
            </>
          ) : (
            <div className="h-1.5 rounded-full bg-muted w-full" />
          )}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
          <div className="bg-card border border-border p-5 rounded-xl shadow-sm">
            <div className="text-sm text-muted-foreground mb-1">Hours Logged</div>
            <div className="text-xl font-semibold font-mono">{totalHoursLogged.toFixed(2)}h</div>
          </div>
        {!isViewer && (
          <>
            <div className="bg-card border border-border p-4 rounded-xl shadow-sm">
              <div className="text-sm text-muted-foreground mb-1">Budget Hours</div>
              <div className="font-medium">{project.budget_hours ? `${project.budget_hours}h` : 'No budget'}</div>
            </div>
            <div className="bg-card border border-border p-4 rounded-xl shadow-sm">
              <div className="text-sm text-muted-foreground mb-1">Default Rate</div>
              <div className="font-medium">{project.default_hourly_rate_cents ? `$${(project.default_hourly_rate_cents / 100).toFixed(2)}/h` : 'None'}</div>
            </div>
          </>
        )}
      </div>

      <Tabs defaultValue="overview" className="mt-8">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="tasks">Tasks</TabsTrigger>
          {project.visibility === 'private' && (
            <TabsTrigger value="members">Members</TabsTrigger>
          )}
          {isManagerOrAdmin && (
            <TabsTrigger value="settings">Settings</TabsTrigger>
          )}
        </TabsList>
        <TabsContent value="overview" className="mt-6 space-y-6">
          <div className="bg-card border border-border p-6 rounded-xl shadow-sm">
            <h3 className="text-sm font-semibold text-foreground mb-6">Hours Logged</h3>
            {chartData.length > 0 ? (
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                    <XAxis 
                      dataKey="date" 
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                      dy={10}
                    />
                    <YAxis 
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                    />
                    <Tooltip 
                      cursor={{ fill: 'hsl(var(--muted))', opacity: 0.4 }}
                      contentStyle={{ 
                        backgroundColor: 'hsl(var(--card))', 
                        borderColor: 'hsl(var(--border))',
                        borderRadius: '0.5rem',
                        boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                      }}
                      formatter={(value: any) => [`${value}h`, 'Hours']}
                    />
                    <Bar 
                      dataKey="hours" 
                      fill="#FE6900" 
                      radius={[4, 4, 0, 0]} 
                      maxBarSize={50}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[300px] w-full flex items-center justify-center border border-dashed border-border rounded-lg">
                <p className="text-sm text-muted-foreground">No time entries recorded yet.</p>
              </div>
            )}
          </div>
        </TabsContent>
        <TabsContent value="tasks" className="mt-6">
          <TaskTable projectId={project.id} isManagerOrAdmin={isManagerOrAdmin} />
        </TabsContent>
        {project.visibility === 'private' && (
          <TabsContent value="members" className="mt-6">
            <div className="bg-card border border-border p-8 rounded-xl shadow-sm text-center text-muted-foreground">
              Project Members management will be implemented in a future phase.
            </div>
          </TabsContent>
        )}
        {isManagerOrAdmin && (
          <TabsContent value="settings" className="mt-6">
            <div className="space-y-6">
              <div className="bg-card border border-border p-8 rounded-xl shadow-sm flex flex-col items-start text-left">
                <h3 className="text-lg font-semibold text-foreground mb-1">Edit Details</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Update the project's name, client, budget, or billing preferences.
                </p>
                <Button onClick={() => setIsSettingsOpen(true)} className="bg-brand-orange hover:bg-brand-orange-hover text-white">
                  Open Settings
                </Button>
              </div>

              <div className="bg-destructive/5 border border-destructive/20 p-8 rounded-xl shadow-sm flex flex-col items-start text-left">
                <h3 className="text-lg font-semibold text-destructive mb-1">Danger Zone</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Permanently delete this project. This action cannot be undone. You can only delete projects that have no time entries recorded.
                </p>
                <Button 
                  variant="destructive" 
                  disabled={deleteProject.isPending}
                  onClick={() => {
                    if (confirm("Are you sure you want to permanently delete this project?")) {
                      deleteProject.mutate(project.id, {
                        onSuccess: () => {
                          toast.success("Project permanently deleted")
                          router.push('/projects')
                        },
                        onError: (err: any) => {
                          const detail = err.response?.data?.detail
                          const msg = typeof detail === 'string' ? detail : detail?.detail || "Failed to delete project"
                          toast.error(msg)
                        }
                      })
                    }
                  }}
                >
                  {deleteProject.isPending ? "Deleting..." : "Delete Project"}
                </Button>
              </div>
            </div>
          </TabsContent>
        )}
      </Tabs>

      {project && (
        <CreateProjectDialog 
          open={isSettingsOpen} 
          onOpenChange={setIsSettingsOpen} 
          initialData={project} 
        />
      )}
    </div>
  )
}
