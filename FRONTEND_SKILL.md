---
name: yusitime-frontend
description: >
  Activate for ALL frontend work on Yusi Time. Covers creative design
  philosophy, dual-theme system (light + dark), component standards,
  and stack conventions. Stack: Next.js 14 App Router · TypeScript strict ·
  Tailwind CSS 3 (darkMode: 'class') · shadcn/ui · next-themes · lucide-react
  · Framer Motion · TanStack Query v5 · Zustand · React Hook Form + Zod.
---

# Yusi Time — Frontend Skill
## Creative Design Intelligence · Dual Theme System · Code Standards

---

## PART 0 — READ THIS FIRST: THE DESIGN PHILOSOPHY

Before touching a single component, understand what Yusi Time's UI
must *feel* like. This is not a style guide. It is a design philosophy.
Every decision flows from these five principles.

### Principle 1 — Restraint is the skill
The hardest thing in UI design is knowing what NOT to add. Every border,
shadow, color, animation, and label you add costs the user cognitive
attention. Yusi Time users stare at this app for 8 hours a day tracking
their work. Every unnecessary element is friction compounded over a career.

**The test:** Before adding any visual element, ask: "Does removing this
make the UI worse?" If the answer is no, remove it.

### Principle 2 — Typography IS the design
In modern minimal SaaS, typography does the work that decoration used to do.
Size contrast, weight contrast, and letter-spacing create hierarchy. Color
contrast creates emphasis. Monospace numerals create data credibility.
If the typography is doing its job, you need almost no other decoration.

**The signal:** If you find yourself adding borders and backgrounds to
create visual separation, your typography hierarchy is broken. Fix the
typography first.

### Principle 3 — Depth through luminance, not shadows
The old way: add `box-shadow` to make things feel elevated.
The modern way: step up the background lightness value.
Light mode: white → gray-50 → gray-100 as surfaces layer deeper.
Dark mode: zinc-950 → zinc-900 → zinc-800 as surfaces layer deeper.
Depth is a luminance relationship. Shadows are decoration.
**Use shadows only for floating elements** (dropdowns, modals, tooltips)
that genuinely need to communicate "this is above the page."

### Principle 4 — Interactions must be felt, not seen
Micro-interactions in 2026 are not about wow moments. They are about
confidence. When a user stops a timer, they need to feel it happened — not
be dazzled by it. The rounding toast slides up quietly. The stop button
depresses with a 0.95 scale. The timer digit fades to rest. None of these
are visible unless you look for them. All of them are felt.

**The rule:** Every interaction has exactly one moment of feedback.
Not zero (confusing), not two (noisy). One.

### Principle 5 — The interface disappears; the work remains
The best time-tracking UI is the one users stop noticing. When someone opens
Yusi Time, they should see their projects, their time, their approvals — not
the interface. Sidebar, timer bar, navigation: these are scaffolding.
They should recede. The data should lead.

**The test:** Can a new user find their most important information within
3 seconds of loading the dashboard? If not, the hierarchy is wrong.

---

## PART 1 — DUAL THEME SYSTEM

### 1.1 How It Works (Architecture)

shadcn/ui uses CSS variables for all colors. `next-themes` adds/removes
the `dark` class on `<html>`. Tailwind's `darkMode: 'class'` reads that
class. Result: every shadcn component and every Tailwind `dark:` class
flips automatically. Zero per-component theme logic needed.

```
tailwind.config.ts    → darkMode: 'class'
app/layout.tsx        → <ThemeProvider attribute="class" defaultTheme="system">
globals.css           → :root { /* light vars */ } .dark { /* dark vars */ }
components/           → use semantic tokens only, never raw colors
```

### 1.2 Installation Pattern

```tsx
// 1. Install: pnpm add next-themes

// 2. web/src/components/ThemeProvider.tsx
'use client'
import { ThemeProvider as NextThemesProvider } from 'next-themes'
import type { ThemeProviderProps } from 'next-themes'

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
}

// 3. web/src/app/layout.tsx
import { ThemeProvider } from '@/components/ThemeProvider'
export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}

// 4. Theme toggle component
'use client'
import { useTheme } from 'next-themes'
import { Sun, Moon, Monitor } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent,
  DropdownMenuItem, DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'

export function ThemeToggle() {
  const { setTheme } = useTheme()
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Toggle theme">
          <Sun className="w-4 h-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute w-4 h-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => setTheme('light')}>
          <Sun className="w-4 h-4 mr-2" /> Light
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('dark')}>
          <Moon className="w-4 h-4 mr-2" /> Dark
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('system')}>
          <Monitor className="w-4 h-4 mr-2" /> System
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```

### 1.3 The Complete CSS Variable System

This goes in `globals.css`. It defines both themes entirely.
Every color in the app must trace back to one of these variables.
Never use a raw hex color in a component — ever.

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
  /* ── BRAND ─────────────────────────────────── */
  --brand-navy:        #1E2D4B;   /* Logo navy — primary dark */
  --brand-orange:      #F06900;   /* Logo orange — primary accent */
  --brand-orange-hover:#D95E00;   /* Orange darkened 10% for hover */
  --brand-orange-light:#FFF0E6;   /* Orange 6% tint for backgrounds */
  --brand-navy-light:  #EEF1F7;   /* Navy 6% tint for backgrounds */

  /* ── LIGHT THEME ──────────────────────────── */
  --background:        0 0% 99%;         /* #FCFCFC */
  --surface:           0 0% 100%;        /* #FFFFFF cards */
  --surface-raised:    0 0% 97%;         /* #F7F7F7 hover */
  --surface-overlay:   0 0% 94%;         /* #F0F0F0 pressed */
  --card:              var(--surface);
  --card-foreground:   220 47% 18%;      /* navy-ish dark text */
  --popover:           var(--surface);
  --popover-foreground: 220 47% 18%;

  /* Sidebar uses brand navy */
  --sidebar-background: 220 47% 18%;     /* #1E2D4B brand navy */
  --sidebar-foreground: 220 20% 72%;     /* muted blue-gray */
  --sidebar-primary:    24 100% 47%;     /* #F06900 orange */
  --sidebar-active-bg:  rgba(240,105,0,0.12);
  --sidebar-active-border: #F06900;
  --sidebar-accent:     220 40% 22%;     /* slightly lighter navy */
  --sidebar-border:     rgba(255,255,255,0.06);

  /* Brand primary = orange */
  --primary:            24 100% 47%;     /* #F06900 */
  --primary-foreground: 0 0% 100%;       /* white on orange */
  --primary-hover:      24 100% 42%;     /* #D95E00 */
  --primary-muted:      24 100% 95%;     /* #FFF0E6 */

  /* Secondary = navy */
  --secondary:          220 47% 18%;     /* #1E2D4B */
  --secondary-foreground: 0 0% 100%;

  /* Semantic */
  --success:            142 71% 40%;     /* #18A34A */
  --success-muted:      141 79% 93%;
  --warning:            38 92% 50%;      /* #F59E0B */
  --warning-muted:      48 96% 89%;
  --destructive:        0 84% 60%;       /* #EF4444 */
  --destructive-foreground: 0 0% 100%;
  --destructive-muted:  0 86% 94%;

  /* Entry statuses */
  --status-pending:     258 90% 66%;     /* #8B5CF6 violet */
  --status-pending-muted: 258 100% 95%;
  --status-approved:    142 71% 40%;
  --status-approved-muted: 141 79% 93%;
  --status-draft:       220 9% 46%;
  --status-draft-muted: 220 14% 93%;

  /* Text */
  --foreground:         220 47% 18%;     /* #1E2D4B — brand navy as primary text */
  --foreground-2:       220 15% 35%;     /* secondary text */
  --foreground-3:       220 9% 52%;      /* muted text */
  --foreground-4:       220 9% 68%;      /* placeholder */
  --muted:              220 14% 96%;
  --muted-foreground:   220 9% 46%;
  --accent:             220 14% 96%;
  --accent-foreground:  220 47% 18%;

  /* Borders */
  --border:             220 13% 91%;
  --border-strong:      220 9% 80%;
  --input:              220 13% 91%;
  --ring:               24 100% 47%;     /* orange focus ring */
  --radius:             0.625rem;
}

.dark {
  /* Page & surfaces */
  --background:         220 40% 6%;      /* #0C101A  deep navy-black */
  --surface:            220 38% 9%;      /* #121825  card bg */
  --surface-raised:     220 35% 13%;     /* #1A2235  hover */
  --surface-overlay:    220 30% 17%;     /* #222D42  pressed */
  --card:               var(--surface);
  --card-foreground:    0 0% 96%;
  --popover:            220 38% 11%;
  --popover-foreground: 0 0% 96%;

  /* Sidebar stays navy but deeper */
  --sidebar-background: 220 47% 10%;     /* deeper navy */
  --sidebar-foreground: 220 20% 55%;
  --sidebar-primary:    24 100% 52%;     /* slightly brighter orange in dark */
  --sidebar-active-bg:  rgba(240,105,0,0.15);
  --sidebar-active-border: #FF7A1A;
  --sidebar-accent:     220 40% 14%;
  --sidebar-border:     rgba(255,255,255,0.05);

  /* Brand primary */
  --primary:            24 100% 52%;     /* brighter orange in dark */
  --primary-foreground: 0 0% 100%;
  --primary-hover:      24 100% 45%;
  --primary-muted:      24 80% 12%;

  /* Secondary */
  --secondary:          220 35% 20%;
  --secondary-foreground: 0 0% 90%;

  /* Semantic */
  --success:            142 71% 42%;
  --success-muted:      142 60% 10%;
  --warning:            38 92% 50%;
  --warning-muted:      38 80% 10%;
  --destructive:        0 84% 60%;
  --destructive-foreground: 0 0% 100%;
  --destructive-muted:  0 70% 12%;

  /* Entry statuses */
  --status-pending:     258 90% 70%;
  --status-pending-muted: 258 50% 12%;
  --status-approved:    142 71% 45%;
  --status-approved-muted: 142 60% 10%;
  --status-draft:       220 9% 52%;
  --status-draft-muted: 220 30% 14%;

  /* Text */
  --foreground:         0 0% 96%;
  --foreground-2:       220 10% 72%;
  --foreground-3:       220 8% 52%;
  --foreground-4:       220 8% 36%;
  --muted:              220 35% 14%;
  --muted-foreground:   220 10% 52%;
  --accent:             220 35% 14%;
  --accent-foreground:  0 0% 96%;

  /* Borders */
  --border:             220 30% 16%;
  --border-strong:      220 25% 24%;
  --input:              220 30% 16%;
  --ring:               24 100% 52%;
}
}

@layer base {
  * { @apply border-border; }
  body {
    @apply bg-background text-foreground;
    font-feature-settings: "rlig" 1, "calt" 1;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
}
```

### 1.4 Tailwind Config (Required)

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],                    // ← required for next-themes
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Satoshi', 'system-ui', 'sans-serif'],
        mono: ['DM Mono', 'ui-monospace', 'monospace'],
      },
      colors: {
        // Map all CSS variables to Tailwind classes
        background:  'hsl(var(--background))',
        foreground:  'hsl(var(--foreground))',
        surface:     'hsl(var(--surface))',
        'surface-raised': 'hsl(var(--surface-raised))',
        primary: {
          DEFAULT:    'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
          muted:      'hsl(var(--primary-muted))',
        },
        secondary: {
          DEFAULT:    'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        success: {
          DEFAULT: 'hsl(var(--success))',
          muted:   'hsl(var(--success-muted))',
        },
        warning: {
          DEFAULT: 'hsl(var(--warning))',
          muted:   'hsl(var(--warning-muted))',
        },
        destructive: {
          DEFAULT:    'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
          muted:      'hsl(var(--destructive-muted))',
        },
        status: {
          pending:        'hsl(var(--status-pending))',
          'pending-muted':'hsl(var(--status-pending-muted))',
          approved:       'hsl(var(--status-approved))',
          'approved-muted':'hsl(var(--status-approved-muted))',
          draft:          'hsl(var(--status-draft))',
          'draft-muted':  'hsl(var(--status-draft-muted))',
        },
        muted: {
          DEFAULT:    'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        border:  'hsl(var(--border))',
        input:   'hsl(var(--input))',
        ring:    'hsl(var(--ring))',
        card: {
          DEFAULT:    'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        sidebar: {
          DEFAULT:    'hsl(var(--sidebar-background))',
          foreground: 'hsl(var(--sidebar-foreground))',
          primary:    'hsl(var(--sidebar-primary))',
          accent:     'hsl(var(--sidebar-accent))',
          border:     'hsl(var(--sidebar-border))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
export default config
```

---

## PART 2 — CREATIVE DESIGN INTELLIGENCE

### 2.1 The Typography System (Your Primary Design Tool)

```
Font stack:
  UI text  → Satoshi   (clean, geometric, warm — not Inter's cold neutrality)
  Numbers  → DM Mono   (ALL time values, ALL monetary values, ALL durations)

Scale — use exactly these, never invent intermediate sizes:

  Display   text-3xl font-bold tracking-[-0.04em]    30px  — stat card hero numbers
  Heading   text-xl  font-semibold tracking-[-0.03em] 20px  — page titles
  Title     text-base font-semibold tracking-[-0.01em] 16px  — card headings, section titles
  Body      text-sm   font-normal  leading-relaxed    14px  — all body text
  Caption   text-xs   font-normal  text-muted-foreground 12px — metadata, timestamps
  Label     text-[10px] font-medium uppercase tracking-[0.06em] — table headers, section labels

Mono scale:
  Timer hero     font-mono text-3xl font-bold tracking-[-0.02em]
  Stat value     font-mono text-2xl font-bold
  Table duration font-mono text-sm font-medium
  Inline amount  font-mono text-sm text-success-DEFAULT
```

**The typography hierarchy test:** Cover your color system. Does the page
still have clear visual order? If yes, your typography is doing its job.
If no, fix type before adding color.

### 2.2 The Whitespace System (Your Second Design Tool)

Generous whitespace is not wasted space. It is the signal that a product
is confident. Cramped UIs communicate anxiety. Use this 4pt grid:

```
Micro gaps (within components): gap-1 (4px), gap-1.5 (6px), gap-2 (8px)
Component internal padding:     p-3 (12px), p-4 (16px), p-5 (20px)
Card padding:                   p-4 md:p-5 (standard), p-3 (compact tables)
Between cards:                  gap-3 (12px) dense, gap-4 (16px) standard
Page padding:                   px-4 md:px-6 py-4 md:py-6
Section separation:             space-y-4 (16px) standard, space-y-6 (24px) major
Max content width:              max-w-7xl mx-auto
```

**The whitespace rule:** When a layout feels cluttered, double the spacing
before touching anything else. Spacing fixes 80% of "it looks cheap" problems.

### 2.3 Color as Information, Not Decoration

Color in Yusi Time communicates exactly six things. Nothing else.

```
Orange (#F06900) → Primary action, active state, running timer, links
Green  (#22C55E) → Approved status, success state, billable amount, positive trend
Violet (#8B5CF6) → Pending/submitted status only
Amber  (#F59E0B) → Warning, idle state, budget threshold, expiry notice
Red    (#EF4444) → Danger action, rejected status, error state
Gray              → Everything else — editable entries, secondary text, borders
```

**The color test:** Could you explain why each color exists in terms of
information, not aesthetics? If the answer is "it looks nice," remove the color.

Color accents are used sparingly. A page with one orange element has a
more powerful accent than a page with six orange elements. The fewer the
colored elements, the more each one communicates.

### 2.4 Surface & Depth (Without Shadows)

Create depth using luminance steps, not box-shadows.

```
Light mode depth stack:
  Page background:    bg-background    (#FCFCFC) — deepest, lowest
  Card surface:       bg-surface       (#FFFFFF) — one step up
  Hover / secondary:  bg-surface-raised (#F7F7F7) — interactive state
  Table header:       bg-muted         (#F0F0F0) — slight elevation

Dark mode depth stack:
  Page background:    bg-background    (#0F0F10) — deepest
  Card surface:       bg-card          (#16161A) — one step up
  Hover / secondary:  bg-surface-raised (#1F1F24) — interactive
  Elevated (modals):  bg-popover       (#1C1C20) — floating

Shadows — ONLY for floating elements:
  Dropdown/Select:    shadow-md (medium shadow for popover)
  Dialog/Modal:       shadow-xl (strong shadow for modal overlay)
  Toast:              shadow-lg (toast needs to float above content)
  Cards, tables:      NO SHADOW — use border only
  Sidebar:            NO SHADOW — use border-r only
```

### 2.5 Border System

```
Default border (everywhere):
  className="border border-border"
  → light: 1px solid hsl(220 13% 91%)   clean gray
  → dark:  1px solid hsl(240 4% 16%)    near-invisible zinc

Strong border (emphasis, active selected):
  className="border border-border-strong"

Accent border (active nav item, focused input):
  className="border border-primary"
  → adds a colored border edge, no background change needed

Hairline separator (between table rows):
  className="divide-y divide-border"

NEVER use border + shadow together on the same card.
Pick one. Border for structure. Shadow for floating.
```

### 2.6 The Active Navigation State

The sidebar active item pattern is the most visible design signature.
Get it right:

```tsx
// Active nav item — this is the Yusi Time signature
// Left accent bar + subtle tinted background + primary text
className={cn(
  "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors",
  isActive
    ? "bg-primary/10 text-primary border-l-2 border-primary pl-[10px] font-medium"
    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-foreground"
)}

// In dark mode: bg-primary/10 becomes a deep blue tint
// In light mode: bg-primary/10 becomes a soft blue tint
// The border-l-2 accent line is the futuristic touch
```

### 2.7 Status Badges — The Exact Pattern

```tsx
// Use these exact patterns. The rectangular radius (rounded-md not rounded-full)
// is intentional — pills feel dated, rectangles feel modern/technical.

const statusBadge = {
  draft: "bg-status-draft-muted text-status-draft text-[10px] font-medium px-2 py-0.5 rounded-md",
  pending: "bg-status-pending-muted text-status-pending text-[10px] font-medium px-2 py-0.5 rounded-md",
  approved: "bg-status-approved-muted text-status-approved text-[10px] font-medium px-2 py-0.5 rounded-md",
  rejected: "bg-destructive-muted text-destructive text-[10px] font-medium px-2 py-0.5 rounded-md",
  archived: "bg-warning-muted text-warning text-[10px] font-medium px-2 py-0.5 rounded-md",
  // Roles
  admin:   "bg-destructive-muted text-destructive text-[10px] font-medium px-2 py-0.5 rounded-md",
  manager: "bg-warning-muted text-warning text-[10px] font-medium px-2 py-0.5 rounded-md",
  member:  "bg-primary-muted text-primary text-[10px] font-medium px-2 py-0.5 rounded-md",
  viewer:  "bg-status-draft-muted text-status-draft text-[10px] font-medium px-2 py-0.5 rounded-md",
}
```

### 2.8 Interaction Design — Minimal and Purposeful

Every interactive element has exactly these states. No more, no fewer.

```
DEFAULT   → the resting state. Clean, undecorated.
HOVER     → bg shifts one luminance step. Color stays same.
           Use: hover:bg-surface-raised (light) hover:bg-surface-raised (dark)
           Duration: 120ms ease-out. Never longer.
ACTIVE    → subtle scale: active:scale-[0.98]
           Duration: 80ms. Feels immediate and physical.
FOCUS     → ring-2 ring-ring ring-offset-2 ring-offset-background
           Visible focus ring. Never remove this.
DISABLED  → opacity-50 cursor-not-allowed. No other change.
LOADING   → skeleton pulse OR spinner on the button itself.
           Never disable a button during loading without a spinner.
```

**Animation budget:** Each screen gets exactly ONE animated moment.
The timer's pulsing dot. The toast sliding up. The modal scaling in.
Never two animated elements competing for attention simultaneously.

```
Framer Motion timing budget:
  Enter:           opacity 0→1 + y 6→0,  duration: 0.18s, ease: easeOut
  Exit:            opacity 1→0,           duration: 0.12s, ease: easeIn
  Modal scale:     scale 0.96→1,          duration: 0.20s, ease: easeOut
  Toast slide-up:  y 12→0,               duration: 0.22s, ease: easeOut
  List stagger:    staggerChildren 0.04s  (max 5 items staggered)
  Page transition: opacity 0→1,           duration: 0.15s
  
  NEVER animate: width, height, padding, margin, border-radius on hover
  ONLY animate:  opacity, transform (translate, scale, rotate)
  MAX duration:  0.3s for any UI transition
```

### 2.9 Empty States — Design Opportunities, Not Afterthoughts

Empty states are the most neglected screens. They are also the first
thing a new user sees on every section. Design them with care.

```tsx
// Every empty state follows this exact visual hierarchy:
// 1. Icon (lucide, muted color, 40px)
// 2. Heading (title weight, foreground color)
// 3. Description (body, muted-foreground, max 2 lines, max-w-xs)
// 4. CTA button (primary, if action available)

function EmptyState({ icon: Icon, heading, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="w-10 h-10 rounded-xl bg-muted flex items-center justify-center mb-4">
        <Icon className="w-5 h-5 text-muted-foreground" />
      </div>
      <h3 className="text-sm font-semibold text-foreground mb-1">{heading}</h3>
      <p className="text-xs text-muted-foreground max-w-xs leading-relaxed mb-5">
        {description}
      </p>
      {action}
    </div>
  )
}

// The icon sits in a rounded-xl muted box — this gives it weight
// without using color, maintaining the restraint principle.
```

### 2.10 Skeleton Loading — Match the Shape Exactly

Skeletons must be the exact dimensions of the real content.
A mismatched skeleton causes layout shift and destroys perceived quality.

```tsx
// Table row skeleton — matches exact row height of 44px
function TableRowSkeleton() {
  return (
    <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
      <Skeleton className="w-16 h-3" />                    {/* date */}
      <div className="flex items-center gap-2 flex-1">
        <Skeleton className="w-2 h-2 rounded-full" />      {/* color dot */}
        <div className="space-y-1.5">
          <Skeleton className="w-28 h-3" />                {/* project name */}
          <Skeleton className="w-20 h-2.5" />              {/* task name */}
        </div>
      </div>
      <Skeleton className="w-24 h-3" />                    {/* description */}
      <Skeleton className="w-12 h-3" />                    {/* duration */}
      <Skeleton className="w-14 h-4 rounded-md" />         {/* badge */}
    </div>
  )
}
```

---

## PART 3 — COMPONENT STANDARDS (STACK RULES)

### 3.1 File Structure

```
web/src/
├── app/
│   ├── layout.tsx               ← ThemeProvider here
│   ├── (auth)/                  ← public routes
│   └── (app)/
│       ├── layout.tsx           ← AppShell (sidebar + timer bar)
│       └── [all protected pages]
├── components/
│   ├── ui/                      ← shadcn primitives only
│   └── shared/
│       ├── AppShell.tsx         ← layout wrapper
│       ├── Sidebar.tsx
│       ├── TimerBar.tsx
│       ├── ThemeToggle.tsx
│       ├── EmptyState.tsx       ← reusable empty state
│       └── StatusBadge.tsx      ← reusable badge component
├── features/
│   └── [feature]/
│       ├── components/          ← feature-specific components
│       ├── hooks/               ← React Query hooks
│       ├── api.ts               ← typed API calls
│       └── schemas.ts           ← Zod schemas
├── lib/
│   ├── api-client.ts            ← axios instance + interceptors
│   ├── utils.ts                 ← cn(), formatDuration(), formatMoney()
│   └── query-client.ts          ← React Query config
└── stores/
    ├── timer-store.ts           ← Zustand: idle state, UI timer state
    └── ui-store.ts              ← Zustand: sidebar, active modal
```

### 3.2 Never Use Raw Colors

```tsx
// ❌ WRONG — breaks theme switching
className="bg-[#FFFFFF] text-[#111827] border-[#E5E7EB]"
className="bg-white dark:bg-zinc-900"       // hardcoded — fragile

// ✅ CORRECT — theme-aware semantic tokens
className="bg-background text-foreground border-border"
className="bg-card text-card-foreground"
className="text-muted-foreground"
className="bg-primary text-primary-foreground"

// For status colors from CSS variables:
className="text-success-DEFAULT bg-success-muted"
className="text-status-pending bg-status-pending-muted"
```

### 3.3 shadcn Component Map

```
Modal / Dialog          → <Dialog>                (never build modals from scratch)
Dropdown navigation     → <DropdownMenu>
Form select             → <Select>
Searchable picker       → <Command> inside <Popover>  (timer project/task picker)
Toast notifications     → sonner <toast()>          (NOT shadcn Toast)
Tab sections            → <Tabs>
Toggle / switch         → <Switch>
Table                   → <Table> + shadcn primitives
Notification panel      → <Sheet side="right">
Avatar                  → <Avatar> with <AvatarFallback> initials
Progress bar            → <Progress>
Theme toggle            → custom ThemeToggle (§1.2)
All tooltips            → <Tooltip> + <TooltipContent>
All confirmations       → <AlertDialog>             (not window.confirm)
```

### 3.4 Sonner Toast (NOT shadcn Toast)

```tsx
// Install: pnpm add sonner
// In layout.tsx: <Toaster position="bottom-right" />

import { toast } from 'sonner'

// Rounding toast — mandatory after every time entry save
function showRoundingToast(rounding: RoundingResult) {
  const raw = formatDuration(rounding.rawSeconds)
  const rounded = formatDuration(rounding.roundedSeconds)
  const wasRounded = rounding.rawSeconds !== rounding.roundedSeconds

  toast.success(`Saved as ${rounded}`, {
    description: wasRounded
      ? `${raw} → rounded ${rounding.roundingMode} to nearest ${rounding.roundingIntervalMinutes}m`
      : undefined,
    duration: 5000,
  })
}

// Error toast
toast.error('Failed to save entry', { description: error.message })

// Info toast (non-critical)
toast.info('Timer switched to Website Redesign')
```

### 3.5 React Query — Query Factory Pattern

```typescript
// features/timeEntries/hooks/useTimeEntries.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

// Query key factory — typed, centralized
export const timeEntryKeys = {
  all:     (wsId: string) => ['time-entries', wsId] as const,
  current: (wsId: string) => ['time-entries', wsId, 'current'] as const,
  detail:  (id: string)   => ['time-entries', 'detail', id] as const,
}

// Stale times — match data volatility to cache freshness
const STALE = {
  timer:    0,          // always fresh — polled every 5s
  entries:  30_000,     // 30s
  projects: 60_000,     // 1min
  reports:  120_000,    // 2min
  members:  300_000,    // 5min — rarely changes
  settings: 600_000,    // 10min
}

export function useCurrentTimer(workspaceId: string) {
  return useQuery({
    queryKey: timeEntryKeys.current(workspaceId),
    queryFn:  () => timeEntriesApi.current(workspaceId),
    staleTime: STALE.timer,
    refetchInterval: 5_000,
  })
}

export function useStopTimer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: timeEntriesApi.stop,
    onSuccess: (data, { workspaceId }) => {
      // Show rounding toast immediately on success
      showRoundingToast(data.rounding)
      // Invalidate all affected data
      qc.invalidateQueries({ queryKey: ['time-entries', workspaceId] })
      qc.invalidateQueries({ queryKey: ['dashboard', workspaceId] })
    },
  })
}
```

### 3.6 Zustand — Strict Separation

```typescript
// ✅ Zustand is for UI state that the API doesn't know about.
// NEVER store server data in Zustand.

// stores/timer-store.ts — idle detection state
interface TimerStore {
  isIdle: boolean
  idleStartTime: Date | null
  setIdle: (val: boolean, time?: Date) => void
  clearIdle: () => void
}
export const useTimerStore = create<TimerStore>((set) => ({
  isIdle: false, idleStartTime: null,
  setIdle: (isIdle, idleStartTime) => set({ isIdle, idleStartTime }),
  clearIdle: () => set({ isIdle: false, idleStartTime: null }),
}))

// Always use selectors — never subscribe to whole store
const isIdle = useTimerStore(s => s.isIdle)          // ✅
const store = useTimerStore()                          // ❌
```

### 3.7 TypeScript — Non-Negotiable Rules

```typescript
// strict: true in tsconfig. These are the daily rules:

// No any — ever
const x: any = ...        // ❌ forbidden

// Explicit prop interfaces on every component
interface Props {          // ✅
  workspaceId: string
  onStop?: (id: string) => void
}

// Discriminated unions for status
type EntryStatus = 'draft' | 'running' | 'pending' | 'approved'

// cn() for ALL conditional class merging
import { cn } from '@/lib/utils'
className={cn('base', condition && 'extra', className)}  // ✅
className={`base ${condition ? 'extra' : ''}`}           // ❌

// Named exports everywhere except Next.js pages
export function MyComponent() {}    // ✅
export default function MyComponent() {}  // ❌ (except pages)
```

---

## PART 4 — YUSI TIME BUSINESS RULES IN UI

These rules are correctness requirements, not style preferences.
Violating them is a bug, not a design opinion.

### Rule 1 — Viewer Data Isolation
Financial fields must be ABSENT from the DOM for Viewer role.
Not hidden. Not `opacity-0`. Not `invisible`. **Not rendered.**

```tsx
// The API omits the fields. The component must not render the column.
{role !== 'viewer' && (
  <TableCell className="font-mono text-sm text-success-DEFAULT">
    {entry.billableAmount}
  </TableCell>
)}
// Fields to gate: billableAmount, hourlyRate, totalBillableAmount,
// budgetAmount, defaultHourlyRate, currency values
```

### Rule 2 — Entry Lock States
```typescript
// Entries are locked (read-only for non-Admin) when:
// status === 'pending'  → submitted, awaiting approval
// status === 'approved' → permanently locked
// Admin role → NEVER locked (always show full controls)

// Disabled icon button pattern:
<button
  disabled={isLocked && role !== 'admin'}
  className={cn(
    "p-1.5 rounded-md transition-colors",
    isLocked && role !== 'admin'
      ? "opacity-30 cursor-not-allowed"
      : "text-muted-foreground hover:text-foreground hover:bg-surface-raised"
  )}
  title={isLocked ? "Entry is locked" : "Edit entry"}
  aria-label={isLocked ? "Edit entry (locked)" : "Edit entry"}
>
  <Pencil className="w-3.5 h-3.5" />
</button>
```

### Rule 3 — Submit Week Button
```tsx
// Always disabled with tooltip explanation when no qualifying entries
<Tooltip>
  <TooltipTrigger asChild>
    <span tabIndex={!hasEntries ? 0 : undefined}>
      <Button disabled={!hasEntries} onClick={onSubmit}>
        Submit Week {hasEntries && `(${count})`}
      </Button>
    </span>
  </TooltipTrigger>
  {!hasEntries && (
    <TooltipContent>No unlocked entries to submit this week</TooltipContent>
  )}
</Tooltip>
```

### Rule 4 — Invite Button (Admin Only)
```tsx
// Does not exist in the DOM for any role except Admin
{role === 'admin' && (
  <Button onClick={onInvite}>
    <UserPlus className="w-4 h-4 mr-2" />
    Invite Member
  </Button>
)}
```

### Rule 5 — Idle Modal (Cannot Be Dismissed)
```tsx
<Dialog open={isIdle} onOpenChange={() => {}}>
  <DialogContent
    onPointerDownOutside={e => e.preventDefault()}
    onEscapeKeyDown={e => e.preventDefault()}
    className="sm:max-w-sm [&>button]:hidden"  // hides shadcn's default X button
  >
    {/* Three options only. No close. No escape. */}
  </DialogContent>
</Dialog>
```

### Rule 6 — Rounding Toast (Mandatory)
Every timer stop, manual entry save, and entry edit must call
`showRoundingToast(rounding)` with the API's rounding response.
See §3.4 for implementation.

### Rule 7 — Role-Conditional Navigation
```tsx
const NAV = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['admin','manager','member','viewer'] },
  { href: '/timesheet', label: 'Timesheet',  icon: CalendarClock,   roles: ['admin','manager','member','viewer'] },
  { href: '/projects',  label: 'Projects',   icon: FolderOpen,      roles: ['admin','manager','member','viewer'] },
  { href: '/reports',   label: 'Reports',    icon: BarChart2,       roles: ['admin','manager','member','viewer'] },
  { href: '/approvals', label: 'Approvals',  icon: CheckSquare,     roles: ['admin','manager'] },
  { href: '/settings',  label: 'Settings',   icon: Settings,        roles: ['admin','manager','member','viewer'] },
] as const

// Filter before rendering — Approvals never appears for Member/Viewer
const visible = NAV.filter(item => item.roles.includes(userRole))
```

### Rule 8 — Super Admin UI Gating

The `is_superadmin` boolean is returned in every `GET /users/me` response via
the `UserPublic` schema. The frontend uses this flag to gate two things:

**1. The Super Admin nav link in the main app Sidebar:**
```tsx
// ABSENT from DOM for all non-super-admin users — not hidden
{currentUser?.is_superadmin && (
  <Link href="/superadmin">...</Link>
)}
```

**2. The entire `/superadmin` route tree:**
The `app/superadmin/layout.tsx` component checks `is_superadmin` on mount.
If `false`, it redirects to `/dashboard` immediately. This is the primary
authorization gate for all Super Admin pages.

**What NOT to do:**
```tsx
// ❌ Hidden instead of absent
<Link href="/superadmin" className={isSuper ? '' : 'hidden'}>

// ❌ Disabled instead of absent
<Link href="/superadmin" onClick={e => !isSuper && e.preventDefault()}>

// ❌ Checking role instead of flag
{member.role === 'superadmin' && ...}  // 'superadmin' is never a workspace role

// ✅ Correct — absent from DOM
{currentUser?.is_superadmin && <Link href="/superadmin">...</Link>}
```

**Super Admin UI is only built in Phase 7.5.** Do not create any file under
`web/src/app/superadmin/` before Phase 7.5 begins and is approved.
The `is_superadmin` field is present in `UserPublic` from Phase 1.5 onward
but no component reads it until Phase 7.5.

---

## PART 5 — MANDATORY COMPONENT STATES

Every data-driven component must implement all four before it is complete.

```tsx
// The pattern — apply to every component that fetches data
function TimeEntryList({ workspaceId }) {
  const { data, isLoading, isError, error, refetch } = useTimeEntries(workspaceId)

  // 1. LOADING — skeleton that matches real content shape
  if (isLoading) return <TimeEntryListSkeleton />

  // 2. ERROR — message + retry
  if (isError) return (
    <div className="flex flex-col items-center py-10 gap-3">
      <AlertCircle className="w-8 h-8 text-destructive" />
      <p className="text-sm text-muted-foreground">{error.message}</p>
      <Button variant="outline" size="sm" onClick={() => refetch()}>
        Try again
      </Button>
    </div>
  )

  // 3. EMPTY — icon + heading + description + CTA
  if (!data?.length) return (
    <EmptyState
      icon={Clock}
      heading="No time entries yet"
      description="Start a timer or add a manual entry to begin tracking your work."
      action={<Button size="sm" onClick={onStartTimer}>Start Timer</Button>}
    />
  )

  // 4. DATA — the real content
  return <TimeEntryTable entries={data} />
}
```

---

## PART 6 — ACCESSIBILITY (NON-NEGOTIABLE)

```
Contrast requirements:
  Body text on background:     minimum 4.5:1 (WCAG AA)
  Large text / headings:       minimum 3:1
  text-foreground on bg:       ✅ passes in both themes
  text-muted-foreground on bg: check each theme — muted gray can fail on light

Focus rings — never remove:
  All interactive elements: focus-visible:ring-2 focus-visible:ring-ring
                            focus-visible:ring-offset-2 focus-visible:outline-none
  shadcn components handle this automatically

Icon-only buttons — always need aria-label:
  <Button variant="ghost" size="icon" aria-label="Edit entry">
    <Pencil className="w-4 h-4" />
  </Button>

Keyboard navigation:
  Tab order follows visual left-to-right, top-to-bottom flow
  All modals trap focus (shadcn Dialog handles via Radix)
  Dropdowns close on Escape (shadcn handles — do NOT prevent this,
  EXCEPT for the Idle Detection Modal which explicitly prevents Escape)

Reduced motion:
  Wrap Framer Motion in MotionConfig in root layout:
  <MotionConfig reducedMotion="user">{children}</MotionConfig>
```

---

## PART 7 — PERFORMANCE

```typescript
// Server vs Client — push 'use client' as deep as possible
// Page layouts → Server Component (no directive)
// Data + interaction → Client Component ('use client')

// Never import barrel files — import directly
import { Button } from '@/components/ui/button'      // ✅
import { Button } from '@/components/ui'             // ❌

// Parallel data fetching — never waterfall
const [projects, members] = await Promise.all([
  fetchProjects(workspaceId),
  fetchMembers(workspaceId),
])

// Lazy-load heavy feature pages
const ReportPage = dynamic(() => import('@/features/reports/ReportPage'), {
  loading: () => <ReportPageSkeleton />,
})

// Virtualize long lists (detailed report, time entries > 50 rows)
// Use @tanstack/react-virtual
```

---

## PART 8 — PRE-DELIVERY CHECKLIST

Before marking any component done, verify every item:

**Design Quality**
- [ ] Typography: DM Mono on ALL time and money values
- [ ] Colors: only semantic tokens used (no raw hex, no dark: hardcoding)
- [ ] Whitespace: generous, consistent with the 4pt grid
- [ ] One primary (orange) button per view maximum
- [ ] Interactions: exactly one animated moment per screen
- [ ] Both themes checked: open browser in light, switch to dark, verify nothing breaks

**Business Rules**
- [ ] Viewer: financial fields absent from DOM (not hidden)
- [ ] Locked entries: edit/delete disabled with tooltip
- [ ] Submit Week: disabled with tooltip when no qualifying entries
- [ ] Invite: renders only for Admin role
- [ ] Idle modal: no X button, no backdrop dismiss, no Escape
- [ ] Rounding toast: fires on every save

**Code Quality**
- [ ] No `any` types
- [ ] All forms: React Hook Form + Zod
- [ ] All API data: React Query (no direct fetch in components)
- [ ] All UI state: Zustand (no server data in Zustand)
- [ ] All icons: lucide-react only
- [ ] All interactive components: shadcn primitives
- [ ] All class merging: cn() utility
- [ ] Named exports (not default) for all non-page components

**States**
- [ ] Loading skeleton (matches real content shape)
- [ ] Empty state (icon + heading + description + CTA)
- [ ] Error state (message + retry button)
- [ ] Disabled state (opacity-50, cursor-not-allowed)

**Accessibility**
- [ ] Focus rings visible on all interactive elements
- [ ] Icon-only buttons have aria-label
- [ ] Tab navigation works without mouse
- [ ] prefers-reduced-motion respected (MotionConfig in root)

---

## PART 9 — DO NOT USE LIST

Never introduce these regardless of what other resources suggest:

```
❌ Any icon library except lucide-react
❌ Headless UI (replaced by shadcn)
❌ Redux or Context for server state (use React Query)
❌ SWR (use React Query)
❌ Direct fetch() or axios in components (use api-client.ts)
❌ localStorage for tokens (in-memory + HttpOnly cookie)
❌ shadcn Toast (use sonner)
❌ Raw hex colors in components (#FFFFFF, #111827 etc)
❌ dark: class hardcoded without semantic token
❌ Box shadows on cards or sidebars
❌ Rounded-full pill badges (use rounded-md)
❌ Inter or Roboto fonts (use Satoshi)
❌ Purple gradients
❌ Animations over 0.3s
❌ Animating width, height, padding on hover
❌ Multiple primary-color elements competing per screen
❌ @ts-ignore without written justification comment
❌ Default exports on non-page components
❌ Barrel imports from @/components/ui
❌ window.confirm() for confirmations (use AlertDialog)
❌ Inline styles (use Tailwind classes)
❌ Dark mode out of scope — both themes are required
❌ `'superadmin'` as a value in workspace role checks, role enums, or role comparisons
❌ `className="hidden"` to hide Super Admin UI from non-super-admin users (use conditional rendering)
❌ Any file under `web/src/app/superadmin/` before Phase 7.5 is approved
❌ Reading `is_superadmin` from anywhere other than the `GET /users/me` response (`UserPublic`)
```
