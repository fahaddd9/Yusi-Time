import { useState, useEffect } from 'react'
import { format, subDays, startOfWeek, endOfWeek, startOfMonth, endOfMonth, subWeeks } from 'date-fns'
import { Filter, Save, Download, Calendar, Search, Users, Briefcase, Plus, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Calendar as CalendarComponent } from "@/components/ui/calendar"
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog"
import { cn } from "@/lib/utils"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
  DropdownMenuGroup
} from '@/components/ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter
} from '@/components/ui/dialog'
import { SavedReportView } from '../api'

export interface ReportFilters {
  date_from: string
  date_to: string
  date_range_type?: string
  group_by?: 'project' | 'user' | 'client' | 'tag'
  project_id?: string
  client_id?: string
  task_id?: string
  user_id?: string
  billable?: boolean
  status?: string
}

interface FilterBarProps {
  filters: ReportFilters
  onChange: (filters: ReportFilters) => void
  
  // View management
  savedViews?: SavedReportView[]
  onSaveView?: (name: string, savedFilters: any) => Promise<void> | void
  onSelectView?: (view: SavedReportView) => void
  onDeleteView?: (viewId: string) => void
  
  // CSV Export
  onExportCsv?: () => void
  
  // Which fields to show
  showGroupBy?: boolean
  showBillable?: boolean
  showStatus?: boolean
  showMemberFilter?: boolean
  showTaskFilter?: boolean
  
  // Workspace data for dropdowns (passed from parent)
  projects?: { id: string; name: string }[]
  clients?: { id: string; name: string }[]
  users?: { id: string; name: string }[]
  tasks?: { id: string; name: string }[]
}

const DATE_RANGES = [
  { label: 'Last 7 days', value: 'last_7_days' },
  { label: 'Last 30 days', value: 'last_30_days' },
  { label: 'This Week', value: 'this_week' },
  { label: 'Last Week', value: 'last_week' },
  { label: 'This Month', value: 'this_month' },
  { label: 'All Time', value: 'all_time' },
  { label: 'Custom', value: 'custom' },
]

export function FilterBar({
  filters,
  onChange,
  savedViews = [],
  onSaveView,
  onSelectView,
  onDeleteView,
  onExportCsv,
  showGroupBy = false,
  showBillable = true,
  showStatus = true,
  showMemberFilter,
  showTaskFilter = false,
  projects = [],
  clients = [],
  users = [],
  tasks = []
}: FilterBarProps) {
  const [dateRangeType, setDateRangeType] = useState('last_7_days')
  const [saveViewName, setSaveViewName] = useState('')
  const [saveDialogOpen, setSaveDialogOpen] = useState(false)
  const [viewToDelete, setViewToDelete] = useState<string | null>(null)
  
  const [localCustomFrom, setLocalCustomFrom] = useState(filters.date_from)
  const [localCustomTo, setLocalCustomTo] = useState(filters.date_to)
  const [customError, setCustomError] = useState('')

  useEffect(() => {
    if (dateRangeType !== 'custom') {
      setLocalCustomFrom(filters.date_from)
      setLocalCustomTo(filters.date_to)
      setCustomError('')
    }
  }, [filters.date_from, filters.date_to, dateRangeType])

  const handleUpdate = (updates: Partial<ReportFilters>) => {
    onChange({ ...filters, ...updates })
  }

  const handleDateRangeChange = (val: string | null) => {
    if (!val) return
    setDateRangeType(val)
    const now = new Date()
    let date_from = filters.date_from
    let date_to = filters.date_to

    switch (val) {
      case 'last_7_days':
        date_from = format(subDays(now, 7), 'yyyy-MM-dd')
        date_to = format(now, 'yyyy-MM-dd')
        break
      case 'last_30_days':
        date_from = format(subDays(now, 30), 'yyyy-MM-dd')
        date_to = format(now, 'yyyy-MM-dd')
        break
      case 'this_week':
        date_from = format(startOfWeek(now, { weekStartsOn: 1 }), 'yyyy-MM-dd')
        date_to = format(endOfWeek(now, { weekStartsOn: 1 }), 'yyyy-MM-dd')
        break
      case 'last_week':
        date_from = format(startOfWeek(subWeeks(now, 1), { weekStartsOn: 1 }), 'yyyy-MM-dd')
        date_to = format(endOfWeek(subWeeks(now, 1), { weekStartsOn: 1 }), 'yyyy-MM-dd')
        break
      case 'this_month':
        date_from = format(startOfMonth(now), 'yyyy-MM-dd')
        date_to = format(endOfMonth(now), 'yyyy-MM-dd')
        break
      case 'all_time':
        date_from = '2000-01-01'
        date_to = '2099-12-31'
        break
      case 'custom':
        return
    }
    
    if (val !== 'custom') {
      handleUpdate({ date_from, date_to })
    }
  }

  const handleCustomDateChange = (field: 'date_from' | 'date_to', value: string) => {
    const newFrom = field === 'date_from' ? value : localCustomFrom
    const newTo = field === 'date_to' ? value : localCustomTo
    
    if (field === 'date_from') setLocalCustomFrom(value)
    if (field === 'date_to') setLocalCustomTo(value)
    
    if (newFrom && newTo && newFrom > newTo) {
      setCustomError('Start date cannot be after end date')
    } else {
      setCustomError('')
      handleUpdate({ date_from: newFrom, date_to: newTo })
    }
  }

  const handleSaveView = async () => {
    if (saveViewName.trim() && onSaveView) {
      try {
        await onSaveView(saveViewName.trim(), { ...filters, date_range_type: dateRangeType })
        setSaveViewName('')
        setSaveDialogOpen(false)
      } catch (err: any) {
        // Parent component will show toast, we just prevent dialog close
      }
    }
  }

  const handleSelectView = (view: SavedReportView) => {
    if (!onSelectView) return
    const savedFilters = view.filters as any
    if (savedFilters.date_range_type && savedFilters.date_range_type !== 'custom') {
      const now = new Date()
      let date_from = savedFilters.date_from
      let date_to = savedFilters.date_to
      switch (savedFilters.date_range_type) {
        case 'last_7_days':
          date_from = format(subDays(now, 7), 'yyyy-MM-dd')
          date_to = format(now, 'yyyy-MM-dd')
          break
        case 'last_30_days':
          date_from = format(subDays(now, 30), 'yyyy-MM-dd')
          date_to = format(now, 'yyyy-MM-dd')
          break
        case 'this_week':
          date_from = format(startOfWeek(now, { weekStartsOn: 1 }), 'yyyy-MM-dd')
          date_to = format(endOfWeek(now, { weekStartsOn: 1 }), 'yyyy-MM-dd')
          break
        case 'last_week':
          date_from = format(startOfWeek(subWeeks(now, 1), { weekStartsOn: 1 }), 'yyyy-MM-dd')
          date_to = format(endOfWeek(subWeeks(now, 1), { weekStartsOn: 1 }), 'yyyy-MM-dd')
          break
        case 'this_month':
          date_from = format(startOfMonth(now), 'yyyy-MM-dd')
          date_to = format(endOfMonth(now), 'yyyy-MM-dd')
          break
        case 'all_time':
          date_from = '2000-01-01'
          date_to = '2099-12-31'
          break
      }
      setDateRangeType(savedFilters.date_range_type)
      onSelectView({ ...view, filters: { ...savedFilters, date_from, date_to } })
    } else {
      if (savedFilters.date_range_type) setDateRangeType(savedFilters.date_range_type)
      else setDateRangeType('custom')
      onSelectView(view)
    }
  }

  const handleClearFilters = () => {
    handleUpdate({
      project_id: undefined,
      client_id: undefined,
      task_id: undefined,
      user_id: undefined,
      billable: undefined,
      status: undefined
    })
  }

  const hasActiveFilters = !!(filters.project_id || filters.client_id || filters.task_id || filters.user_id || filters.billable !== undefined || filters.status)

  return (
    <div className="flex flex-col gap-3 p-3 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg shadow-sm">
      
      {/* Top Row: Views & Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          {onSelectView && (
            <DropdownMenu>
              <DropdownMenuTrigger>
                <Button variant="outline" size="sm" className="gap-2 h-9 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-[1px] transition-all bg-white dark:bg-neutral-900 border-neutral-300 dark:border-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-800">
                  <Filter className="w-4 h-4 text-neutral-500 dark:text-neutral-400" />
                  <span className="hidden sm:inline text-neutral-700 dark:text-neutral-300">Views</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-56">
                <DropdownMenuGroup>
                  <DropdownMenuLabel>Your Saved Views</DropdownMenuLabel>
                  {savedViews.length === 0 ? (
                    <div className="p-2 text-sm text-neutral-500 text-center">No saved views</div>
                  ) : (
                    savedViews.map(view => (
                      <DropdownMenuItem key={view.id} className="justify-between group">
                        <span className="truncate flex-1 cursor-pointer py-1.5" onClick={() => handleSelectView(view)}>{view.name}</span>
                        {onDeleteView && (
                          <div 
                            className="p-1 cursor-pointer opacity-0 group-hover:opacity-100 transition-opacity" 
                            onPointerDown={(e) => { 
                              e.preventDefault()
                              e.stopPropagation()
                              setViewToDelete(view.id) 
                            }}
                          >
                            <X className="w-4 h-4 text-neutral-400 hover:text-red-500" />
                          </div>
                        )}
                      </DropdownMenuItem>
                    ))
                  )}
                </DropdownMenuGroup>
              </DropdownMenuContent>
            </DropdownMenu>
          )}

          {onSaveView && (
            <Dialog open={saveDialogOpen} onOpenChange={setSaveDialogOpen}>
              <DialogTrigger>
                <Button variant="outline" size="sm" className="gap-2 h-9 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-[1px] transition-all bg-white dark:bg-neutral-900 border-neutral-300 dark:border-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-800">
                  <Save className="w-4 h-4 text-neutral-500 dark:text-neutral-400" />
                  <span className="hidden sm:inline text-neutral-700 dark:text-neutral-300">Save View</span>
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[425px]">
                <DialogHeader><DialogTitle>Save Report View</DialogTitle></DialogHeader>
                <div className="py-4">
                  <Input placeholder="E.g., Monthly Billable by Client" value={saveViewName} onChange={(e) => setSaveViewName(e.target.value)} />
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setSaveDialogOpen(false)}>Cancel</Button>
                  <Button onClick={handleSaveView} disabled={!saveViewName.trim()}>Save</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          )}
        </div>

        <div className="flex items-center gap-2">
          {onExportCsv && (
            <Button size="sm" onClick={onExportCsv} className="gap-2 h-9 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-[1px] transition-all bg-brand-orange hover:bg-brand-orange/90 text-white border-none">
              <Download className="w-4 h-4" />
              <span className="hidden sm:inline">Export CSV</span>
            </Button>
          )}
        </div>
      </div>

      <div className="h-px w-full bg-neutral-100 dark:bg-neutral-800"></div>

      {/* Bottom Row: Filters */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Date Range Selector */}
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-neutral-500 hidden sm:block" />
            <Select value={dateRangeType} onValueChange={handleDateRangeChange}>
              <SelectTrigger className="w-[140px] h-9">
                <span data-slot="select-value" className="flex flex-1 text-left truncate">
                  {DATE_RANGES.find(r => r.value === dateRangeType)?.label || 'Date Range'}
                </span>
              </SelectTrigger>
              <SelectContent>
                {DATE_RANGES.map(r => (
                  <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            {dateRangeType === 'custom' && (
              <div className="flex items-center gap-2">
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant={"outline"} className={cn("w-[130px] justify-start text-left font-normal h-9 px-3", !localCustomFrom && "text-muted-foreground")}>
                      {localCustomFrom ? format(new Date(localCustomFrom), "PP") : <span>Pick a date</span>}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <CalendarComponent mode="single" selected={localCustomFrom ? new Date(localCustomFrom + 'T00:00:00') : undefined} onSelect={(date) => {
                      if (date) {
                        const offsetDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
                        handleCustomDateChange('date_from', offsetDate.toISOString().split('T')[0])
                      }
                    }} initialFocus />
                  </PopoverContent>
                </Popover>
                <span className="text-neutral-500 text-sm">to</span>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant={"outline"} className={cn("w-[130px] justify-start text-left font-normal h-9 px-3", !localCustomTo && "text-muted-foreground")}>
                      {localCustomTo ? format(new Date(localCustomTo), "PP") : <span>Pick a date</span>}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <CalendarComponent mode="single" selected={localCustomTo ? new Date(localCustomTo + 'T00:00:00') : undefined} onSelect={(date) => {
                      if (date) {
                        const offsetDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
                        handleCustomDateChange('date_to', offsetDate.toISOString().split('T')[0])
                      }
                    }} initialFocus />
                  </PopoverContent>
                </Popover>
              </div>
            )}
          </div>
          {customError && (
            <span className="text-xs text-red-500 font-medium ml-6">{customError}</span>
          )}
        </div>

        <div className="h-5 w-px bg-neutral-200 dark:bg-neutral-800 mx-1 hidden lg:block"></div>

        <Select value={filters.project_id || 'all'} onValueChange={(val: any) => handleUpdate({ project_id: val === 'all' || !val ? undefined : val })}>
          <SelectTrigger className="w-[160px] h-9">
            <span data-slot="select-value" className="flex flex-1 text-left truncate">
              <span className="text-neutral-500 mr-1 hidden lg:inline">Project:</span>
              {filters.project_id && filters.project_id !== 'all' ? projects.find(p => p.id === filters.project_id)?.name || filters.project_id : 'All'}
            </span>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Projects</SelectItem>
            {projects.map(p => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}
          </SelectContent>
        </Select>

        <Select value={filters.client_id || 'all'} onValueChange={(val: any) => handleUpdate({ client_id: val === 'all' || !val ? undefined : val })}>
          <SelectTrigger className="w-[160px] h-9">
            <span data-slot="select-value" className="flex flex-1 text-left truncate">
              <span className="text-neutral-500 mr-1 hidden lg:inline">Client:</span>
              {filters.client_id && filters.client_id !== 'all' ? clients.find(c => c.id === filters.client_id)?.name || filters.client_id : 'All'}
            </span>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Clients</SelectItem>
            {clients.map(c => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}
          </SelectContent>
        </Select>

        {showTaskFilter && (
          <Select disabled={!filters.project_id} value={filters.task_id || 'all'} onValueChange={(val: any) => handleUpdate({ task_id: val === 'all' || !val ? undefined : val })}>
            <SelectTrigger className="w-[160px] h-9">
              <span data-slot="select-value" className="flex flex-1 text-left truncate">
                <span className="text-neutral-500 mr-1 hidden lg:inline">Task:</span>
                {!filters.project_id ? 'Select project' : (filters.task_id && filters.task_id !== 'all' ? tasks.find(t => t.id === filters.task_id)?.name || filters.task_id : 'All Tasks')}
              </span>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Tasks</SelectItem>
              {tasks.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}
            </SelectContent>
          </Select>
        )}

        {showMemberFilter !== false && (
          <Select value={filters.user_id || 'all'} onValueChange={(val: any) => handleUpdate({ user_id: val === 'all' || !val ? undefined : val })}>
            <SelectTrigger className="w-[160px] h-9">
              <span data-slot="select-value" className="flex flex-1 text-left truncate">
                <span className="text-neutral-500 mr-1 hidden lg:inline">Member:</span>
                {filters.user_id && filters.user_id !== 'all' ? users.find(u => u.id === filters.user_id)?.name || filters.user_id : 'All'}
              </span>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Members</SelectItem>
              {users.map(u => <SelectItem key={u.id} value={u.id}>{u.name}</SelectItem>)}
            </SelectContent>
          </Select>
        )}

        {showBillable && (
          <Select value={filters.billable !== undefined ? String(filters.billable) : 'all'} onValueChange={(val) => handleUpdate({ billable: val === 'all' ? undefined : val === 'true' })}>
            <SelectTrigger className="w-[130px] h-9">
              <span data-slot="select-value" className="flex flex-1 text-left truncate">
                {filters.billable === true ? 'Billable' : filters.billable === false ? 'Non-Billable' : 'All Status'}
              </span>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="true">Billable</SelectItem>
              <SelectItem value="false">Non-Billable</SelectItem>
            </SelectContent>
          </Select>
        )}

        {showGroupBy && (
          <>
            <div className="h-5 w-px bg-neutral-200 dark:bg-neutral-800 mx-1 hidden lg:block"></div>
            <Select value={filters.group_by || 'project'} onValueChange={(val) => handleUpdate({ group_by: val as any })}>
              <SelectTrigger className="w-[180px] h-9 bg-neutral-50 dark:bg-neutral-900 border-neutral-300 dark:border-neutral-700">
                <span data-slot="select-value" className="flex flex-1 text-left truncate">
                  <span className="text-neutral-500 font-medium mr-1">Group by:</span> 
                  <span className="capitalize">{filters.group_by === 'user' ? 'Member' : (filters.group_by || 'Project')}</span>
                </span>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="project">Project</SelectItem>
                <SelectItem value="client">Client</SelectItem>
                {showMemberFilter !== false && (
                  <SelectItem value="user">Member</SelectItem>
                )}
                <SelectItem value="tag">Tag</SelectItem>
              </SelectContent>
            </Select>
          </>
        )}

        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={handleClearFilters} className="h-9 px-3 text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300">
            Clear filters
          </Button>
        )}
      </div>

      <AlertDialog open={!!viewToDelete} onOpenChange={(open) => !open && setViewToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Saved View</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this saved view? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              className="bg-red-500 hover:bg-red-600 focus:ring-red-500"
              onClick={() => {
                if (viewToDelete && onDeleteView) {
                  onDeleteView(viewToDelete)
                }
              }}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
