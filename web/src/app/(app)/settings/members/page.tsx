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
  Link as LinkIcon,
  UserCircle2
} from 'lucide-react'
import { format, parseISO } from 'date-fns'
import { PageHeader } from '@/components/ui/setting-row'

function RoleBadge({ role }: { role: string }) {
  let classes = ''
  switch (role) {
    case 'admin':
      classes = 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-500/10 dark:text-purple-400 dark:border-purple-500/20'
      break
    case 'manager':
      classes = 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/20'
      break
    case 'member':
      classes = 'bg-slate-50 text-slate-700 border-slate-200 dark:bg-slate-500/10 dark:text-slate-400 dark:border-slate-500/20'
      break
    case 'viewer':
      classes = 'bg-transparent text-muted-foreground border-dashed border-border'
      break
    default:
      classes = 'bg-muted text-muted-foreground border-border'
  }

  return (
    <Badge variant="outline" className={cn('text-[11px] px-2 py-0.5 rounded-full capitalize font-medium', classes)}>
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
    <div className="space-y-12 pb-12">
      <section>
        <PageHeader 
          title="Team Members" 
          description="Manage who has access to this workspace and their roles."
        >
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
                <Button className="bg-brand-orange hover:bg-brand-orange/90 text-white shadow-sm rounded-lg">
                  <UserPlus className="w-4 h-4 mr-2" />
                  Invite member
                </Button>
              } />
              <DialogContent className="sm:max-w-md rounded-2xl">
                <DialogHeader>
                  <DialogTitle>Invite new member</DialogTitle>
                </DialogHeader>
                {!createdInvite ? (
                  <div className="py-4 space-y-5">
                    <div className="space-y-2">
                      <Label htmlFor="invite-email" className="text-sm font-medium">Email address</Label>
                      <Input
                        id="invite-email"
                        type="email"
                        value={inviteEmail}
                        onChange={(e) => setInviteEmail(e.target.value)}
                        placeholder="colleague@company.com"
                        className="focus-visible:ring-brand-orange/50"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-sm font-medium">Role</Label>
                      <Select value={inviteRole} onValueChange={(v) => v && setInviteRole(v as any)}>
                        <SelectTrigger className="focus-visible:ring-brand-orange/50">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="admin">Admin</SelectItem>
                          <SelectItem value="manager">Manager</SelectItem>
                          <SelectItem value="member">Member</SelectItem>
                          <SelectItem value="viewer">Viewer</SelectItem>
                        </SelectContent>
                      </Select>
                      <p className="text-[13px] text-muted-foreground pt-1.5 leading-relaxed">
                        {inviteRole === 'admin' && 'Full access to all settings, billing, and workspace management.'}
                        {inviteRole === 'manager' && 'Can manage projects, approve timesheets, and invite members.'}
                        {inviteRole === 'member' && 'Can track time and view their own reports and assigned projects.'}
                        {inviteRole === 'viewer' && 'Read-only access to workspace data.'}
                      </p>
                    </div>
                    <Button
                      onClick={handleCreateInvite}
                      disabled={!inviteEmail || createInviteMutation.isPending}
                      className="w-full bg-brand-orange hover:bg-brand-orange/90 text-white rounded-lg mt-2"
                    >
                      {createInviteMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                      Send invite
                    </Button>
                  </div>
                ) : (
                  <div className="py-4 space-y-4 min-w-0">
                    <div className="flex items-start gap-3 p-4 bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 rounded-xl min-w-0">
                      <Check className="w-5 h-5 text-emerald-600 dark:text-emerald-400 mt-0.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-foreground">Invite created successfully!</p>
                        <p className="text-[13px] text-muted-foreground mt-1">
                          Share this link with <strong>{createdInvite.invite.email}</strong> to join.
                        </p>
                        <div className="flex items-center gap-2 mt-3 min-w-0">
                          <code className="text-xs bg-white dark:bg-black/20 border border-border px-2 py-1.5 rounded-md truncate flex-1 font-mono min-w-0 select-all">
                            {createdInvite.inviteUrl}
                          </code>
                          <Button
                            variant="outline"
                            size="sm"
                            className="flex-shrink-0 h-8"
                            onClick={() => handleCopyLink(createdInvite.inviteUrl)}
                          >
                            {copied ? (
                              <><Check className="w-3.5 h-3.5 mr-1.5 text-emerald-500" />Copied!</>
                            ) : (
                              <><Copy className="w-3.5 h-3.5 mr-1.5" />Copy</>
                            )}
                          </Button>
                        </div>
                        <p className="text-xs text-amber-600 dark:text-amber-400 mt-3 flex items-center gap-1 font-medium">
                          <Clock className="w-3.5 h-3.5" />
                          Link expires on {format(parseISO(createdInvite.invite.expires_at), 'MMM d, yyyy')}
                        </p>
                      </div>
                    </div>
                    <DialogClose render={<Button variant="outline" className="w-full rounded-lg">Done</Button>} />
                  </div>
                )}
              </DialogContent>
            </Dialog>
          )}
        </PageHeader>

        <div className="bg-white dark:bg-card rounded-2xl shadow-sm border border-border/60 overflow-hidden">
          {membersLoading ? (
            <div className="p-6 space-y-4">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full rounded-lg" />)}
            </div>
          ) : (
            <Table>
              <TableHeader className="bg-muted/30">
                <TableRow className="hover:bg-transparent border-b-border/60">
                  <TableHead className="w-[45%] font-medium">Member</TableHead>
                  <TableHead className="font-medium">Role</TableHead>
                  <TableHead className="font-medium">Date joined</TableHead>
                  <TableHead className="w-24 text-right font-medium">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {membersData?.items.map((member) => (
                  <TableRow key={member.user_id} className="border-b-border/40 hover:bg-muted/20 transition-colors">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-muted flex items-center justify-center border border-border/60 text-muted-foreground flex-shrink-0">
                          {/* Fallback to initials if avatar logic existed, else User icon */}
                          <UserCircle2 className="w-5 h-5 opacity-50" />
                        </div>
                        <div className="flex flex-col">
                          <span className="text-sm font-medium text-foreground">{member.full_name}</span>
                          <span className="text-xs text-muted-foreground">{member.email}</span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {isAdmin && member.role !== 'admin' ? (
                        <DropdownMenu>
                          <DropdownMenuTrigger render={
                            <Button variant="ghost" size="sm" className="h-7 px-2 -ml-2 hover:bg-muted font-normal focus-visible:ring-brand-orange/50">
                              <RoleBadge role={member.role} />
                              <ChevronDown className="w-3 h-3 ml-1.5 text-muted-foreground opacity-50" />
                            </Button>
                          } />
                          <DropdownMenuContent align="start" className="rounded-xl">
                            {(['admin', 'manager', 'member', 'viewer'] as const).map((r) => (
                              <DropdownMenuItem
                                key={r}
                                className="capitalize cursor-pointer rounded-lg"
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
                          className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors rounded-lg"
                          onClick={() => {
                            setRemovingUserId(member.user_id)
                            setRemovingUserName(member.full_name)
                          }}
                          aria-label={`Remove ${member.full_name}`}
                        >
                          <UserMinus className="w-4 h-4" />
                        </Button>
                      ) : (
                        <span className="text-xs text-muted-foreground opacity-30 px-2">—</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {(!membersData?.items || membersData.items.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={4} className="h-32 text-center text-muted-foreground text-sm">
                      No members found.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </div>
      </section>

      {/* SECTION 2: Pending Invites */}
      {isAdmin && invitesData && invitesData.items.length > 0 && (
        <section>
          <PageHeader 
            title="Pending Invites" 
            description="Invitations that have not been accepted yet." 
          />
          <div className="bg-white dark:bg-card rounded-2xl shadow-sm border border-border/60 overflow-hidden">
            <Table>
              <TableHeader className="bg-muted/30">
                <TableRow className="hover:bg-transparent border-b-border/60">
                  <TableHead className="w-[45%] font-medium">Email address</TableHead>
                  <TableHead className="font-medium">Role</TableHead>
                  <TableHead className="font-medium">Expires</TableHead>
                  <TableHead className="w-24 text-right font-medium">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invitesData.items.map((invite) => (
                  <TableRow key={invite.id} className="border-b-border/40 hover:bg-muted/20 transition-colors">
                    <TableCell className="text-sm font-medium text-foreground">
                      {invite.email}
                    </TableCell>
                    <TableCell>
                      <RoleBadge role={invite.role} />
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-1">
                        <span className="text-sm text-muted-foreground tabular-nums">
                          {format(parseISO(invite.expires_at), 'MMM d, yyyy')}
                        </span>
                        {new Date(invite.expires_at) < new Date(Date.now() + 2 * 24 * 60 * 60 * 1000) && (
                          <span className="text-[10px] text-amber-700 bg-amber-50 dark:bg-amber-500/10 dark:text-amber-400 border border-amber-200 dark:border-amber-500/20 rounded-full px-2 py-0.5 w-fit font-medium">
                            Expiring soon
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-foreground rounded-lg"
                          onClick={() => {
                            const inviteUrl = `${window.location.origin}/join/${invite.token}`
                            handleCopyLink(inviteUrl)
                          }}
                          title="Copy invite link"
                        >
                          <LinkIcon className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-destructive hover:text-destructive hover:bg-destructive/10 h-8 px-3 text-xs rounded-lg font-medium"
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
          </div>
        </section>
      )}

      {/* Remove member confirmation */}
      <AlertDialog open={!!removingUserId} onOpenChange={(open) => !open && setRemovingUserId(null)}>
        <AlertDialogContent className="rounded-2xl">
          <AlertDialogHeader>
            <AlertDialogTitle>Remove Team Member</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove <strong>{removingUserName}</strong> from this workspace?
              They will lose access immediately. Time entries logged by this user will remain.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-lg">Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive hover:bg-destructive/90 text-destructive-foreground rounded-lg"
              onClick={handleConfirmRemove}
              disabled={removeMemberMutation.isPending}
            >
              {removeMemberMutation.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              Remove member
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
