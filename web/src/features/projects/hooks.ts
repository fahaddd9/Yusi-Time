import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { projectsApi } from "./api"
import { useWorkspaceStore } from "@/stores/workspace-store"
import { 
  CreateClientDTO, UpdateClientDTO, 
  CreateProjectDTO, UpdateProjectDTO, 
  CreateTaskDTO, UpdateTaskDTO, 
  CreateTagDTO 
} from "./types"

// --- CLIENTS ---
export function useClients() {
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useQuery({
    queryKey: ["clients", workspaceId],
    queryFn: () => projectsApi.listClients(workspaceId!).then(res => res.data),
    enabled: !!workspaceId,
  })
}

export function useCreateClient() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useMutation({
    mutationFn: (data: CreateClientDTO) => projectsApi.createClient(workspaceId!, data).then(res => res.data.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["clients", workspaceId] })
    }
  })
}

export function useUpdateClient() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useMutation({
    mutationFn: ({ id, data }: { id: string, data: UpdateClientDTO }) => 
      projectsApi.updateClient(workspaceId!, id, data).then(res => res.data.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["clients", workspaceId] })
      queryClient.invalidateQueries({ queryKey: ["projects", workspaceId] }) // in case client name changes
    }
  })
}

export function useDeleteClient() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useMutation({
    mutationFn: (id: string) => projectsApi.deleteClient(workspaceId!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["clients", workspaceId] })
      queryClient.invalidateQueries({ queryKey: ["projects", workspaceId] })
    }
  })
}

// --- PROJECTS ---
export function useProjects(params?: { status?: string; client_id?: string }) {
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useQuery({
    queryKey: ["projects", workspaceId, params],
    queryFn: () => projectsApi.listProjects(workspaceId!, params).then(res => res.data),
    enabled: !!workspaceId,
  })
}

export function useProject(projectId: string | undefined) {
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useQuery({
    queryKey: ["projects", workspaceId, projectId],
    queryFn: () => projectsApi.getProject(workspaceId!, projectId!).then(res => res.data.data),
    enabled: !!workspaceId && !!projectId,
  })
}

export function useCreateProject() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useMutation({
    mutationFn: (data: CreateProjectDTO) => projectsApi.createProject(workspaceId!, data).then(res => res.data.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", workspaceId] })
    }
  })
}

export function useUpdateProject() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useMutation({
    mutationFn: ({ id, data }: { id: string, data: UpdateProjectDTO }) => 
      projectsApi.updateProject(workspaceId!, id, data).then(res => res.data.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["projects", workspaceId] })
      queryClient.invalidateQueries({ queryKey: ["projects", workspaceId, variables.id] })
    }
  })
}

export function useArchiveProject() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useMutation({
    mutationFn: (id: string) => projectsApi.archiveProject(workspaceId!, id).then(res => res.data.data),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["projects", workspaceId] })
      queryClient.invalidateQueries({ queryKey: ["projects", workspaceId, id] })
    }
  })
}

export function useDeleteProject() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useMutation({
    mutationFn: (id: string) => projectsApi.deleteProject(workspaceId!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", workspaceId] })
    }
  })
}

// --- PROJECT MEMBERS ---
export function useProjectMembers(projectId: string | undefined) {
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useQuery({
    queryKey: ["projects", workspaceId, projectId, "members"],
    queryFn: () => projectsApi.listProjectMembers(workspaceId!, projectId!).then(res => res.data.data),
    enabled: !!workspaceId && !!projectId,
  })
}

export function useAddProjectMember() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useMutation({
    mutationFn: ({ projectId, userId }: { projectId: string, userId: string }) => 
      projectsApi.addProjectMember(workspaceId!, projectId, userId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["projects", workspaceId, variables.projectId, "members"] })
    }
  })
}

export function useRemoveProjectMember() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useMutation({
    mutationFn: ({ projectId, userId }: { projectId: string, userId: string }) => 
      projectsApi.removeProjectMember(workspaceId!, projectId, userId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["projects", workspaceId, variables.projectId, "members"] })
    }
  })
}

// --- TASKS ---
export function useTasks(projectId: string | undefined) {
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useQuery({
    queryKey: ["tasks", workspaceId, projectId],
    queryFn: () => projectsApi.listTasks(workspaceId!, projectId!).then(res => res.data),
    enabled: !!workspaceId && !!projectId,
  })
}

export function useCreateTask() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useMutation({
    mutationFn: (data: CreateTaskDTO) => projectsApi.createTask(workspaceId!, data).then(res => res.data.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["tasks", workspaceId, variables.project_id] })
    }
  })
}

export function useUpdateTask() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useMutation({
    mutationFn: ({ id, data, projectId }: { id: string, data: UpdateTaskDTO, projectId: string }) => 
      projectsApi.updateTask(workspaceId!, id, data).then(res => res.data.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["tasks", workspaceId, variables.projectId] })
    }
  })
}

export function useDeleteTask() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useMutation({
    mutationFn: ({ id, projectId }: { id: string, projectId: string }) => projectsApi.deleteTask(workspaceId!, id),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["tasks", workspaceId, variables.projectId] })
    }
  })
}

// --- TAGS ---
export function useTags() {
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useQuery({
    queryKey: ["tags", workspaceId],
    queryFn: () => projectsApi.listTags(workspaceId!).then(res => res.data.data),
    enabled: !!workspaceId,
  })
}

export function useCreateTag() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useMutation({
    mutationFn: (data: CreateTagDTO) => projectsApi.createTag(workspaceId!, data).then(res => res.data.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags", workspaceId] })
    }
  })
}

export function useUpdateTag() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useMutation({
    mutationFn: ({ id, data }: { id: string, data: Partial<CreateTagDTO> }) => 
      projectsApi.updateTag(workspaceId!, id, data).then(res => res.data.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags", workspaceId] })
    }
  })
}

export function useDeleteTag() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  return useMutation({
    mutationFn: (id: string) => projectsApi.deleteTag(workspaceId!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags", workspaceId] })
    }
  })
}
