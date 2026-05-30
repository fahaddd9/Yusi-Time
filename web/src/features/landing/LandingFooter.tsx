"use client"

import Link from "next/link"
import { ThemeToggle } from "@/components/ThemeToggle"

export function LandingFooter() {
  return (
    <footer className="bg-[#0A0F1A] text-slate-400 py-12 border-t border-white/5">
      <div className="container mx-auto px-4 md:px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
          <div className="col-span-2 md:col-span-1 space-y-4">
            <Link href="/" className="flex items-center gap-2">
              <div className="inline-flex items-center justify-center w-6 h-6 rounded-md bg-brand-orange">
                <span className="text-white font-bold text-xs font-mono">Y</span>
              </div>
              <span className="text-lg font-bold tracking-tight text-white">
                Yusi<span className="text-brand-orange">Time</span>
              </span>
            </Link>
            <p className="text-sm">
              The time tracker that doesn't feel like a time tracker.
            </p>
          </div>
          
          <div>
            <h4 className="text-white font-semibold mb-4">Product</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="#features" className="hover:text-white transition-colors">Features</Link></li>
              <li><Link href="#pricing" className="hover:text-white transition-colors">Pricing</Link></li>
              <li><Link href="/login" className="hover:text-white transition-colors">Sign in</Link></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-white font-semibold mb-4">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="#" className="hover:text-white transition-colors">Documentation</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">API Reference</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Blog</Link></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-white font-semibold mb-4">Legal</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="#" className="hover:text-white transition-colors">Privacy Policy</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Terms of Service</Link></li>
            </ul>
          </div>
        </div>
        
        <div className="pt-8 border-t border-white/10 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm">
            © {new Date().getFullYear()} Yusi Time Inc. All rights reserved.
          </p>
          <div className="flex items-center gap-4">
            <span className="text-sm">Theme:</span>
            <ThemeToggle />
          </div>
        </div>
      </div>
    </footer>
  )
}
