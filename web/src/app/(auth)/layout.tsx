import { ThemeToggle } from "@/components/ThemeToggle"

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4 relative overflow-hidden">
      {/* Subtle dot grid background */}
      <div
        className="absolute inset-0 opacity-[0.025]"
        style={{
          backgroundImage: "radial-gradient(circle, hsl(var(--foreground)) 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />
      {/* Orange glow blob — top right */}
      <div className="absolute top-0 right-0 w-[400px] h-[400px] rounded-full bg-brand-orange/5 blur-[80px] pointer-events-none" />
      {/* Navy glow blob — bottom left */}
      <div className="absolute bottom-0 left-0 w-[300px] h-[300px] rounded-full bg-brand-navy/10 blur-[80px] pointer-events-none dark:bg-brand-orange/5" />

      {/* Theme toggle — top right corner */}
      <div className="absolute top-4 right-4 z-20">
        <ThemeToggle />
      </div>

      {/* Auth card slot */}
      <div className="relative z-10 w-full max-w-[420px]">
        {children}
      </div>
    </div>
  )
}
