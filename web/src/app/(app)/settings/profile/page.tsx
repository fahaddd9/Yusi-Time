'use client'

import { useEffect, useState } from 'react'
import { useMe, useUpdateMe } from '@/features/settings/hooks'
import { PageHeader, SettingRow } from '@/components/ui/setting-row'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Loader2, User2 } from 'lucide-react'
import { usePushNotifications } from '@/features/attendance/hooks/usePushNotifications'
import { requestNativeIdlePermission } from '@/features/timer/hooks/useIdleDetector'

export default function ProfileSettingsPage() {
  const { data: user, isLoading } = useMe()
  const updateMutation = useUpdateMe()

  const [fullName, setFullName] = useState('')
  const [avatarUrl, setAvatarUrl] = useState('')
  const [timezone, setTimezone] = useState('UTC')
  const [weeklyHoursGoal, setWeeklyHoursGoal] = useState<number | undefined>()

  const [idleGranted, setIdleGranted] = useState(false)
  const [idleUnsupported, setIdleUnsupported] = useState(false)
  const [idlePreference, setIdlePreference] = useState(false)

  const push = usePushNotifications()

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const pref = localStorage.getItem('os_idle_preference') === 'enabled'
      setIdlePreference(pref)
      // @ts-ignore
      if (!window.IdleDetector) {
        setIdleUnsupported(true)
      } else {
        // @ts-ignore
        navigator.permissions.query({ name: 'idle-detection' }).then((status) => {
          setIdleGranted(status.state === 'granted')
          status.onchange = () => {
            setIdleGranted(status.state === 'granted')
            if (status.state !== 'granted') {
              localStorage.removeItem('os_idle_preference')
              setIdlePreference(false)
            }
          }
        }).catch(() => {
          // Ignore unsupported query
        })
      }
    }
  }, [])

  const handleIdleToggle = async (checked: boolean) => {
    if (checked) {
      const res = await requestNativeIdlePermission()
      if (res === 'granted') {
        setIdleGranted(true)
        setIdlePreference(true)
        localStorage.setItem('os_idle_preference', 'enabled')
      }
      if (res === 'unsupported') setIdleUnsupported(true)
    } else {
      setIdlePreference(false)
      localStorage.removeItem('os_idle_preference')
    }
  }

  useEffect(() => {
    if (user) {
      setFullName(user.full_name)
      setAvatarUrl(user.avatar_url ?? '')
      setTimezone(user.timezone ?? 'UTC')
      setWeeklyHoursGoal(user.weekly_hours_goal ?? undefined)
    }
  }, [user])

  const handleSave = () => {
    updateMutation.mutate({
      full_name: fullName,
      avatar_url: avatarUrl || undefined,
      timezone,
      weekly_hours_goal: weeklyHoursGoal,
    })
  }

  if (isLoading) {
    return (
      <div className="max-w-2xl space-y-6">
        {[1].map((i) => (
          <Skeleton key={i} className="h-64 w-full rounded-xl" />
        ))}
      </div>
    )
  }

  return (
    <div className="max-w-5xl pb-16">
      <div className="mb-10">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Profile Settings</h1>
      </div>

      <section className="">
        <div className="mb-6">
          <PageHeader 
            title="Personal Info" 
            description="Update your photo, name, and locale settings here." 
          />
        </div>
        <div className="space-y-4">
            <SettingRow label="Email address" description="The email address associated with your account.">
              <div className="h-10 px-3 py-2 rounded-md border border-border bg-muted/30 text-sm flex items-center text-muted-foreground max-w-md">
                {user?.email}
              </div>
            </SettingRow>

            <SettingRow label="Full name" description="Your preferred display name across the workspace.">
              <div className="flex flex-col sm:flex-row gap-4 sm:items-center">
                <div className="w-16 h-16 rounded-full overflow-hidden bg-muted flex items-center justify-center border border-border flex-shrink-0">
                  {avatarUrl ? (
                    <img src={avatarUrl} alt="Avatar" className="w-full h-full object-cover" />
                  ) : (
                    <User2 className="w-8 h-8 text-muted-foreground/50" />
                  )}
                </div>
                <div className="flex-1 max-w-md">
                  <Input
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Enter your full name"
                    className="transition-shadow focus-visible:ring-brand-orange/50"
                  />
                </div>
              </div>
            </SettingRow>

            <SettingRow label="Avatar URL" description="Link to your profile picture.">
              <Input
                value={avatarUrl}
                onChange={(e) => setAvatarUrl(e.target.value)}
                placeholder="https://..."
                className="max-w-md transition-shadow focus-visible:ring-brand-orange/50"
              />
            </SettingRow>

            <SettingRow label="Timezone" description="Your local timezone.">
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
            </SettingRow>
        </div>
      </section>

      <section className="mt-12 pt-12 border-t border-border/40 first:border-0 first:pt-0 first:mt-0">
        <div className="mb-6">
          <PageHeader 
            title="Goals" 
            description="Set your personal targets." 
          />
        </div>
        <div className="space-y-4">
            <SettingRow label="Weekly hours goal" description="Target total tracked hours per week.">
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  min={0}
                  step={0.5}
                  value={weeklyHoursGoal ?? ''}
                  onChange={(e) => setWeeklyHoursGoal(e.target.value ? parseFloat(e.target.value) : undefined)}
                  className="max-w-[100px] transition-shadow focus-visible:ring-brand-orange/50"
                />
                <span className="text-sm text-muted-foreground">hours</span>
              </div>
            </SettingRow>
        </div>
      </section>

      <section className="mt-12 pt-12 border-t border-border/40 first:border-0 first:pt-0 first:mt-0">
        <div className="mb-6">
          <PageHeader 
            title="Notification Settings" 
            description="Manage your browser push notifications." 
          />
        </div>
        <div className="space-y-4">
            <SettingRow label="Enable push notifications" description="Receive attendance prompts directly on your device.">
              <div className="flex items-center gap-3">
                <Switch 
                  checked={push.isEnabled} 
                  onCheckedChange={(checked) => checked ? push.enable() : push.disable()} 
                  disabled={push.isPending || push.permissionState === 'unsupported' || push.permissionState === 'denied'} 
                />
                {(push.permissionState === 'unsupported' || push.permissionState === 'denied') && (
                  <span className="text-sm text-muted-foreground">
                    {push.statusLabel}
                  </span>
                )}
              </div>
            </SettingRow>

            <SettingRow 
              label="Enable OS-level idle detection" 
              description="Chrome/Edge only. Full cross-app OS detection requires the desktop app."
            >
              <div className="flex items-center gap-3">
                <Switch 
                  checked={idlePreference} 
                  onCheckedChange={handleIdleToggle}
                  disabled={idleUnsupported}
                />
                {idleUnsupported && (
                  <span className="text-sm text-muted-foreground">
                    Unsupported
                  </span>
                )}
              </div>
            </SettingRow>
        </div>
      </section>

      {/* Global Save Button */}
      <div className="mt-12 pt-8 border-t border-border/40 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h3 className="text-[15px] font-semibold text-foreground">Save Changes</h3>
          <p className="text-[13px] text-muted-foreground mt-1">Make sure to save your personal details.</p>
        </div>
        <Button
          onClick={handleSave}
          disabled={updateMutation.isPending || !fullName}
          className="bg-brand-orange hover:bg-brand-orange/90 text-white shadow-sm transition-all rounded-xl px-8 h-10 w-full sm:w-auto"
        >
          {updateMutation.isPending ? (
            <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Saving...</>
          ) : (
            'Save changes'
          )}
        </Button>
      </div>
    </div>
  )
}
