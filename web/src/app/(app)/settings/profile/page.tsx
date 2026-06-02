'use client'

import { useEffect, useState } from 'react'
import { useMe, useUpdateMe } from '@/features/settings/hooks'
import { cn } from '@/lib/utils'

// shadcn UI
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
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

export default function ProfileSettingsPage() {
  const { data: user, isLoading } = useMe()
  const updateMutation = useUpdateMe()

  const [fullName, setFullName] = useState('')
  const [avatarUrl, setAvatarUrl] = useState('')
  const [timezone, setTimezone] = useState('UTC')
  const [weeklyHoursGoal, setWeeklyHoursGoal] = useState<number | undefined>()

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
    <div className="max-w-2xl">
      <PageHeader title="Profile Settings" />

      <Card className="mb-4">
        <CardHeader className="pb-0">
          <CardTitle className="text-title">My Profile</CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <SettingRow label="Email Address" description="The email address associated with your account.">
            <p className="text-body text-muted-foreground">{user?.email}</p>
          </SettingRow>

          <SettingRow label="Full Name" description="Your preferred display name.">
            <Input
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-[220px]"
            />
          </SettingRow>

          <SettingRow label="Avatar URL" description="Link to an image file for your profile picture.">
            <Input
              value={avatarUrl}
              onChange={(e) => setAvatarUrl(e.target.value)}
              className="w-[220px]"
              placeholder="https://"
            />
          </SettingRow>

          <SettingRow label="Timezone" description="Your local timezone for reports and timers.">
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
          </SettingRow>

          <SettingRow label="Weekly Hours Goal" description="Target billable hours per week.">
            <Input
              type="number"
              min={1}
              max={168}
              value={weeklyHoursGoal ?? ''}
              onChange={(e) => setWeeklyHoursGoal(e.target.value ? Number(e.target.value) : undefined)}
              placeholder="e.g. 40"
              className="w-[120px] font-mono tabular-nums"
            />
          </SettingRow>

          <div className="flex justify-end pt-4 mt-2 border-t border-border">
            <Button
              onClick={handleSave}
              disabled={updateMutation.isPending || !fullName}
              className="bg-primary hover:bg-primary/90 text-white shadow-[0_0_15px_rgba(254,105,0,0.3)]"
            >
              {updateMutation.isPending ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Saving...</>
              ) : (
                'Save Changes'
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
