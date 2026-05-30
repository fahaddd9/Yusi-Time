"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Play, Square, Tag, Folder } from "lucide-react"

function formatTime(seconds: number) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`
}

export function TimerDemoSection() {
  const [isRunning, setIsRunning] = useState(false)
  const [seconds, setSeconds] = useState(0)
  const [entries, setEntries] = useState<{ id: number; duration: number }[]>([])

  useEffect(() => {
    let interval: NodeJS.Timeout
    if (isRunning) {
      interval = setInterval(() => setSeconds(s => s + 1), 1000)
    }
    return () => clearInterval(interval)
  }, [isRunning])

  const handleToggle = () => {
    if (isRunning) {
      if (seconds > 0) {
        setEntries(prev => [{ id: Date.now(), duration: seconds }, ...prev])
      }
      setSeconds(0)
    }
    setIsRunning(!isRunning)
  }

  return (
    <section id="demo" className="py-24 bg-brand-navy-light dark:bg-brand-navy/20">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground">
            Tracking time should take 1 second.
          </h2>
          <p className="text-lg text-muted-foreground">
            Try it yourself. No required fields. No friction. Just click play and get back to work.
          </p>
        </div>

        <div className="max-w-2xl mx-auto">
          {/* Active Timer UI */}
          <div className="bg-card border border-border rounded-xl shadow-lg p-4 flex flex-col sm:flex-row items-center gap-4 transition-all">
            <input 
              type="text" 
              placeholder="What are you working on?" 
              className="flex-1 bg-transparent border-none outline-none text-foreground placeholder:text-muted-foreground px-2 h-10 w-full"
              readOnly
            />
            
            <div className="flex items-center gap-2 text-muted-foreground">
              <button className="p-2 hover:bg-muted rounded-md transition-colors" title="Project">
                <Folder className="w-4 h-4" />
              </button>
              <button className="p-2 hover:bg-muted rounded-md transition-colors" title="Tag">
                <Tag className="w-4 h-4" />
              </button>
            </div>

            <div className="flex items-center gap-4 w-full sm:w-auto justify-between sm:justify-end border-t sm:border-t-0 border-border pt-4 sm:pt-0">
              <span className={`font-mono text-2xl font-semibold w-[120px] text-right transition-colors ${isRunning ? 'text-brand-orange' : 'text-foreground'}`}>
                {formatTime(seconds)}
              </span>
              <button 
                onClick={handleToggle}
                className={`w-12 h-12 flex items-center justify-center rounded-full text-white transition-all transform active:scale-95 shadow-md ${
                  isRunning 
                    ? "bg-destructive hover:bg-destructive/90 hover:shadow-destructive/20" 
                    : "bg-brand-orange hover:bg-brand-orange-hover hover:shadow-brand-orange/20"
                }`}
              >
                {isRunning ? <Square className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-1" />}
              </button>
            </div>
          </div>

          {/* Past Entries */}
          <div className="mt-8 space-y-2">
            <AnimatePresence>
              {entries.map((entry) => (
                <motion.div
                  key={entry.id}
                  initial={{ opacity: 0, height: 0, y: -20 }}
                  animate={{ opacity: 1, height: "auto", y: 0 }}
                  className="bg-card border border-border rounded-lg p-4 flex justify-between items-center overflow-hidden"
                >
                  <div className="text-foreground">Landing Page Design</div>
                  <div className="font-mono text-muted-foreground">{formatTime(entry.duration)}</div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  )
}
