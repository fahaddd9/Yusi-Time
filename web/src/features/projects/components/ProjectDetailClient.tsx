"use client"

import { useProject, useArchiveProject } from "@/features/projects/hooks"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { ProjectTag } from "@/components/ui/project-tag"
import { StatusBadge } from "@/components/ui/status-badge"
import { ChevronLeft, Edit2, Archive, Lock } from "lucide-react"
import Link from "next/link"
import { TaskTable } from "./TaskTable"

export function ProjectDetailClient({ projectId }: { projectId: string }) {
  const { data: project, isLoading } = useProject(projectId)
  const archiveProject = useArchiveProject()

  if (isLoading) {
    return <div className="p-8 flex justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-orange"></div></div>
  }

  if (!project) {
    return <div className="p-8 text-muted-foreground">Project not found</div>
  }

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
          {project.status !== "archived" && (
            <Button 
              variant="outline" 
              onClick={() => archiveProject.mutate(project.id)}
              disabled={archiveProject.isPending}
            >
              <Archive className="w-4 h-4 mr-2" />
              Archive
            </Button>
          )}
          <Button variant="outline">
            <Edit2 className="w-4 h-4 mr-2" />
            Settings
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-card border border-border p-4 rounded-xl shadow-sm">
          <div className="text-sm text-muted-foreground mb-1">Hours Logged</div>
          <div className="font-medium">{(project.hours_logged || 0).toFixed(2)}h</div>
        </div>
        <div className="bg-card border border-border p-4 rounded-xl shadow-sm">
          <div className="text-sm text-muted-foreground mb-1">Budget Hours</div>
          <div className="font-medium">{project.budget_hours ? `${project.budget_hours}h` : 'No budget'}</div>
        </div>
        <div className="bg-card border border-border p-4 rounded-xl shadow-sm">
          <div className="text-sm text-muted-foreground mb-1">Default Rate</div>
          <div className="font-medium">{project.default_hourly_rate_cents ? `$${(project.default_hourly_rate_cents / 100).toFixed(2)}/h` : 'None'}</div>
        </div>
      </div>

      <Tabs defaultValue="tasks" className="mt-8">
        <TabsList>
          <TabsTrigger value="tasks">Tasks</TabsTrigger>
          <TabsTrigger value="members">Members</TabsTrigger>
        </TabsList>
        <TabsContent value="tasks" className="mt-6">
          <TaskTable projectId={project.id} />
        </TabsContent>
        <TabsContent value="members" className="mt-6">
          <div className="bg-card border border-border p-8 rounded-xl shadow-sm text-center text-muted-foreground">
            Project Members management will be implemented in a future phase.
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
