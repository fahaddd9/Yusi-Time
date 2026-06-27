"use client"

import { useState } from "react"
import { useTags, useDeleteTag } from "@/features/projects/hooks"
import { useWorkspaceStore } from "@/stores/workspace-store"
import { useWorkspaces } from "@/features/settings/hooks"
import { Button } from "@/components/ui/button"
import { Plus, Edit2, Trash2, ShieldAlert } from "lucide-react"
import { CreateTagDialog } from "./CreateTagDialog"
import { PageHeader } from "@/components/ui/setting-row"

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
      <div className="space-y-12 pb-12">
        <section>
          <PageHeader title="Tags" description="Manage global workspace tags for timesheets and projects." />
          <div className="bg-destructive/10 text-destructive p-12 rounded-2xl border border-destructive/20 flex flex-col items-center">
            <ShieldAlert className="w-12 h-12 mb-4" />
            <h1 className="text-xl font-semibold mb-2">Access Denied</h1>
            <p className="text-sm">You do not have permission to view or manage tags.</p>
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="space-y-12 pb-12">
      <section>
        <PageHeader 
          title="Tags" 
          description="Manage global workspace tags for timesheets and projects."
        >
          <Button onClick={() => setIsCreateOpen(true)} className="bg-brand-orange hover:bg-brand-orange/90 text-white shadow-sm rounded-lg">
            <Plus className="w-4 h-4 mr-2" />
            Add Tag
          </Button>
        </PageHeader>

        <div className="bg-white dark:bg-card border border-border/60 rounded-2xl shadow-sm overflow-hidden">
          {(!tags || tags.length === 0) ? (
            <div className="p-16 text-center text-muted-foreground flex flex-col items-center">
              <p className="text-[13px] mb-6">No tags added yet.</p>
              <Button onClick={() => setIsCreateOpen(true)} className="bg-brand-orange hover:bg-brand-orange/90 text-white shadow-sm rounded-lg">
                <Plus className="w-4 h-4 mr-2" />
                Add Tag
              </Button>
            </div>
          ) : (
            <table className="w-full text-sm text-left">
              <thead className="bg-muted/30 text-muted-foreground text-[13px] font-medium border-b border-border/60">
                <tr>
                  <th className="px-6 py-4 font-medium w-[70%]">Tag Name</th>
                  <th className="px-6 py-4 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {tags.map((tag: any) => (
                  <tr key={tag.id} className="hover:bg-muted/20 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        {tag.color ? (
                          <div className="w-3 h-3 rounded-full shadow-sm ring-1 ring-inset ring-black/10" style={{ backgroundColor: tag.color }} />
                        ) : (
                          <div className="w-3 h-3 rounded-full bg-muted border border-border" />
                        )}
                        <span className="font-medium text-foreground">{tag.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity focus-within:opacity-100">
                        <Button variant="ghost" size="icon-sm" className="h-8 w-8 rounded-lg" onClick={() => setEditingTag(tag)}>
                          <Edit2 className="w-4 h-4 text-muted-foreground" />
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="icon-sm" 
                          className="h-8 w-8 rounded-lg hover:bg-destructive/10 hover:text-destructive"
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
      </section>

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
