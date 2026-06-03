import { apiClient } from "@/lib/api-client"
import { 
  Client, Project, Task, Tag, 
  CreateClientDTO, UpdateClientDTO, 
  CreateProjectDTO, UpdateProjectDTO, 
  CreateTaskDTO, UpdateTaskDTO, 
  CreateTagDTO 
} from "./types"

export const projectsApi = {
  // Clients
  listClients: async (workspaceId: string) => {
    return apiClient.get<{ data: Client[], total: number }>(`/clients`, { params: { workspace_id: workspaceId } })
  },
  createClient: async (workspaceId: string, data: CreateClientDTO) => {
    return apiClient.post<{ data: Client }>(`/clients`, data, { params: { workspace_id: workspaceId } })
  },
  updateClient: async (workspaceId: string, clientId: string, data: UpdateClientDTO) => {
    return apiClient.patch<{ data: Client }>(`/clients/${clientId}`, data, { params: { workspace_id: workspaceId } })
  },
  deleteClient: async (workspaceId: string, clientId: string) => {
    return apiClient.delete(`/clients/${clientId}`, { params: { workspace_id: workspaceId } })
  },

  // Projects
  listProjects: async (workspaceId: string, params?: { status?: string; client_id?: string }) => {
    return apiClient.get<{ data: Project[], total: number }>(`/projects`, { 
      params: { workspace_id: workspaceId, ...params } 
    })
  },
  getProject: async (workspaceId: string, projectId: string) => {
    return apiClient.get<{ data: Project }>(`/projects/${projectId}`, { params: { workspace_id: workspaceId } })
  },
  createProject: async (workspaceId: string, data: CreateProjectDTO) => {
    return apiClient.post<{ data: Project }>(`/projects`, data, { params: { workspace_id: workspaceId } })
  },
  updateProject: async (workspaceId: string, projectId: string, data: UpdateProjectDTO) => {
    return apiClient.patch<{ data: Project }>(`/projects/${projectId}`, data, { params: { workspace_id: workspaceId } })
  },
  archiveProject: async (workspaceId: string, projectId: string) => {
    return apiClient.post<{ data: Project }>(`/projects/${projectId}/archive`, {}, { params: { workspace_id: workspaceId } })
  },
  deleteProject: async (workspaceId: string, projectId: string) => {
    return apiClient.delete(`/projects/${projectId}`, { params: { workspace_id: workspaceId } })
  },
  
  // Project Members
  listProjectMembers: async (workspaceId: string, projectId: string) => {
    return apiClient.get<{ data: any[] }>(`/projects/${projectId}/members`, { params: { workspace_id: workspaceId } })
  },
  addProjectMember: async (workspaceId: string, projectId: string, userId: string) => {
    return apiClient.post(`/projects/${projectId}/members`, { user_id: userId }, { params: { workspace_id: workspaceId } })
  },
  removeProjectMember: async (workspaceId: string, projectId: string, userId: string) => {
    return apiClient.delete(`/projects/${projectId}/members/${userId}`, { params: { workspace_id: workspaceId } })
  },

  // Tasks
  listTasks: async (workspaceId: string, projectId: string) => {
    return apiClient.get<{ data: Task[], total: number }>(`/tasks`, { params: { workspace_id: workspaceId, project_id: projectId } })
  },
  createTask: async (workspaceId: string, data: CreateTaskDTO) => {
    return apiClient.post<{ data: Task }>(`/tasks`, data, { params: { workspace_id: workspaceId } })
  },
  updateTask: async (workspaceId: string, taskId: string, data: UpdateTaskDTO) => {
    return apiClient.patch<{ data: Task }>(`/tasks/${taskId}`, data, { params: { workspace_id: workspaceId } })
  },
  deleteTask: async (workspaceId: string, taskId: string) => {
    return apiClient.delete(`/tasks/${taskId}`, { params: { workspace_id: workspaceId } })
  },

  // Tags
  listTags: async (workspaceId: string) => {
    return apiClient.get<{ data: Tag[] }>(`/tags`, { params: { workspace_id: workspaceId } })
  },
  createTag: async (workspaceId: string, data: CreateTagDTO) => {
    return apiClient.post<{ data: Tag }>(`/tags`, data, { params: { workspace_id: workspaceId } })
  },
  updateTag: async (workspaceId: string, tagId: string, data: Partial<CreateTagDTO>) => {
    return apiClient.patch<{ data: Tag }>(`/tags/${tagId}`, data, { params: { workspace_id: workspaceId } })
  },
  deleteTag: async (workspaceId: string, tagId: string) => {
    return apiClient.delete(`/tags/${tagId}`, { params: { workspace_id: workspaceId } })
  }
}
