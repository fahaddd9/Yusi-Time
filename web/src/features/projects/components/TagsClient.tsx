"use client"

import { useState } from "react"
import { useTags, useDeleteTag } from "@/features/projects/hooks"
import { useWorkspaceStore } from "@/stores/workspace-store"
import { useWorkspaces } from "@/features/settings/hooks"
import { Button } from "@/components/ui/button"
import { Plus, Edit2, Trash2, ShieldAlert } from "lucide-react"
import { CreateTagDialog } from "./CreateTagDialog"

export function TagsClient() {
  const { data: tags, isLoading } = useTags()
  const deleteTag = useDeleteTag()
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [editingTag, setEditingTag] = useState<any>(null)

  const { activeWorkspaceId } = useWorkspaceStore()
  const { data: workspaces } = useWorkspaces()

  if (isLoading) {
    return <div className="p-8 flex justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-orange"></div></div>
  }

  const callerRole = workspaces?.find((w) => w.id === activeWorkspaceId)?.role ?? 'viewer'
  const isManagerOrAdmin = callerRole === 'admin' || callerRole === 'manager'

  if (!isManagerOrAdmin) {
    return (
      <div className="p-8 max-w-4xl mx-auto space-y-6 text-center">
        <div className="bg-destructive/10 text-destructive p-12 rounded-xl border border-destructive/20 flex flex-col items-center">
          <ShieldAlert className="w-12 h-12 mb-4" />
          <h1 className="text-2xl font-bold mb-2">403 Forbidden</h1>
          <p>You do not have permission to view or manage tags.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 max-w-4xl space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Tags</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage global workspace tags for timesheets and projects.</p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)} className="bg-brand-orange hover:bg-brand-orange-hover text-white">
          <Plus className="w-4 h-4 mr-2" />
          Add Tag
        </Button>
      </div>

      <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
        {(!tags || tags.length === 0) ? (
          <div className="p-12 text-center text-muted-foreground">
            No tags added yet.
          </div>
        ) : (
          <table className="w-full text-sm text-left">
            <thead className="bg-muted/50 text-muted-foreground text-xs uppercase">
              <tr>
                <th className="px-6 py-4 font-medium">Tag</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {tags.map((tag: any) => (
                <tr key={tag.id} className="hover:bg-muted/30 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {tag.color && (
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: tag.color }} />
                      )}
                      <span className="font-medium text-foreground">{tag.name}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button variant="ghost" size="icon-sm" className="h-8 w-8" onClick={() => setEditingTag(tag)}>
                        <Edit2 className="w-4 h-4 text-muted-foreground" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="icon-sm" 
                        className="h-8 w-8 hover:bg-destructive/10 hover:text-destructive"
                        onClick={() => {
                          if (confirm("Delete this tag?")) {
                            deleteTag.mutate(tag.id)
                          }
                        }}
                        disabled={deleteTag.isPending}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <CreateTagDialog 
        open={isCreateOpen || !!editingTag} 
        onOpenChange={(open) => {
          setIsCreateOpen(open)
          if (!open) setEditingTag(null)
        }} 
        initialData={editingTag}
      />
    </div>
  )
}
