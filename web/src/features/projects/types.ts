export interface Client {
  id: string
  workspace_id: string
  name: string
  email: string | null
  phone: string | null
  hourly_rate_cents: number | null
  project_count: number
  created_at: string
  updated_at: string
}

export interface Project {
  id: string
  workspace_id: string
  name: string
  client_id: string | null
  client_name: string | null
  visibility: "public" | "private"
  status: "active" | "archived" | "completed"
  default_hourly_rate_cents: number | null
  default_billable: boolean
  budget_hours: number | null
  budget_amount_cents: number | null
  color: string | null
  hours_logged: number
  created_at: string
  updated_at: string
}

export interface Task {
  id: string
  workspace_id: string
  project_id: string
  name: string
  assignee_user_id: string | null
  estimated_hours: number | null
  billable_override: boolean | null
  hourly_rate_cents: number | null
  created_at: string
}

export interface Tag {
  id: string
  workspace_id: string
  name: string
  color: string | null
  created_at: string
}

export interface CreateClientDTO {
  name: string
  email?: string | null
  phone?: string | null
  address?: string | null
  currency?: string
  hourly_rate_cents?: number | null
}

export interface UpdateClientDTO extends Partial<CreateClientDTO> {}

export interface CreateProjectDTO {
  name: string
  client_id?: string | null
  visibility?: "public" | "private"
  status?: "active" | "archived" | "completed"
  default_hourly_rate_cents?: number | null
  budget_hours?: number | null
  budget_amount_cents?: number | null
  color?: string | null
}

export interface UpdateProjectDTO extends Partial<CreateProjectDTO> {}

export interface CreateTaskDTO {
  project_id: string
  name: string
  assignee_user_id?: string | null
  estimated_hours?: number | null
  billable_override?: boolean | null
  hourly_rate_cents?: number | null
}

export interface UpdateTaskDTO {
  name?: string
  assignee_user_id?: string | null
  estimated_hours?: number | null
  billable_override?: boolean | null
  hourly_rate_cents?: number | null
}

export interface CreateTagDTO {
  name: string
  color?: string | null
}
