"use client"

import { useState } from "react"
import { useClients, useDeleteClient } from "@/features/projects/hooks"
import { useWorkspaceStore } from "@/stores/workspace-store"
import { useWorkspaces } from "@/features/settings/hooks"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Plus, Edit2, Trash2, ShieldAlert, ClipboardList } from "lucide-react"
import { CreateClientDialog } from "./CreateClientDialog"
import { PageHeader } from "@/components/ui/setting-row"

export function ClientsClient() {
  const { data: clientsRes, isLoading } = useClients()
  const deleteClient = useDeleteClient()
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [editingClient, setEditingClient] = useState<any>(null)

  const { activeWorkspaceId } = useWorkspaceStore()
  const { data: workspaces } = useWorkspaces()

  const clients = clientsRes?.data || []

  const callerRole = workspaces?.find((w) => w.id === activeWorkspaceId)?.role ?? 'viewer'
  const isManagerOrAdmin = callerRole === 'admin' || callerRole === 'manager'

  if (!isLoading && !isManagerOrAdmin) {
    return (
      <div className="space-y-12 pb-12">
        <section>
          <PageHeader title="Clients" description="Manage your workspace clients and their default rates." />
          <div className="bg-destructive/10 text-destructive p-12 rounded-2xl border border-destructive/20 flex flex-col items-center">
            <ShieldAlert className="w-12 h-12 mb-4" />
            <h1 className="text-xl font-semibold mb-2">Access Denied</h1>
            <p className="text-sm">You do not have permission to view or manage clients.</p>
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="space-y-12 pb-12">
      <section>
        <PageHeader 
          title="Clients" 
          description="Manage your workspace clients and their default rates."
        >
          <Button onClick={() => setIsCreateOpen(true)} className="bg-brand-orange hover:bg-brand-orange/90 text-white shadow-sm rounded-lg">
            <Plus className="w-4 h-4 mr-2" />
            Add Client
          </Button>
        </PageHeader>

        <div className="bg-white dark:bg-card border border-border/60 rounded-2xl shadow-sm overflow-hidden">
          <table className="w-full text-sm text-left">
            <thead className="bg-muted/30 text-muted-foreground text-[13px] font-medium border-b border-border/60">
              <tr>
                <th className="px-6 py-4 font-medium w-[25%]">Name</th>
                <th className="px-6 py-4 font-medium w-[25%]">Email</th>
                <th className="px-6 py-4 font-medium w-[15%]">Phone</th>
                <th className="px-6 py-4 font-medium w-[15%] text-right">Hourly Rate</th>
                <th className="px-6 py-4 font-medium w-[10%] text-center">Projects</th>
                <th className="px-6 py-4 font-medium w-[10%] text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40">
              {isLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <tr key={`skeleton-${i}`}>
                    <td className="px-6 py-4"><Skeleton className="h-4 w-32 rounded-md" /></td>
                    <td className="px-6 py-4"><Skeleton className="h-4 w-40 rounded-md" /></td>
                    <td className="px-6 py-4"><Skeleton className="h-4 w-24 rounded-md" /></td>
                    <td className="px-6 py-4"><div className="flex justify-end"><Skeleton className="h-4 w-16 rounded-md" /></div></td>
                    <td className="px-6 py-4"><div className="flex justify-center"><Skeleton className="h-4 w-8 rounded-md" /></div></td>
                    <td className="px-6 py-4"><div className="flex justify-end"><Skeleton className="h-8 w-16 rounded-md" /></div></td>
                  </tr>
                ))
              ) : clients.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-16">
                    <div className="flex flex-col items-center justify-center text-center">
                      <div className="bg-muted/30 p-4 rounded-full mb-4 border border-border/60">
                        <ClipboardList className="w-8 h-8 text-muted-foreground" />
                      </div>
                      <h3 className="text-base font-semibold text-foreground mb-1">No clients yet</h3>
                      <p className="text-[13px] text-muted-foreground max-w-sm mb-6">
                        Add a client to assign them to projects and set default billing rates.
                      </p>
                      <Button onClick={() => setIsCreateOpen(true)} className="bg-brand-orange hover:bg-brand-orange/90 text-white shadow-sm rounded-lg">
                        <Plus className="w-4 h-4 mr-2" />
                        Add Client
                      </Button>
                    </div>
                  </td>
                </tr>
              ) : (
                clients.map((client) => (
                  <tr key={client.id} className="hover:bg-muted/20 transition-colors group">
                    <td className="px-6 py-4 font-medium text-foreground">{client.name}</td>
                    <td className="px-6 py-4 text-muted-foreground">{client.email || '—'}</td>
                    <td className="px-6 py-4 text-muted-foreground">{client.phone || '—'}</td>
                    <td className="px-6 py-4 text-right text-muted-foreground">
                      {client.hourly_rate_cents ? `$${(client.hourly_rate_cents / 100).toFixed(2)}` : '—'}
                    </td>
                    <td className="px-6 py-4 text-center text-muted-foreground">
                      {client.project_count || 0}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity focus-within:opacity-100">
                        <Button variant="ghost" size="icon-sm" className="h-8 w-8 rounded-lg" onClick={() => setEditingClient(client)}>
                          <Edit2 className="w-4 h-4 text-muted-foreground" />
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="icon-sm" 
                          className="h-8 w-8 rounded-lg hover:bg-destructive/10 hover:text-destructive"
                          onClick={() => {
                            if (confirm("Delete this client? This will remove the client from all associated projects.")) {
                              deleteClient.mutate(client.id)
                            }
                          }}
                          disabled={deleteClient.isPending}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <CreateClientDialog 
        open={isCreateOpen || !!editingClient} 
        onOpenChange={(open) => {
          setIsCreateOpen(open)
          if (!open) setEditingClient(null)
        }} 
        initialData={editingClient}
      />
    </div>
  )
}
