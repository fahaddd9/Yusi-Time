/**
 * Settings root page — redirects to the workspace settings.
 */
import { redirect } from 'next/navigation'

export default function SettingsPage() {
  redirect('/settings/workspace')
}
