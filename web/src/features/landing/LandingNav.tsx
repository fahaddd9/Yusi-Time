"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import Image from "next/image"
import { useTheme } from "next-themes"
import { Button, buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { ThemeToggle } from "@/components/ThemeToggle"

export function LandingNav() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [mounted, setMounted] = useState(false)
  const { resolvedTheme } = useTheme()

  useEffect(() => {
    setMounted(true)
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 80)
    }
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  const useDarkAppearance = !mounted ? true : (!isScrolled || resolvedTheme === 'dark')

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? "bg-background/95 backdrop-blur-md border-b border-border shadow-sm py-3"
          : "bg-transparent py-5"
      }`}
    >
      <div className="container mx-auto px-4 md:px-6 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <Image 
            src={useDarkAppearance ? "/logo-dark.svg" : "/logo-light.svg"} 
            alt="Yusi Time" 
            width={120} 
            height={32} 
            priority
          />
        </Link>

        <div className="flex items-center gap-4">
          <ThemeToggle className={useDarkAppearance ? "text-white hover:text-gray-200 hover:bg-white/10" : "text-slate-900 hover:text-slate-700"} />
          <Link 
            href="/login" 
            className={cn(
              buttonVariants({ variant: "ghost" }), 
              "hidden sm:inline-flex hover:bg-transparent",
              useDarkAppearance ? "text-white hover:text-gray-200" : "text-slate-900 hover:text-slate-700"
            )}
          >
            Sign in
          </Link>
          <Link href="/signup" className={cn(buttonVariants({ variant: "default" }), "bg-brand-orange hover:bg-brand-orange-hover text-white shadow-sm hover:shadow transition-all")}>
            Start Free
          </Link>
        </div>
      </div>
    </nav>
  )
}
