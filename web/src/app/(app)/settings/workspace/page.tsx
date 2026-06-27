'use client'

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { useRouter } from 'next/navigation'
import { useWorkspaceStore } from '@/stores/workspace-store'
import {
  useWorkspace,
  useUpdateWorkspace,
  useDeleteWorkspace,
  useWorkspaces
} from '@/features/settings/hooks'
import {
  useUpdateAttendanceSettings,
  useUpdateBillableSettings,
} from '@/features/attendance/hooks/useAttendance'
import type { WorkspaceUpdate } from '@/features/settings/api'
import { cn } from '@/lib/utils'

// shadcn UI
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
import { PageHeader, SettingRow } from '@/components/ui/setting-row'

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
  const attendanceMutation = useUpdateAttendanceSettings(activeWorkspaceId ?? '')
  const billableMutation = useUpdateBillableSettings(activeWorkspaceId ?? '')

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
  const [idleTimeout, setIdleTimeout] = useState(5)
  const [mandatoryDescriptions, setMandatoryDescriptions] = useState(false)
  const [maxTimerDuration, setMaxTimerDuration] = useState<number | undefined>()

  // Compliance
  const [pastEntryLimit, setPastEntryLimit] = useState<number | undefined>()
  const [lockPeriodDays, setLockPeriodDays] = useState<number | undefined>()
  const [approvalEnabled, setApprovalEnabled] = useState(false)
  
  // Attendance
  const [attendanceEnabled, setAttendanceEnabled] = useState(false)
  const [workDayStart, setWorkDayStart] = useState('09:00:00')
  const [targetDailyHours, setTargetDailyHours] = useState(8)
  const [attendanceMode, setAttendanceMode] = useState<'fixed_schedule' | 'flexible_hours'>('fixed_schedule')
  const [offDays, setOffDays] = useState<number[]>([0, 6])

  // Billing
  const [isBillable, setIsBillable] = useState(true)

  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showApprovalWarning, setShowApprovalWarning] = useState(false)
  const [showBillableWarning, setShowBillableWarning] = useState(false)

  useEffect(() => {
    if (workspace) {
      setName(workspace.name)
      setLogoUrl(workspace.logo_url ?? '')
      setTimezone(workspace.default_timezone ?? 'UTC')
      setDateFormat(workspace.date_format ?? 'MM/DD/YYYY')
      setCurrency(workspace.currency ?? 'USD')
      setDefaultHourlyRate(workspace.default_hourly_rate_cents ? workspace.default_hourly_rate_cents / 100 : undefined)

      setRoundingMode(workspace.rounding_mode ?? 'none')
      setRoundingInterval(workspace.rounding_interval_minutes ?? undefined)
      setIdleEnabled(workspace.idle_detection_enabled ?? false)
      setIdleTimeout(workspace.idle_timeout_minutes ?? 5)
      setMandatoryDescriptions(workspace.mandatory_description ?? false)
      setMaxTimerDuration(workspace.max_timer_duration_seconds ? workspace.max_timer_duration_seconds / 3600 : undefined)

      setPastEntryLimit(workspace.past_entry_limit_days ?? undefined)
      setLockPeriodDays(workspace.lock_period_days ?? undefined)
      setApprovalEnabled(workspace.approval_workflow_enabled ?? false)
      
      setAttendanceEnabled(workspace.attendance_enabled ?? false)
      setWorkDayStart(workspace.work_start_time ?? '09:00:00')
      setTargetDailyHours(workspace.daily_required_hours ?? 8)
      setAttendanceMode(workspace.attendance_mode ?? 'fixed_schedule')
      setOffDays(workspace.off_days ?? [0, 6])
      
      setIsBillable(workspace.is_billable ?? true)
    }
  }, [workspace])

  const handleSave = () => {
    if (attendanceEnabled) {
      if (targetDailyHours <= 0 || isNaN(targetDailyHours)) {
        toast.error("Target daily hours must be greater than 0")
        return
      }
      if (!workDayStart) {
        toast.error("Please provide a valid time")
        return
      }
    }

    const payload: WorkspaceUpdate = {
      name,
      logo_url: logoUrl || undefined,
      default_timezone: timezone,
      date_format: dateFormat,
      currency,
      default_hourly_rate_cents: defaultHourlyRate ? Math.round(defaultHourlyRate * 100) : undefined,
      rounding_mode: roundingMode,
      mandatory_description: mandatoryDescriptions,
      max_timer_duration_seconds: maxTimerDuration ? maxTimerDuration * 3600 : undefined,
      past_entry_limit_days: pastEntryLimit,
      lock_period_days: lockPeriodDays,
      approval_workflow_enabled: approvalEnabled,
      idle_detection_enabled: idleEnabled,
    }
    
    if (roundingMode !== 'none') {
      payload.rounding_interval_minutes = roundingInterval
    }
    if (idleEnabled) {
      payload.idle_timeout_minutes = idleTimeout
    }

    updateMutation.mutate(payload)
    
    // Also save attendance and billable separately as they are distinct features
    attendanceMutation.mutate({
      attendance_enabled: attendanceEnabled,
      work_start_time: workDayStart,
      daily_required_hours: targetDailyHours,
      attendance_mode: attendanceMode,
      off_days: offDays
    })
  }

  const handleApprovalToggle = (checked: boolean) => {
    if (!checked && workspace?.approval_workflow_enabled) {
      setShowApprovalWarning(true)
    } else {
      setApprovalEnabled(checked)
    }
  }
  
  const handleBillableToggle = async (checked: boolean) => {
    if (!checked && isBillable) {
      setShowBillableWarning(true)
    } else {
      try {
        await billableMutation.mutateAsync(checked)
        setIsBillable(checked)
        toast.success('Workspace billable settings updated')
      } catch (err) {
        toast.error('Failed to update billable settings')
      }
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

  return (
    <div className="max-w-5xl pb-16">
      <div className="mb-10">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Workspace Settings</h1>
      </div>

      {/* SECTION 1: General */}
      <section className="">
        <div className="mb-6">
          <PageHeader 
            title="General" 
            description="Manage your workspace identity, currency, and locale." 
          />
        </div>
        <div className="space-y-4">
            <SettingRow label="Workspace name" description="The display name for this workspace." disabled={!isAdmin}>
              {isAdmin ? (
                <Input value={name} onChange={(e) => setName(e.target.value)} className="max-w-md transition-shadow focus-visible:ring-brand-orange/50" />
              ) : (
                <p className="text-sm text-foreground">{name}</p>
              )}
            </SettingRow>
            
            <SettingRow label="Logo URL" description="Link to an image file for your workspace logo." disabled={!isAdmin}>
              {isAdmin ? (
                <Input value={logoUrl} onChange={(e) => setLogoUrl(e.target.value)} className="max-w-md transition-shadow focus-visible:ring-brand-orange/50" placeholder="https://" />
              ) : (
                <p className="text-sm text-foreground">{logoUrl || 'Not set'}</p>
              )}
            </SettingRow>
            
            <SettingRow label="Timezone" description="Default timezone for time entries." disabled={!isAdmin}>
              {isAdmin ? (
                <Select value={timezone} onValueChange={(v) => v && setTimezone(v)}>
                  <SelectTrigger className="max-w-md transition-shadow focus-visible:ring-brand-orange/50">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="UTC">UTC</SelectItem>
                    <SelectItem value="America/New_York">Eastern Time</SelectItem>
                    <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
                    <SelectItem value="Europe/London">London</SelectItem>
                    <SelectItem value="Asia/Karachi">Pakistan Standard Time (PKT)</SelectItem>
                    <SelectItem value="Asia/Kolkata">India Standard Time (IST)</SelectItem>
                    <SelectItem value="Australia/Sydney">Sydney</SelectItem>
                  </SelectContent>
                </Select>
              ) : (
                <p className="text-sm text-foreground">{timezone}</p>
              )}
            </SettingRow>
            
            <SettingRow label="Date format" description="How dates are displayed across the app." disabled={!isAdmin}>
              {isAdmin ? (
                <Select value={dateFormat} onValueChange={(v) => v && setDateFormat(v)}>
                  <SelectTrigger className="max-w-md transition-shadow focus-visible:ring-brand-orange/50">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                    <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                    <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                  </SelectContent>
                </Select>
              ) : (
                <p className="text-sm text-foreground">{dateFormat}</p>
              )}
            </SettingRow>
            
            <SettingRow label="Currency" description="Currency for billable amounts." disabled={!isAdmin}>
              {isAdmin ? (
                <Select value={currency} onValueChange={(v) => v && setCurrency(v)}>
                  <SelectTrigger className="max-w-md transition-shadow focus-visible:ring-brand-orange/50">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="USD">USD ($)</SelectItem>
                    <SelectItem value="EUR">EUR (€)</SelectItem>
                    <SelectItem value="GBP">GBP (£)</SelectItem>
                    <SelectItem value="PKR">PKR (Rs)</SelectItem>
                    <SelectItem value="INR">INR (₹)</SelectItem>
                  </SelectContent>
                </Select>
              ) : (
                <p className="text-sm text-foreground">{currency}</p>
              )}
            </SettingRow>

            <SettingRow label="Default hourly rate" description="Workspace-level fallback rate." disabled={!isAdmin}>
              {isAdmin ? (
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">$</span>
                  <Input 
                    type="number" 
                    className="max-w-[150px] transition-shadow focus-visible:ring-brand-orange/50"
                    value={defaultHourlyRate ?? ''} 
                    onChange={(e) => setDefaultHourlyRate(e.target.value ? parseFloat(e.target.value) : undefined)} 
                    min={0}
                  />
                </div>
              ) : (
                <p className="text-sm text-foreground font-mono tabular-nums">${defaultHourlyRate ?? 0}</p>
              )}
            </SettingRow>
        </div>
      </section>

      {/* SECTION 2: Time Tracking */}
      <section className="mt-12 pt-12 border-t border-border/40 first:border-0 first:pt-0 first:mt-0">
        <div className="mb-6">
          <PageHeader 
            title="Time Tracking" 
            description="Configure how time is recorded and rounded." 
          />
        </div>
        <div className="space-y-4">
            <SettingRow label="Rounding mode" description="How timer durations are rounded when saving." disabled={!isAdmin}>
              {isAdmin ? (
                <Select value={roundingMode} onValueChange={(v) => v && setRoundingMode(v)}>
                  <SelectTrigger className="max-w-[200px] transition-shadow focus-visible:ring-brand-orange/50">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">none</SelectItem>
                    <SelectItem value="up">up</SelectItem>
                    <SelectItem value="down">down</SelectItem>
                    <SelectItem value="nearest">nearest</SelectItem>
                  </SelectContent>
                </Select>
              ) : (
                <p className="text-sm text-foreground">{roundingMode}</p>
              )}
            </SettingRow>
            
            {roundingMode !== 'none' && (
              <SettingRow label="Rounding interval" description="Round to the nearest X minutes." disabled={!isAdmin}>
                {isAdmin ? (
                  <Select value={roundingInterval?.toString()} onValueChange={(v) => v && setRoundingInterval(parseInt(v))}>
                    <SelectTrigger className="max-w-[200px] transition-shadow focus-visible:ring-brand-orange/50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="5">5 minutes</SelectItem>
                      <SelectItem value="10">10 minutes</SelectItem>
                      <SelectItem value="15">15 minutes</SelectItem>
                      <SelectItem value="30">30 minutes</SelectItem>
                    </SelectContent>
                  </Select>
                ) : (
                  <p className="text-sm text-foreground">{roundingInterval} minutes</p>
                )}
              </SettingRow>
            )}

            <SettingRow label="Idle detection" description="Auto-pause when user has been inactive." disabled={!isAdmin}>
              {isAdmin ? (
                <Switch 
                  checked={idleEnabled} 
                  onCheckedChange={setIdleEnabled}
                  className="data-[state=checked]:bg-brand-orange"
                />
              ) : (
                <p className="text-sm text-foreground">{idleEnabled ? 'Enabled' : 'Disabled'}</p>
              )}
            </SettingRow>
            
            {idleEnabled && (
              <SettingRow label="Idle timeout" description="Minutes before idle is detected." disabled={!isAdmin}>
                {isAdmin ? (
                  <Select value={idleTimeout?.toString()} onValueChange={(v) => v && setIdleTimeout(parseInt(v))}>
                    <SelectTrigger className="max-w-[200px] transition-shadow focus-visible:ring-brand-orange/50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">1 minute</SelectItem>
                      <SelectItem value="5">5 minutes</SelectItem>
                      <SelectItem value="10">10 minutes</SelectItem>
                      <SelectItem value="15">15 minutes</SelectItem>
                      <SelectItem value="30">30 minutes</SelectItem>
                    </SelectContent>
                  </Select>
                ) : (
                  <p className="text-sm text-foreground">{idleTimeout} minutes</p>
                )}
              </SettingRow>
            )}

            <SettingRow label="Mandatory descriptions" description="Require a description on every time entry." disabled={!isAdmin}>
              {isAdmin ? (
                <Switch 
                  checked={mandatoryDescriptions} 
                  onCheckedChange={setMandatoryDescriptions}
                  className="data-[state=checked]:bg-brand-orange"
                />
              ) : (
                <p className="text-sm text-foreground">{mandatoryDescriptions ? 'Yes' : 'No'}</p>
              )}
            </SettingRow>

            <SettingRow label="Max timer duration" description="Auto-stop timer after this many hours." disabled={!isAdmin}>
              {isAdmin ? (
                <div className="flex items-center gap-2">
                  <Input 
                    type="number" 
                    className="max-w-[100px] transition-shadow focus-visible:ring-brand-orange/50"
                    value={maxTimerDuration ?? ''} 
                    onChange={(e) => setMaxTimerDuration(e.target.value ? parseInt(e.target.value) : undefined)} 
                    placeholder="12"
                  />
                  <span className="text-sm text-muted-foreground">hours</span>
                </div>
              ) : (
                <p className="text-sm text-foreground">{maxTimerDuration || 'No limit'}</p>
              )}
            </SettingRow>
        </div>
      </section>

      {/* SECTION 3: Compliance & Approval */}
      <section className="mt-12 pt-12 border-t border-border/40 first:border-0 first:pt-0 first:mt-0">
        <div className="mb-6">
          <PageHeader 
            title="Compliance & Approval" 
            description="Configure locks and approval workflows." 
          />
        </div>
        <div className="space-y-4">
            <SettingRow label="Past entry limit" description="How many days back manual entries can be backdated." disabled={!isAdmin}>
              {isAdmin ? (
                <div className="flex items-center gap-2">
                  <Input 
                    type="number" 
                    className="max-w-[100px] transition-shadow focus-visible:ring-brand-orange/50"
                    value={pastEntryLimit ?? ''} 
                    onChange={(e) => setPastEntryLimit(e.target.value ? parseInt(e.target.value) : undefined)} 
                    placeholder="Unrestricted"
                  />
                  <span className="text-sm text-muted-foreground">days</span>
                </div>
              ) : (
                <p className="text-sm text-foreground">{pastEntryLimit !== undefined ? `${pastEntryLimit} days` : 'Unrestricted'}</p>
              )}
            </SettingRow>

            <SettingRow label="Lock period (days)" description="Entries older than this cannot be edited (0 = disabled)." disabled={!isAdmin}>
              {isAdmin ? (
                <Input 
                  type="number" 
                  className="max-w-[100px] transition-shadow focus-visible:ring-brand-orange/50"
                  value={lockPeriodDays ?? ''} 
                  onChange={(e) => setLockPeriodDays(e.target.value ? parseInt(e.target.value) : undefined)} 
                />
              ) : (
                <p className="text-sm text-foreground">{lockPeriodDays || 'Disabled'}</p>
              )}
            </SettingRow>

            <SettingRow label="Approval workflow" description="Require manager approval for timesheets." disabled={!isAdmin}>
              {isAdmin ? (
                <Switch 
                  checked={approvalEnabled} 
                  onCheckedChange={handleApprovalToggle}
                  className="data-[state=checked]:bg-brand-orange"
                />
              ) : (
                <p className="text-sm text-foreground">{approvalEnabled ? 'Enabled' : 'Disabled'}</p>
              )}
            </SettingRow>
        </div>
      </section>

      {/* SECTION 4: Attendance & Schedule */}
      <section className="mt-12 pt-12 border-t border-border/40 first:border-0 first:pt-0 first:mt-0">
        <div className="mb-6">
          <PageHeader 
            title="Attendance & Schedule" 
            description="Manage working hours and attendance policies." 
          />
        </div>
        <div className="space-y-4">
            <SettingRow
              label="Enable attendance tracking"
              description="Turn on work-start prompts and daily hour targets for all Members."
            >
              {isAdmin ? (
                <Switch 
                  checked={attendanceEnabled} 
                  onCheckedChange={setAttendanceEnabled}
                  className="data-[state=checked]:bg-brand-orange"
                />
              ) : (
                <p className="text-sm text-foreground">{attendanceEnabled ? 'Enabled' : 'Disabled'}</p>
              )}
            </SettingRow>

            {attendanceEnabled && (
              <SettingRow
                label={attendanceMode === 'flexible_hours' ? "Daily reminder time" : "Work start time"}
                description={attendanceMode === 'flexible_hours' ? "When to remind users if they haven't logged time." : "When should users be prompted to start their day?"}
              >
                {isAdmin ? (
                  <Input 
                    type="time" 
                    value={workDayStart} 
                    onChange={(e) => setWorkDayStart(e.target.value)} 
                    disabled={!attendanceEnabled}
                    className="max-w-[150px] transition-shadow focus-visible:ring-brand-orange/50" 
                  />
                ) : (
                  <p className="text-sm text-foreground">{workDayStart}</p>
                )}
              </SettingRow>
            )}

            {attendanceEnabled && (
              <SettingRow
                label="Target daily hours"
                description="Default required hours per day."
              >
                {isAdmin ? (
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <Input 
                        type="number" 
                        min={0.01}
                        step={0.01}
                        value={targetDailyHours} 
                        onChange={(e) => setTargetDailyHours(parseFloat(e.target.value) || 0)} 
                        disabled={!attendanceEnabled}
                        className={cn(
                          "max-w-[100px] font-mono transition-shadow focus-visible:ring-brand-orange/50",
                          targetDailyHours <= 0 ? "border-destructive focus-visible:ring-destructive/50" : ""
                        )} 
                      />
                      <span className="text-sm text-muted-foreground">hours</span>
                    </div>
                    {targetDailyHours <= 0 && <p className="text-xs text-destructive">Must be greater than 0</p>}
                  </div>
                ) : (
                  <p className="text-sm text-foreground font-mono">
                    {targetDailyHours} <span className="text-muted-foreground text-xs">hrs</span>
                  </p>
                )}
              </SettingRow>
            )}

            {attendanceEnabled && (
              <SettingRow
                label="Attendance mode"
                description="Choose how work hours are tracked."
              >
                {isAdmin ? (
                  <Select disabled={!attendanceEnabled} value={attendanceMode} onValueChange={(v) => v && setAttendanceMode(v as 'fixed_schedule' | 'flexible_hours')}>
                    <SelectTrigger className="w-full sm:w-[200px] transition-shadow focus-visible:ring-brand-orange/50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="fixed_schedule">Fixed Schedule</SelectItem>
                      <SelectItem value="flexible_hours">Flexible Hours</SelectItem>
                    </SelectContent>
                  </Select>
                ) : (
                  <p className="text-sm text-foreground">{attendanceMode === 'fixed_schedule' ? 'Fixed Schedule' : 'Flexible Hours'}</p>
                )}
              </SettingRow>
            )}

            {attendanceEnabled && (
              <SettingRow
                label="Off days"
                description="Select which days are non-working days."
              >
                {isAdmin ? (
                  <div className="flex flex-wrap gap-2 items-center sm:justify-end">
                    {[
                      { label: 'S', val: 0 },
                      { label: 'M', val: 1 },
                      { label: 'T', val: 2 },
                      { label: 'W', val: 3 },
                      { label: 'T', val: 4 },
                      { label: 'F', val: 5 },
                      { label: 'S', val: 6 },
                    ].map((d) => {
                      const isOffDay = offDays.includes(d.val)
                      return (
                        <button
                          key={d.val}
                          type="button"
                          disabled={!attendanceEnabled}
                          onClick={() => {
                            setOffDays(prev => 
                              prev.includes(d.val) 
                                ? prev.filter(x => x !== d.val)
                                : [...prev, d.val].sort()
                            )
                          }}
                          className={cn(
                            "w-9 h-9 rounded-full text-[13px] font-semibold transition-colors flex items-center justify-center border",
                            isOffDay 
                              ? "bg-brand-orange text-white border-brand-orange shadow-sm hover:bg-brand-orange/90" 
                              : "bg-transparent text-muted-foreground border-border hover:bg-muted",
                            !attendanceEnabled && "opacity-50 cursor-not-allowed hover:bg-transparent hover:text-muted-foreground"
                          )}
                          >
                            {d.label}
                          </button>
                        )
                      })}
                    </div>
                  ) : (
                    <div className="flex gap-2 items-center sm:justify-end">
                      {[0,1,2,3,4,5,6].map(d => !offDays.includes(d) && (
                        <span key={d} className="w-8 h-8 rounded-full bg-brand-orange/10 text-brand-orange flex items-center justify-center text-[11px] font-bold">
                          {['S','M','T','W','T','F','S'][d]}
                        </span>
                      ))}
                    </div>
                  )}
                </SettingRow>
            )}
        </div>
      </section>

      {/* SECTION 5: Billing */}
      <section className="mt-12 pt-12 border-t border-border/40 first:border-0 first:pt-0 first:mt-0">
        <div className="mb-6">
          <PageHeader 
            title="Billing" 
            description="Manage workspace-wide billable tracking." 
          />
        </div>
        <div className="space-y-4">
            <SettingRow
              label="Workspace is billable"
              description="When OFF, no billable rates are applied workspace-wide. Stored rate data is preserved and restored if re-enabled."
            >
              {isAdmin ? (
                <Switch 
                  checked={isBillable} 
                  onCheckedChange={handleBillableToggle}
                  className="data-[state=checked]:bg-brand-orange"
                />
              ) : (
                <p className="text-sm text-foreground">{isBillable ? 'Yes' : 'No'}</p>
              )}
            </SettingRow>
            {!isBillable && (
              <div className="p-4 bg-muted/50 rounded-xl mt-4">
                <p className="text-sm text-muted-foreground flex items-center">
                  Billable tracking is OFF. All new time entries will have no billable rate applied.
                </p>
              </div>
            )}
        </div>
      </section>

      {/* SECTION 6: Danger Zone */}
      {isAdmin && (
        <section className="mt-12 pt-12 border-t border-border/40 first:border-0 first:pt-0 first:mt-0">
        <div className="mb-6">
          <PageHeader 
            title="Danger Zone" 
            description="Irreversible and destructive actions." 
          />
        </div>
        <div className="space-y-4">
              <SettingRow 
                label="Delete workspace" 
                description="Permanently delete this workspace. This action cannot be undone."
              >
                <div className="flex justify-start w-full">
                  <Button variant="outline"
                    className="border-destructive text-destructive hover:bg-destructive hover:text-white transition-colors rounded-lg shadow-sm px-6"
                    onClick={() => setShowDeleteDialog(true)}>
                    Delete workspace
                  </Button>
                </div>
              </SettingRow>
        </div>
        </section>
      )}

      {/* Global Save Button */}
      {isAdmin && (
        <div className="mt-12 pt-8 border-t border-border/40 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h3 className="text-[15px] font-semibold text-foreground">Save Changes</h3>
            <p className="text-[13px] text-muted-foreground mt-1">Make sure to save your general, compliance, and time tracking settings.</p>
          </div>
          <Button onClick={handleSave} disabled={updateMutation.isPending || attendanceMutation.isPending || billableMutation.isPending}
            className="bg-brand-orange hover:bg-brand-orange/90 text-white shadow-sm rounded-xl px-8 h-10 w-full sm:w-auto transition-all">
            {updateMutation.isPending || attendanceMutation.isPending || billableMutation.isPending ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Saving...</> : 'Save changes'}
          </Button>
        </div>
      )}

      {/* Dialogs */}
      <AlertDialog open={showBillableWarning} onOpenChange={setShowBillableWarning}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Disable workspace billing?</AlertDialogTitle>
            <AlertDialogDescription>
              Projects and tasks will no longer be billable workspace-wide. Existing rate data will be
              preserved and restored if you re-enable billing. Continue?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              id="billable-disable-confirm"
              className="bg-brand-orange text-white hover:bg-brand-orange/90"
              onClick={async () => {
                try {
                  await billableMutation.mutateAsync(false)
                  setIsBillable(false)
                  toast.success('Workspace billable settings updated')
                  setShowBillableWarning(false)
                } catch (err) {
                  toast.error('Failed to update billable settings')
                }
              }}
            >
              Disable Billing
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={showApprovalWarning} onOpenChange={setShowApprovalWarning}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Disable Approval Workflow?</AlertDialogTitle>
            <AlertDialogDescription>
              <span className="block bg-warning/10 border-l-4 border-warning p-3 rounded-r-lg text-sm text-foreground mt-2">
                Submitted timesheets will no longer require manager approval. Existing approved/rejected states will be preserved.
              </span>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-brand-orange text-white hover:bg-brand-orange/90"
              onClick={() => {
                setApprovalEnabled(false)
                setShowApprovalWarning(false)
              }}
            >
              Disable Approvals
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the
              workspace <strong>{workspace?.name}</strong> and all associated data, including
              projects, tasks, and time entries.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete Workspace
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
