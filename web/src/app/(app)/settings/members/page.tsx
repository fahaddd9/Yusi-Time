'use client'

import { useState } from 'react'
import { useWorkspaceStore } from '@/stores/workspace-store'
import {
  useWorkspaceMembers,
  useChangeRole,
  useRemoveMember,
  useCreateInvite,
  useInvites,
  useRevokeInvite,
  useWorkspaces
} from '@/features/settings/hooks'
import type { InviteCreateRequest, InviteResponse } from '@/features/settings/api'
import { cn } from '@/lib/utils'

// shadcn UI
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  ChevronDown,
  Copy,
  Check,
  UserMinus,
  Clock,
  Loader2,
  UserPlus,
  Link as LinkIcon
} from 'lucide-react'
import { format, parseISO } from 'date-fns'

function PageHeader({ title }: { title: string }) {
  return (
    <div className="mb-6 flex items-center justify-between">
      <h1 className="text-2xl font-semibold text-foreground">{title}</h1>
    </div>
  )
}

function RoleBadge({ role }: { role: string }) {
  let classes = ''
  switch (role) {
    case 'admin':
      classes = 'bg-primary/10 text-primary border-primary/20'
      break
    case 'manager':
      classes = 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20'
      break
    case 'member':
      classes = 'bg-muted text-muted-foreground border-border'
      break
    case 'viewer':
      classes = 'bg-transparent text-muted-foreground border-dashed border-border'
      break
    default:
      classes = 'bg-muted text-muted-foreground border-border'
  }

  return (
    <Badge variant="outline" className={cn('text-xs capitalize', classes)}>
      {role}
    </Badge>
  )
}

interface CreatedInvite {
  invite: InviteResponse
  inviteUrl: string
}

export default function MembersPage() {
  const { activeWorkspaceId } = useWorkspaceStore()
  const { data: workspaces } = useWorkspaces()

  const callerRole = workspaces?.find((w) => w.id === activeWorkspaceId)?.role ?? 'viewer'
  const isAdmin = callerRole === 'admin'

  const { data: membersData, isLoading: membersLoading } = useWorkspaceMembers(activeWorkspaceId ?? '')
  const { data: invitesData } = useInvites(activeWorkspaceId ?? '')

  const changeRoleMutation = useChangeRole(activeWorkspaceId ?? '')
  const removeMemberMutation = useRemoveMember(activeWorkspaceId ?? '')
  const createInviteMutation = useCreateInvite(activeWorkspaceId ?? '')
  const revokeInviteMutation = useRevokeInvite(activeWorkspaceId ?? '')

  const [removingUserId, setRemovingUserId] = useState<string | null>(null)
  const [removingUserName, setRemovingUserName] = useState('')

  const [isInviteOpen, setIsInviteOpen] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState<'manager' | 'member' | 'viewer' | 'admin'>('member')
  const [createdInvite, setCreatedInvite] = useState<CreatedInvite | null>(null)
  const [copied, setCopied] = useState(false)

  const handleCreateInvite = () => {
    // API only strictly typed to manager/member/viewer in the interface, but Admin can invite Admin
    // Type casting to bypass strict union if necessary, but we assume it's allowed
    const data = { email: inviteEmail, role: inviteRole } as any
    createInviteMutation.mutate(data, {
      onSuccess: (response) => {
        const invite = response.data
        const url = `${window.location.origin}/join/${invite.token}`
        setCreatedInvite({ invite, inviteUrl: url })
        setInviteEmail('')
      },
    })
  }

  const handleCopyLink = (url: string) => {
    navigator.clipboard.writeText(url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleConfirmRemove = () => {
    if (!removingUserId) return
    removeMemberMutation.mutate(removingUserId, {
      onSuccess: () => setRemovingUserId(null),
    })
  }

  if (!activeWorkspaceId) {
    return <div className="p-6"><p className="text-muted-foreground">No workspace selected.</p></div>
  }

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-foreground">Workspace Members</h1>
        {isAdmin && (
          <Dialog open={isInviteOpen} onOpenChange={(open) => {
            setIsInviteOpen(open)
            if (!open) {
              setCreatedInvite(null)
              setInviteEmail('')
              setInviteRole('member')
            }
          }}>
            <DialogTrigger render={
              <Button className="bg-primary hover:bg-primary/90 text-white shadow-[0_0_15px_rgba(254,105,0,0.3)]">
                <UserPlus className="w-4 h-4 mr-2" />
                Invite Member
              </Button>
            } />
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Invite new member</DialogTitle>
              </DialogHeader>
              {!createdInvite ? (
                <div className="py-4 space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="invite-email">Email Address</Label>
                    <Input
                      id="invite-email"
                      type="email"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      placeholder="colleague@company.com"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Role</Label>
                    <Select value={inviteRole} onValueChange={(v) => v && setInviteRole(v as any)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="admin">Admin</SelectItem>
                        <SelectItem value="manager">Manager</SelectItem>
                        <SelectItem value="member">Member</SelectItem>
                        <SelectItem value="viewer">Viewer</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground pt-1">
                      {inviteRole === 'admin' && 'Full access to all settings and billing.'}
                      {inviteRole === 'manager' && 'Can manage projects, approvals, and members.'}
                      {inviteRole === 'member' && 'Can track time and view their own reports.'}
                      {inviteRole === 'viewer' && 'Read-only access to workspace data.'}
                    </p>
                  </div>
                  <Button
                    onClick={handleCreateInvite}
                    disabled={!inviteEmail || createInviteMutation.isPending}
                    className="w-full bg-primary hover:bg-primary/90 text-white"
                  >
                    {createInviteMutation.isPending && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                    Send Invite
                  </Button>
                </div>
              ) : (
                <div className="py-4 space-y-4 min-w-0">
                  <div className="flex items-start gap-3 p-3 bg-success/10 border border-success/20 rounded-lg min-w-0">
                    <Check className="w-4 h-4 text-success mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground">Invite created!</p>
                      <p className="text-xs text-muted-foreground">
                        Share this link with <strong>{createdInvite.invite.email}</strong>.
                      </p>
                      <div className="flex items-center gap-2 mt-2 min-w-0">
                        <code className="text-xs bg-muted px-2 py-1 rounded truncate flex-1 font-mono min-w-0">
                          {createdInvite.inviteUrl}
                        </code>
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-shrink-0"
                          onClick={() => handleCopyLink(createdInvite.inviteUrl)}
                        >
                          {copied ? (
                            <><Check className="w-3.5 h-3.5 mr-1.5 text-success" />Copied!</>
                          ) : (
                            <><Copy className="w-3.5 h-3.5 mr-1.5" />Copy</>
                          )}
                        </Button>
                      </div>
                      <p className="text-xs text-warning mt-2 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        Expires on {format(parseISO(createdInvite.invite.expires_at), 'MMM d, yyyy')}
                      </p>
                    </div>
                  </div>
                  <DialogClose render={<Button variant="outline" className="w-full">Done</Button>} />
                </div>
              )}
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* SECTION 1: Active Members */}
      <Card className="mb-6">
        <CardHeader className="pb-0 border-b border-border/50">
          <CardTitle className="text-title pb-4">Active Members</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {membersLoading ? (
            <div className="p-6 space-y-4">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="w-[40%]">User</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Joined</TableHead>
                  <TableHead className="w-24 text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {membersData?.items.map((member) => (
                  <TableRow key={member.user_id}>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="text-sm font-medium text-foreground">{member.full_name}</span>
                        <span className="text-xs text-muted-foreground">{member.email}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {isAdmin && member.role !== 'admin' ? (
                        <DropdownMenu>
                          <DropdownMenuTrigger render={
                            <Button variant="ghost" size="sm" className="h-8 px-2 -ml-2 hover:bg-surface-raised font-normal">
                              <RoleBadge role={member.role} />
                              <ChevronDown className="w-3 h-3 ml-1 text-muted-foreground" />
                            </Button>
                          } />
                          <DropdownMenuContent align="start">
                            {(['admin', 'manager', 'member', 'viewer'] as const).map((r) => (
                              <DropdownMenuItem
                                key={r}
                                className="capitalize cursor-pointer"
                                onClick={() => changeRoleMutation.mutate({ userId: member.user_id, newRole: r })}
                              >
                                {r}
                              </DropdownMenuItem>
                            ))}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      ) : (
                        <RoleBadge role={member.role} />
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground tabular-nums">
                      {format(parseISO(member.joined_at), 'MMM d, yyyy')}
                    </TableCell>
                    <TableCell className="text-right">
                      {isAdmin && member.role !== 'admin' ? (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                          onClick={() => {
                            setRemovingUserId(member.user_id)
                            setRemovingUserName(member.full_name)
                          }}
                          aria-label={`Remove ${member.full_name}`}
                        >
                          <UserMinus className="w-4 h-4" />
                        </Button>
                      ) : (
                        <span className="text-xs text-muted-foreground opacity-50 px-2">—</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {(!membersData?.items || membersData.items.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={4} className="h-24 text-center text-muted-foreground">
                      No members found.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* SECTION 2: Pending Invites */}
      {isAdmin && invitesData && invitesData.items.length > 0 && (
        <Card>
          <CardHeader className="pb-0 border-b border-border/50">
            <CardTitle className="text-title pb-4">Pending Invites</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="w-[40%]">Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Expires</TableHead>
                  <TableHead className="w-24 text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invitesData.items.map((invite) => (
                  <TableRow key={invite.id}>
                    <TableCell className="text-sm font-medium text-foreground">
                      {invite.email}
                    </TableCell>
                    <TableCell>
                      <RoleBadge role={invite.role} />
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-0.5">
                        <span className="text-sm text-muted-foreground tabular-nums">
                          {format(parseISO(invite.expires_at), 'MMM d, yyyy')}
                        </span>
                        {new Date(invite.expires_at) < new Date(Date.now() + 2 * 24 * 60 * 60 * 1000) && (
                          <span className="text-[10px] text-warning bg-warning-muted rounded px-1.5 py-0.5 w-fit font-medium">
                            Expiring soon
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-foreground"
                          onClick={() => {
                            const inviteUrl = `${window.location.origin}/join/${invite.token}`
                            handleCopyLink(inviteUrl)
                          }}
                          aria-label="Copy invite link"
                        >
                          <LinkIcon className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-destructive hover:text-destructive hover:bg-destructive/10 h-8 px-3 text-xs"
                          onClick={() => revokeInviteMutation.mutate(invite.token)}
                          disabled={revokeInviteMutation.isPending}
                        >
                          Revoke
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Remove member confirmation */}
      <AlertDialog open={!!removingUserId} onOpenChange={(open) => !open && setRemovingUserId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove Member</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove <strong>{removingUserName}</strong> from this workspace?
              They will lose access immediately.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive hover:bg-destructive/90 text-destructive-foreground"
              onClick={handleConfirmRemove}
              disabled={removeMemberMutation.isPending}
            >
              {removeMemberMutation.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              Remove
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
