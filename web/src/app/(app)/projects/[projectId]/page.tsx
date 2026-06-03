import { ProjectDetailClient } from "@/features/projects/components/ProjectDetailClient"

export default function ProjectDetailPage({ params }: { params: { projectId: string } }) {
  return <ProjectDetailClient projectId={params.projectId} />
}
