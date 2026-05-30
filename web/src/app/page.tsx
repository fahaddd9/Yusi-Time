import { cookies } from "next/headers"
import { redirect } from "next/navigation"

import { LandingNav } from "@/features/landing/LandingNav"
import { HeroSection } from "@/features/landing/HeroSection"
import { SocialProofStrip } from "@/features/landing/SocialProofStrip"
import { FeaturesSection } from "@/features/landing/FeaturesSection"
import { TimerDemoSection } from "@/features/landing/TimerDemoSection"
import { ComparisonSection } from "@/features/landing/ComparisonSection"
import { FinalCTA } from "@/features/landing/FinalCTA"
import { LandingFooter } from "@/features/landing/LandingFooter"

export default function Home() {
  const cookieStore = cookies()
  const hasRefreshToken = cookieStore.has("refresh_token")

  if (hasRefreshToken) {
    redirect("/dashboard")
  }

  return (
    <div className="min-h-screen bg-background">
      <LandingNav />
      <main>
        <HeroSection />
        <SocialProofStrip />
        <FeaturesSection />
        <TimerDemoSection />
        <ComparisonSection />
        <FinalCTA />
      </main>
      <LandingFooter />
    </div>
  )
}
