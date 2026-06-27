"use client"

import * as React from "react"
import { motion, HTMLMotionProps, Variants } from "framer-motion"
import { cn } from "@/lib/utils"

export interface ScrollRevealProps extends HTMLMotionProps<"div"> {
  children: React.ReactNode
  /** Delay in seconds before animation starts. */
  delay?: number
  /** Duration of the animation in seconds. Default is 0.4. */
  duration?: number
  /** Stagger index, useful when rendering a list of items to cascade them. Multiplies by delay/base step. */
  staggerIndex?: number
  /** Define from which direction it slides. 'bottom' means it slides up from bottom. */
  direction?: "bottom" | "top" | "left" | "right" | "none"
  /** The distance to slide in pixels. */
  distance?: number
  /** Whether the animation should trigger only once or every time it enters view. */
  once?: boolean
}

const directionOffsets = {
  bottom: { y: 20, x: 0 },
  top: { y: -20, x: 0 },
  left: { x: -20, y: 0 },
  right: { x: 20, y: 0 },
  none: { x: 0, y: 0 },
}

export function ScrollReveal({
  children,
  className,
  delay = 0,
  duration = 0.5,
  staggerIndex = 0,
  direction = "bottom",
  distance = 30,
  once = true,
  ...props
}: ScrollRevealProps) {
  const baseOffset = directionOffsets[direction]
  
  const variants: Variants = {
    hidden: {
      opacity: 0,
      x: baseOffset.x ? (baseOffset.x > 0 ? distance : -distance) : 0,
      y: baseOffset.y ? (baseOffset.y > 0 ? distance : -distance) : 0,
      scale: 0.98,
    },
    visible: {
      opacity: 1,
      x: 0,
      y: 0,
      scale: 1,
      transition: {
        duration,
        ease: [0.16, 1, 0.3, 1], // Custom springy ease-out
        delay: delay + staggerIndex * 0.08,
      },
    },
  }

  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once, amount: 0.1 }}
      variants={variants}
      className={cn("w-full", className)}
      {...props}
    >
      {children}
    </motion.div>
  )
}
