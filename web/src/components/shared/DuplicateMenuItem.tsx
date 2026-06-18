import { Copy } from 'lucide-react'
import { useDuplicateEntry } from '@/features/time-entries/hooks'
import { DropdownMenuItem } from '@/components/ui/dropdown-menu'

interface Props {
  entryId: string
  entryStatus: string
  workspaceId: string
}

export function DuplicateMenuItem({ entryId, entryStatus, workspaceId }: Props) {
  if (entryStatus === 'pending') return null  // ABSENT not disabled
  const { mutate } = useDuplicateEntry()
  return (
    <DropdownMenuItem onClick={() => mutate({ entryId, workspaceId })}>
      <Copy className="w-4 h-4 mr-2" />Duplicate
    </DropdownMenuItem>
  )
}
