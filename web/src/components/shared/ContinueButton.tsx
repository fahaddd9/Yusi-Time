import { useState } from 'react'
import { Play } from 'lucide-react'
import { useContinueEntry } from '@/features/time-entries/hooks'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
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

interface ContinueButtonProps {
  entryId: string
  entryStatus: string
  workspaceId: string
  hasRunningTimer: boolean
}

export function ContinueButton({
  entryId, entryStatus, workspaceId, hasRunningTimer
}: ContinueButtonProps) {
  const { mutate, isPending } = useContinueEntry()
  const [showConfirm, setShowConfirm] = useState(false)

  // ABSENT for pending — returns null, not disabled
  if (entryStatus === 'pending') return null

  const handleClick = () => {
    if (hasRunningTimer) {
      setShowConfirm(true)
    } else {
      mutate({ entryId, workspaceId })
    }
  }

  return (
    <>
      <Tooltip>
        <TooltipTrigger 
          render={<button />}
          onClick={handleClick}
          disabled={isPending}
          aria-label="Continue this entry"
          className="p-1.5 rounded-md text-muted-foreground hover:text-[#F06900] hover:bg-[#FFF0E6] dark:hover:bg-orange-900/20 transition-colors duration-120 disabled:opacity-40"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
        </TooltipTrigger>
        <TooltipContent>Continue this entry</TooltipContent>
      </Tooltip>

      <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Switch active timer?</AlertDialogTitle>
            <AlertDialogDescription>
              Your current timer will be stopped and saved before starting this one.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-brand-orange hover:bg-brand-orange-hover text-white"
              onClick={() => {
                setShowConfirm(false)
                mutate({ entryId, workspaceId, force: true })
              }}
            >
              Stop & Continue
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
