'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useWorkspaceStore } from '@/stores/workspace-store'
import {
  useWorkspace,
  useUpdateWorkspace,
  useDeleteWorkspace,
  useWorkspaces
} from '@/features/settings/hooks'
import type { WorkspaceUpdate } from '@/features/settings/api'
import { cn } from '@/lib/utils'

// shadcn UI
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
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
import { Loader2 } from 'lucide-react'

function PageHeader({ title }: { title: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-semibold text-foreground">{title}</h1>
    </div>
  )
}

interface SettingRowProps {
  label: string
  description?: React.ReactNode
  children: React.ReactNode
  disabled?: boolean
}

function SettingRow({ label, description, children, disabled = false }: SettingRowProps) {
  return (
    <div className={cn(
      "flex items-start justify-between gap-6 py-4",
      "border-b border-border last:border-b-0"
    )}>
      <div className="flex-1 min-w-0 max-w-sm">
        <p className={cn("text-body font-medium",
          disabled ? "text-muted-foreground" : "text-foreground")}>
          {label}
        </p>
        {description && (
          <p className="text-caption text-muted-foreground mt-0.5 leading-relaxed">
            {description}
          </p>
        )}
      </div>
      <div className="flex-shrink-0 pt-0.5">{children}</div>
    </div>
  )
}

export default function WorkspaceSettingsPage() {
  const router = useRouter()
  const { activeWorkspaceId } = useWorkspaceStore()
  const { data: workspaces } = useWorkspaces()

  // Determine caller's role in this workspace
  const callerRole = workspaces?.find((w) => w.id === activeWorkspaceId)?.role ?? 'viewer'
  const isAdmin = callerRole === 'admin'

  const { data: workspace, isLoading } = useWorkspace(activeWorkspaceId)
  const updateMutation = useUpdateWorkspace(activeWorkspaceId ?? '')
  const deleteMutation = useDeleteWorkspace(activeWorkspaceId ?? '')

  // Form states
  const [name, setName] = useState('')
  const [logoUrl, setLogoUrl] = useState('')
  const [timezone, setTimezone] = useState('UTC')
  const [dateFormat, setDateFormat] = useState('MM/DD/YYYY')
  const [currency, setCurrency] = useState('USD')
  const [defaultHourlyRate, setDefaultHourlyRate] = useState<number | undefined>()

  const [roundingMode, setRoundingMode] = useState('none')
  const [roundingInterval, setRoundingInterval] = useState<number | undefined>()
  const [idleEnabled, setIdleEnabled] = useState(false)
  const [idleTimeout, setIdleTimeout] = useState<number | undefined>()
  const [mandatoryDescription, setMandatoryDescription] = useState(false)
  const [maxTimerDuration, setMaxTimerDuration] = useState<number>(43200) // 12 hours
  const [pastEntryLimit, setPastEntryLimit] = useState<number>(30)

  const [lockPeriod, setLockPeriod] = useState(0)
  const [approvalEnabled, setApprovalEnabled] = useState(false)

  // Dialogs
  const [showApprovalWarning, setShowApprovalWarning] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  useEffect(() => {
    if (workspace) {
      setName(workspace.name)
      setLogoUrl(workspace.logo_url ?? '')
      setTimezone(workspace.default_timezone)
      setDateFormat(workspace.date_format ?? 'MM/DD/YYYY')
      setCurrency(workspace.currency ?? 'USD')
      setDefaultHourlyRate(workspace.default_hourly_rate_cents ? workspace.default_hourly_rate_cents / 100 : undefined)
      
      setRoundingMode(workspace.rounding_mode)
      setRoundingInterval(workspace.rounding_interval_minutes ?? undefined)
      setIdleEnabled(workspace.idle_detection_enabled)
      setIdleTimeout(workspace.idle_timeout_minutes ?? undefined)
      setMandatoryDescription(workspace.mandatory_description)
      setMaxTimerDuration(workspace.max_timer_duration_seconds ?? 43200)
      setPastEntryLimit(workspace.past_entry_limit_days ?? 30)

      setLockPeriod(workspace.lock_period_days)
      setApprovalEnabled(workspace.approval_workflow_enabled)
    }
  }, [workspace])

  const handleSave = () => {
    const payload: WorkspaceUpdate = { 
      name, 
      logo_url: logoUrl,
      default_timezone: timezone,
      date_format: dateFormat,
      currency,
      default_hourly_rate_cents: defaultHourlyRate ? Math.round(defaultHourlyRate * 100) : undefined,
      rounding_mode: roundingMode,
      mandatory_description: mandatoryDescription,
      approval_workflow_enabled: approvalEnabled,
      idle_detection_enabled: idleEnabled,
      max_timer_duration_seconds: maxTimerDuration,
      past_entry_limit_days: pastEntryLimit,
      lock_period_days: lockPeriod
    }
    
    if (roundingMode !== 'none') {
      payload.rounding_interval_minutes = roundingInterval
    }
    if (idleEnabled) {
      payload.idle_timeout_minutes = idleTimeout
    }

    updateMutation.mutate(payload)
  }

  const handleApprovalToggle = (checked: boolean) => {
    if (!checked && workspace?.approval_workflow_enabled) {
      setShowApprovalWarning(true)
    } else {
      setApprovalEnabled(checked)
    }
  }

  const handleDelete = () => {
    deleteMutation.mutate(undefined, {
      onSuccess: () => {
        router.push('/dashboard')
      },
    })
  }

  if (!activeWorkspaceId) {
    return (
      <div className="p-6">
        <p className="text-muted-foreground">No workspace selected.</p>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="p-6 max-w-2xl space-y-6">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-40 w-full rounded-xl" />
        ))}
      </div>
    )
  }

  const isDirty = true // Ideally track this properly, but simplified to always allow save if admin

  return (
    <div className="max-w-2xl">
      <PageHeader title="Workspace Settings" />

      {/* SECTION 1: General */}
      <Card className="mb-4">
        <CardHeader className="pb-0">
          <CardTitle className="text-title">General</CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <SettingRow label="Workspace Name" description="The display name for this workspace." disabled={!isAdmin}>
            {isAdmin ? (
              <Input value={name} onChange={(e) => setName(e.target.value)} className="w-[220px]" />
            ) : (
              <p className="text-body text-foreground">{name}</p>
            )}
          </SettingRow>
          
          <SettingRow label="Logo URL" description="URL of your workspace logo image." disabled={!isAdmin}>
            {isAdmin ? (
              <Input value={logoUrl} onChange={(e) => setLogoUrl(e.target.value)} className="w-[220px]" placeholder="https://" />
            ) : (
              <p className="text-body text-foreground">{logoUrl || 'Not set'}</p>
            )}
          </SettingRow>
          
          <SettingRow label="Timezone" description="Default timezone for time entries." disabled={!isAdmin}>
            {isAdmin ? (
              <Select value={timezone} onValueChange={(v) => v && setTimezone(v)}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="UTC">UTC</SelectItem>
                  <SelectItem value="America/New_York">Eastern Time</SelectItem>
                  <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
                  <SelectItem value="Europe/London">London</SelectItem>
                </SelectContent>
              </Select>
            ) : (
              <p className="text-body text-foreground">{timezone}</p>
            )}
          </SettingRow>
          
          <SettingRow label="Date Format" description="How dates are displayed across the app." disabled={!isAdmin}>
            {isAdmin ? (
              <Select value={dateFormat} onValueChange={(v) => v && setDateFormat(v)}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                  <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                  <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                </SelectContent>
              </Select>
            ) : (
              <p className="text-body text-foreground">{dateFormat}</p>
            )}
          </SettingRow>
          
          <SettingRow label="Currency" description="Currency for billable amounts." disabled={!isAdmin}>
            {isAdmin ? (
              <Select value={currency} onValueChange={(v) => v && setCurrency(v)}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="USD">USD ($)</SelectItem>
                  <SelectItem value="EUR">EUR (€)</SelectItem>
                  <SelectItem value="GBP">GBP (£)</SelectItem>
                </SelectContent>
              </Select>
            ) : (
              <p className="text-body text-foreground">{currency}</p>
            )}
          </SettingRow>
          
          {callerRole !== 'viewer' && (
            <SettingRow label="Default Hourly Rate" description="Workspace-level fallback rate." disabled={!isAdmin}>
              {isAdmin ? (
                <div className="flex items-center gap-1.5">
                  <span className="text-muted-foreground text-body">$</span>
                  <Input 
                    type="number" 
                    value={defaultHourlyRate ?? ''} 
                    onChange={(e) => setDefaultHourlyRate(e.target.value ? Number(e.target.value) : undefined)}
                    className="w-[120px] font-mono tabular-nums" 
                    min={0}
                  />
                </div>
              ) : (
                <p className="text-body text-foreground font-mono tabular-nums">${defaultHourlyRate ?? 0}</p>
              )}
            </SettingRow>
          )}

          {isAdmin && (
            <div className="flex justify-end pt-4 mt-2 border-t border-border">
              <Button onClick={handleSave} disabled={updateMutation.isPending}
                className="bg-primary hover:bg-primary/90 text-white shadow-orange-glow">
                {updateMutation.isPending ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Saving...</> : 'Save Changes'}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* SECTION 2: Time Tracking */}
      <Card className="mb-4">
        <CardHeader className="pb-0">
          <CardTitle className="text-title">Time Tracking</CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <SettingRow label="Rounding Mode" description="How timer durations are rounded when saving." disabled={!isAdmin}>
            {isAdmin ? (
              <Select value={roundingMode} onValueChange={(v) => v && setRoundingMode(v)}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  <SelectItem value="nearest">Nearest</SelectItem>
                  <SelectItem value="up">Round Up</SelectItem>
                  <SelectItem value="down">Round Down</SelectItem>
                </SelectContent>
              </Select>
            ) : (
              <p className="text-body text-foreground capitalize">{roundingMode}</p>
            )}
          </SettingRow>
          
          {roundingMode !== 'none' && (
            <SettingRow label="Rounding Interval" description="Round to the nearest X minutes." disabled={!isAdmin}>
              {isAdmin ? (
                <Select value={roundingInterval?.toString() ?? '15'} onValueChange={(v) => v && setRoundingInterval(Number(v))}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[1, 5, 6, 10, 15, 30].map((v) => (
                      <SelectItem key={v} value={v.toString()}>{v} minutes</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <p className="text-body text-foreground">{roundingInterval} minutes</p>
              )}
            </SettingRow>
          )}

          <SettingRow label="Idle Detection" description="Auto-pause when user has been inactive." disabled={!isAdmin}>
            {isAdmin ? (
              <Switch
                checked={idleEnabled}
                onCheckedChange={setIdleEnabled}
              />
            ) : (
              <p className="text-body text-foreground">{idleEnabled ? 'Enabled' : 'Disabled'}</p>
            )}
          </SettingRow>
          
          {idleEnabled && (
            <SettingRow label="Idle Timeout" description="Minutes before idle is detected." disabled={!isAdmin}>
              {isAdmin ? (
                <Select value={idleTimeout?.toString() ?? '15'} onValueChange={(v) => v && setIdleTimeout(Number(v))}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[1, 2, 5, 10, 15].map((v) => (
                      <SelectItem key={v} value={v.toString()}>{v} minutes</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <p className="text-body text-foreground font-mono tabular-nums">{idleTimeout} min</p>
              )}
            </SettingRow>
          )}

          <SettingRow label="Mandatory Descriptions" description="Require a description on every time entry." disabled={!isAdmin}>
            {isAdmin ? (
              <Switch 
                checked={mandatoryDescription}
                onCheckedChange={setMandatoryDescription}
              />
            ) : (
              <p className="text-body text-foreground">{mandatoryDescription ? 'Yes' : 'No'}</p>
            )}
          </SettingRow>
          
          <SettingRow label="Max Timer Duration" description="Auto-stop timer after this many hours." disabled={!isAdmin}>
            {isAdmin ? (
              <Select value={(maxTimerDuration / 3600).toString()} onValueChange={(v) => v && setMaxTimerDuration(Number(v) * 3600)}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[8, 10, 12, 16, 24].map((v) => (
                    <SelectItem key={v} value={v.toString()}>{v} hours</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <p className="text-body text-foreground font-mono tabular-nums">{maxTimerDuration / 3600} hours</p>
            )}
          </SettingRow>
          
          <SettingRow label="Past Entry Limit" description="How many days back manual entries can be backdated." disabled={!isAdmin}>
            {isAdmin ? (
              <Select value={pastEntryLimit.toString()} onValueChange={(v) => v && setPastEntryLimit(Number(v))}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[7, 14, 30, 90, 365].map((v) => (
                    <SelectItem key={v} value={v.toString()}>{v} days</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <p className="text-body text-foreground font-mono tabular-nums">{pastEntryLimit} days</p>
            )}
          </SettingRow>

          {isAdmin && (
            <div className="flex justify-end pt-4 mt-2 border-t border-border">
              <Button onClick={handleSave} disabled={updateMutation.isPending}
                className="bg-primary hover:bg-primary/90 text-white shadow-orange-glow">
                {updateMutation.isPending ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Saving...</> : 'Save Changes'}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* SECTION 3: Compliance */}
      <Card className="mb-4">
        <CardHeader className="pb-0">
          <CardTitle className="text-title">Compliance</CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <SettingRow label="Lock Period (days)" description="Entries older than this cannot be edited (0 = disabled)." disabled={!isAdmin}>
            {isAdmin ? (
              <Input 
                type="number" 
                value={lockPeriod} 
                onChange={(e) => setLockPeriod(Number(e.target.value))} 
                min={0}
                className="w-[120px] font-mono tabular-nums" 
              />
            ) : (
              <p className="text-body text-foreground font-mono tabular-nums">{lockPeriod}</p>
            )}
          </SettingRow>

          <SettingRow label="Approval Workflow" description="Require manager approval for timesheets." disabled={!isAdmin}>
            {isAdmin ? (
              <Switch 
                checked={approvalEnabled}
                onCheckedChange={handleApprovalToggle}
              />
            ) : (
              <p className="text-body text-foreground">{approvalEnabled ? 'Enabled' : 'Disabled'}</p>
            )}
          </SettingRow>

          {isAdmin && (
            <div className="flex justify-end pt-4 mt-2 border-t border-border">
              <Button onClick={handleSave} disabled={updateMutation.isPending}
                className="bg-primary hover:bg-primary/90 text-white shadow-orange-glow">
                {updateMutation.isPending ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Saving...</> : 'Save Changes'}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* SECTION 4: Danger Zone — Admin only */}
      {isAdmin && (
        <Card className="border-destructive/20">
          <CardHeader>
            <CardTitle className="text-title text-destructive">Danger Zone</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="text-body font-medium text-foreground">Delete Workspace</p>
                <p className="text-caption text-muted-foreground">
                  Permanently delete this workspace after 30 days.
                </p>
              </div>
              <Button variant="outline"
                className="border-destructive/40 text-destructive hover:bg-destructive/5"
                onClick={() => setShowDeleteDialog(true)}>
                Delete Workspace
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Approval Warning Dialog */}
      <AlertDialog open={showApprovalWarning} onOpenChange={setShowApprovalWarning}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Disable Approval Workflow?</AlertDialogTitle>
            <AlertDialogDescription>
              <span className="block bg-warning-muted border-l-4 border-warning p-3 rounded-r-lg text-sm text-foreground mt-2">
                Disabling the approval workflow will automatically approve all pending timesheets.
                This action cannot be undone. Are you sure you want to continue?
              </span>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-warning hover:bg-warning/90 text-white"
              onClick={() => {
                setApprovalEnabled(false)
                setShowApprovalWarning(false)
              }}
            >
              Disable Workflow
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Workspace Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Workspace</AlertDialogTitle>
            <AlertDialogDescription>
              This will schedule the workspace for permanent deletion in 30 days.
              All members will be notified. Are you sure?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive hover:bg-destructive/90 text-destructive-foreground"
              disabled={deleteMutation.isPending}
              onClick={handleDelete}
            >
              {deleteMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
