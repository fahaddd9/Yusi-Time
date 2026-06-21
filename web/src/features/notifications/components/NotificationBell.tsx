'use client'

import React, { useEffect, useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bell, Check, Clock, FileText, XCircle, CheckCircle2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { useNotifications, useMarkNotificationRead, useMarkAllNotificationsRead } from '../hooks/useNotifications'
import { useWorkspaceStore } from '@/stores/workspace-store'
import {
  Popover,
  PopoverContent,
  PopoverHeader,
  PopoverTitle,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'

export function NotificationBell() {
  const { activeWorkspaceId } = useWorkspaceStore()
  const workspaceId = activeWorkspaceId ?? ''
  
  const { data: response, isLoading } = useNotifications({ workspace_id: workspaceId })
  const { mutate: markAllRead } = useMarkAllNotificationsRead()
  const { mutate: markRead } = useMarkNotificationRead()
  
  const notifications = response?.data || []
  const unreadCount = response?.unread_count || 0

  const [isOpen, setIsOpen] = useState(false)
  const markAllReadTimer = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (isOpen && unreadCount > 0) {
      markAllReadTimer.current = setTimeout(() => {
        markAllRead(workspaceId)
      }, 2000)
    } else {
      if (markAllReadTimer.current) clearTimeout(markAllReadTimer.current)
    }

    return () => {
      if (markAllReadTimer.current) clearTimeout(markAllReadTimer.current)
    }
  }, [isOpen, unreadCount, workspaceId, markAllRead])

  // Map event types to icons and colors
  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'timesheet_approved':
        return <div className="p-2 rounded-full bg-emerald-500/10 text-emerald-500"><CheckCircle2 className="h-4 w-4" /></div>
      case 'timesheet_rejected':
        return <div className="p-2 rounded-full bg-rose-500/10 text-rose-500"><XCircle className="h-4 w-4" /></div>
      case 'timesheet_submitted':
        return <div className="p-2 rounded-full bg-blue-500/10 text-blue-500"><FileText className="h-4 w-4" /></div>
      default:
        return <div className="p-2 rounded-full bg-primary/10 text-primary"><Bell className="h-4 w-4" /></div>
    }
  }

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger 
        render={<Button variant="ghost" size="icon" className="relative text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors" />}
      >
        <Bell className="h-5 w-5" />
        <AnimatePresence>
          {unreadCount > 0 && (
            <motion.div
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              key={unreadCount}
              transition={{ type: 'spring', stiffness: 500, damping: 25 }}
              className="absolute top-0 right-0 flex h-4 w-4 items-center justify-center rounded-full bg-[#F06900] text-[9px] font-bold text-white shadow-sm ring-2 ring-background"
            >
              {unreadCount > 9 ? '9+' : unreadCount}
            </motion.div>
          )}
        </AnimatePresence>
      </PopoverTrigger>
      
      <PopoverContent align="end" sideOffset={8} className="w-[380px] sm:w-[450px] p-0 flex flex-col bg-background/95 backdrop-blur-xl border-border/40 shadow-2xl h-[85vh] max-h-[800px] overflow-hidden">
        <PopoverHeader className="p-5 border-b border-border/40 space-y-0 flex-row items-center justify-between bg-card/50">
          <PopoverTitle className="text-lg font-semibold tracking-tight">Notifications</PopoverTitle>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => markAllRead(workspaceId)}
              className="h-8 text-xs font-medium text-primary hover:text-primary/80 hover:bg-primary/10 transition-colors"
            >
              <Check className="h-3.5 w-3.5 mr-1.5" />
              Mark all as read
            </Button>
          )}
        </PopoverHeader>
        
        <ScrollArea className="flex-1 min-h-0">
          <div className="px-4 py-5">
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex gap-4 p-4 rounded-2xl border border-border/30 bg-card/50">
                  <Skeleton className="h-10 w-10 rounded-full" />
                  <div className="space-y-2 flex-1">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-full" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : notifications.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-4 mt-20">
              <div className="h-20 w-20 rounded-full bg-primary/5 flex items-center justify-center mb-2">
                <Bell className="h-10 w-10 text-primary/30" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-foreground">You&apos;re all caught up!</h3>
                <p className="text-sm text-muted-foreground mt-1 max-w-[200px] mx-auto">
                  When you have new notifications, they will appear here.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {notifications.map((notification) => {
                const isRead = notification.read_at !== null
                return (
                  <motion.div
                    layout
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    key={notification.id}
                    className={`group relative flex gap-4 p-4 rounded-2xl transition-all duration-300 cursor-pointer overflow-hidden border ${
                      !isRead 
                        ? 'bg-card border-primary/20 shadow-md shadow-primary/5 hover:border-primary/40' 
                        : 'bg-muted/30 border-transparent hover:bg-card hover:border-border/50 hover:shadow-sm'
                    }`}
                    onClick={() => {
                      if (!isRead) {
                        markRead([notification.id])
                      }
                    }}
                  >
                    {/* Unread indicator gradient line */}
                    {!isRead && (
                      <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-[#F06900] to-orange-400" />
                    )}
                    
                    <div className="shrink-0 mt-0.5 relative z-10">
                      {getEventIcon(notification.event_type)}
                    </div>
                    
                    <div className="flex-1 min-w-0 relative z-10">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <p className={`text-sm tracking-tight ${!isRead ? 'font-semibold text-foreground' : 'font-medium text-foreground/80'}`}>
                          {notification.title}
                        </p>
                        <span className="text-[10px] whitespace-nowrap text-muted-foreground/80 font-medium flex items-center shrink-0 mt-0.5">
                          {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true }).replace('about ', '')}
                        </span>
                      </div>
                      <p className={`text-xs leading-relaxed ${!isRead ? 'text-muted-foreground/90' : 'text-muted-foreground/70'} line-clamp-2`}>
                        {notification.message}
                      </p>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          )}
          </div>
        </ScrollArea>
      </PopoverContent>
    </Popover>
  )
}
