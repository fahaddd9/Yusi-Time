import { Project } from "@/features/projects/types"
import { StatusBadge } from "@/components/ui/status-badge"
import Link from "next/link"
import { Lock, MoreVertical, Archive, Trash, Pencil, FolderOpen } from "lucide-react"
import { Progress } from "@/components/ui/progress"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { useDeleteProject, useArchiveProject } from "@/features/projects/hooks"

interface ProjectListProps {
  projects: Project[]
  isLoading: boolean
  onEdit?: (project: Project) => void
}

export function ProjectList({ projects, isLoading, onEdit }: ProjectListProps) {
  const deleteProject = useDeleteProject()
  const archiveProject = useArchiveProject()

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {[1, 2, 3, 4, 5, 6].map(i => (
          <div key={i} className="bg-card border border-border rounded-xl shadow-sm p-5 h-36 animate-pulse">
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-muted-foreground/20" />
                <div className="h-4 w-24 bg-muted-foreground/20 rounded" />
              </div>
            </div>
            <div className="h-3 w-16 bg-muted-foreground/20 rounded mt-auto" />
            <div className="h-2 w-full bg-muted-foreground/20 rounded mt-4" />
          </div>
        ))}
      </div>
    )
  }

  if (projects.length === 0) {
    return (
      <div className="bg-card border border-border rounded-xl shadow-sm py-16 flex flex-col items-center justify-center text-center">
        <div className="w-11 h-11 rounded-xl bg-brand-orange/8 flex items-center justify-center mb-4">
          <FolderOpen className="w-5 h-5 text-brand-orange" />
        </div>
        <h3 className="text-sm font-semibold text-foreground mb-1">No projects yet</h3>
        <p className="text-xs text-muted-foreground max-w-xs leading-relaxed mb-5">
          Get started by creating a new project. You can assign it to a client later.
        </p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
      {projects.map((project) => {
        const pct = project.budget_hours && project.budget_hours > 0 
          ? (project.hours_logged / project.budget_hours) * 100 
          : 0;
        
        let progressColor = "[&>div]:bg-brand-orange";
        if (pct >= 100) progressColor = "[&>div]:bg-destructive";
        else if (pct >= 80) progressColor = "[&>div]:bg-warning";

        return (
          <Link href={`/projects/${project.id}`} key={project.id} className="block group h-full">
            <div className="bg-card border border-border rounded-xl shadow-sm p-5 hover:border-brand-orange/30 transition-all duration-200 cursor-pointer h-full flex flex-col relative">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: project.color || '#FE6900' }} />
                  <h3 className="font-semibold text-foreground truncate max-w-[200px]">{project.name}</h3>
                </div>
                <div className="flex items-center gap-1" onClick={(e) => e.preventDefault()}>
                  {project.visibility === 'private' && (
                    <div className="flex items-center text-[10px] bg-muted px-1.5 py-0.5 rounded text-muted-foreground mr-1">
                      <Lock className="w-3 h-3 mr-1" />
                      Private
                    </div>
                  )}
                  <DropdownMenu>
                    <DropdownMenuTrigger className="h-8 w-8 inline-flex items-center justify-center rounded-md hover:bg-muted text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity outline-none">
                      <MoreVertical className="w-4 h-4" />
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => {
                        if (onEdit) onEdit(project)
                      }}>
                        <Pencil className="w-4 h-4 mr-2" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => {
                        if (confirm("Archive this project?")) archiveProject.mutate(project.id)
                      }}>
                        <Archive className="w-4 h-4 mr-2" />
                        Archive
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        className="text-destructive focus:text-destructive focus:bg-destructive/10"
                        onClick={() => {
                          if (confirm("Delete this project? This action cannot be undone.")) deleteProject.mutate(project.id)
                        }}
                      >
                        <Trash className="w-4 h-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
              
              <div className="text-sm text-muted-foreground mb-6">
                {project.client_name || "No Client"}
              </div>

              <div className="mt-auto">
                <div className="flex justify-between text-xs text-muted-foreground mb-2">
                  <span>{project.hours_logged.toFixed(2)}h logged</span>
                  {project.budget_hours ? <span>{project.budget_hours.toFixed(2)}h budget</span> : null}
                </div>
                {project.budget_hours ? (
                  <Progress className={progressColor} value={Math.min(pct, 100)} />
                ) : (
                  <div className="h-1.5 rounded-full bg-muted w-full" />
                )}
              </div>
            </div>
          </Link>
        )
      })}
    </div>
  )
}
