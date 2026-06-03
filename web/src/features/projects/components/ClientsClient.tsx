"use client"

import { useState } from "react"
import { useClients, useDeleteClient } from "@/features/projects/hooks"
import { Button } from "@/components/ui/button"
import { Plus, Edit2, Trash2 } from "lucide-react"
import { CreateClientDialog } from "./CreateClientDialog"

export function ClientsClient() {
  const { data: clientsRes, isLoading } = useClients()
  const deleteClient = useDeleteClient()
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [editingClient, setEditingClient] = useState<any>(null)

  const clients = clientsRes?.data || []

  if (isLoading) {
    return <div className="p-8 flex justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-orange"></div></div>
  }

  return (
    <div className="p-8 max-w-4xl space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Clients</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage your workspace clients and their default rates.</p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)} className="bg-brand-orange hover:bg-brand-orange-hover text-white">
          <Plus className="w-4 h-4 mr-2" />
          Add Client
        </Button>
      </div>

      <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
        {clients.length === 0 ? (
          <div className="p-12 text-center text-muted-foreground">
            No clients added yet.
          </div>
        ) : (
          <table className="w-full text-sm text-left">
            <thead className="bg-muted/50 text-muted-foreground text-xs uppercase">
              <tr>
                <th className="px-6 py-4 font-medium">Name</th>
                <th className="px-6 py-4 font-medium">Contact</th>
                <th className="px-6 py-4 font-medium text-right">Default Rate</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {clients.map((client) => (
                <tr key={client.id} className="hover:bg-muted/30 transition-colors group">
                  <td className="px-6 py-4 font-medium text-foreground">{client.name}</td>
                  <td className="px-6 py-4 text-muted-foreground">
                    <div>{client.email || '-'}</div>
                    {client.phone && <div className="text-xs">{client.phone}</div>}
                  </td>
                  <td className="px-6 py-4 text-right text-muted-foreground">
                    {client.hourly_rate_cents ? `$${(client.hourly_rate_cents / 100).toFixed(2)}/h` : '-'}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button variant="ghost" size="icon-sm" className="h-8 w-8" onClick={() => setEditingClient(client)}>
                        <Edit2 className="w-4 h-4 text-muted-foreground" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="icon-sm" 
                        className="h-8 w-8 hover:bg-destructive/10 hover:text-destructive"
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
              ))}
            </tbody>
          </table>
        )}
      </div>

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
