"use client"

import { useState } from "react"
import { useProjects } from "@/features/projects/hooks"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import { CreateProjectDialog } from "@/features/projects/components/CreateProjectDialog"
import { ProjectList } from "@/features/projects/components/ProjectList"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

export default function ProjectsPage() {
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [editingProject, setEditingProject] = useState<any>(null)
  const [statusFilter, setStatusFilter] = useState<string>("active")
  
  const { data: projectsData, isLoading } = useProjects({ 
    status: statusFilter
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Projects</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Manage your workspace projects and their budgets.
          </p>
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Select value={statusFilter} onValueChange={(val) => setStatusFilter(val || "all")}>
            <SelectTrigger className="w-[140px] bg-background">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="archived">Archived</SelectItem>
            </SelectContent>
          </Select>

          <Button onClick={() => setIsCreateOpen(true)} className="bg-brand-orange hover:bg-brand-orange-hover text-white shadow-sm">
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </div>
      </div>

      <ProjectList 
        projects={projectsData?.data || []} 
        isLoading={isLoading} 
        onEdit={(p) => setEditingProject(p)}
      />

      <CreateProjectDialog 
        open={isCreateOpen || !!editingProject} 
        onOpenChange={(val) => {
          setIsCreateOpen(val)
          if (!val) setEditingProject(null)
        }} 
        initialData={editingProject}
      />
    </div>
  )
}
