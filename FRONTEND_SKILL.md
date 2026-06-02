---
name: yusitime-frontend
version: 3.0 (Designer Edition)
description: >
  The complete design intelligence document for Yusi Time. This is not a
  style guide — it is the mind of the designer. Read every word before writing
  a single line of code. Covers: visual philosophy, brand identity, logo usage,
  color architecture, typography, spacing, animation, component anatomy,
  interaction patterns, page-by-page design decisions, and the exact Tailwind
  implementation for every element. Aligned with PRD v1.3 · TRD v1.2 ·
  DB Schema v2.2 · API Spec v1.1 · UI/UX Blueprint v2.0.
stack: >
  Next.js 14 App Router · TypeScript strict · Tailwind CSS 3 (darkMode:class)
  · shadcn/ui · next-themes · lucide-react · Framer Motion · TanStack Query v5
  · Zustand · React Hook Form + Zod · DM Sans · DM Mono
---

---

# PART 0 — THE DESIGNER'S MIND: READ THIS FIRST

Before writing code, you must understand HOW a great designer thinks. This
section is the most important part of the document. Technical specs follow
naturally from design thinking. Code without this thinking produces "functional
but forgettable" UIs. Code with this thinking produces something users stop
and admire.

---

## 0.1 — The Tasko Principle: What Makes It Feel Premium

Study the Tasko dashboard and its sisters (UXBooster, VetCRM). What separates
them from generic dashboards? It is not the features. It is these five things:

**1. Every surface has a story.**
Tasko's stat cards are not just boxes with numbers. They have an icon container
in a tinted background, a bold mono number, a descriptive label, and a subtle
upward-trend indicator. Each element earns its space. Nothing is padding filler.
When you build a stat card for Yusi Time, ask: what is the story of this number?

**2. Color is rationed like expensive paint.**
Tasko uses its accent color (typically a warm tone) on exactly: the active nav
item, the primary CTA button, badge highlights, and progress bars. Everywhere
else is neutral. This restraint makes every orange element on Yusi Time feel
like a spotlight, not decoration. The rule: if orange appears more than twice
on a page, one of those uses is wrong.

**3. Whitespace is not emptiness — it is breathing room.**
VetCRM uses generous padding inside cards (p-5 or p-6), wide gutters between
sections (gap-4 or gap-6), and tall rows (h-14 minimum for table rows). This
creates the "premium SaaS" feeling. Cramped layouts communicate anxiety.
Generous layouts communicate confidence.

**4. Motion is physical, not decorative.**
The best micro-interactions feel like touching something real. A button press
has a tiny scale-down (0.97). A modal appears with a scale-up from 0.96 to 1.0.
A toast slides up from below. These movements are 150–250ms. They do not call
attention to themselves. Users feel them without seeing them.

**5. Feedback is instant and clear.**
When a user stops a timer, they need to feel it immediately. The button changes
state. A toast appears. The timer resets. If any of these are delayed by even
200ms, the user doubts whether it worked. Design all state transitions to appear
instantaneous even when API calls are in-flight (optimistic UI).

---

## 0.2 — Yusi Time's Specific Aesthetic Identity

Yusi Time is a **professional time-tracking tool for serious people**. It is not
playful. It is not corporate. It is the intersection of:

- **The precision of a stopwatch** — clean, monospace numbers, crisp lines
- **The warmth of a boutique agency** — navy + orange is energetic yet trustworthy
- **The minimalism of modern SaaS** — no gradients for decoration, no shadows on
  cards, no decorative borders

The single adjective that describes the Yusi Time aesthetic: **Confident**.
Not flashy. Not timid. Confident. Every decision should pass the test:
"Does this feel confident, or does it feel like it's trying too hard?"

---

## 0.3 — The Three Questions Before Every Component

Before building any component, answer these three questions:

1. **What is the user trying to accomplish on this screen?**
   If it is "track time," the Start Timer button must be the most visually
   dominant element. If it is "review members," the member list must load fast
   with clear role distinctions. Design follows intent.

2. **What state will this component most commonly be in?**
   A timesheet grid is usually full of entries. A new workspace has empty states.
   Design the most common state first. The empty state is secondary (but still
   important — it is what new users see first).

3. **What is the one thing the user should be able to do in 2 seconds?**
   On the Dashboard: see today's hours. On Timesheet: see the week at a glance.
   On Settings: find the specific setting they need. Every page has a "2-second
   task." Make sure that task requires zero visual searching.

---

# PART 1 — BRAND IDENTITY & LOGO SYSTEM

## 1.1 — The Logo Files

Two official logo files exist. Use them exactly as provided:

| File | Usage Context |
|------|--------------|
| `logo-dark.svg` | Dark sidebar, dark backgrounds, anywhere the bg is dark |
| `logo-light.svg` | Light page backgrounds, white cards, light headers |

**Never recreate the logo in code.** Never use a text "YT" abbreviation as a
logo substitute. Never apply filters, shadows, or transforms to the logo SVG.
Use it as-is via `<img src="/logo-dark.svg" />` or as an inlined SVG component.

**Logo anatomy (from SVG analysis):**
- Left: A detailed illustrative stopwatch icon. In `logo-dark.svg`, the icon
  fills are white + orange (`#fe6900`). In `logo-light.svg`, the icon fills
  are navy `#252f50` + orange `#fe6900`.
- Right: "YUSI" wordmark followed by "TIME" inside a rounded-rectangle border
  frame. The "TIME" word and its enclosing frame are always orange `#fe6900`.
- In `logo-dark.svg`: "YUSI" is white. In `logo-light.svg`: "YUSI" is navy.

**Logo sizing:**
```
Sidebar (compact): height: 32px, width: auto
Page headers: height: 28px, width: auto  
Auth pages: height: 40px, width: auto
Landing hero: height: 48px, width: auto
Favicon / tiny: Use stopwatch icon mark only, never the full wordmark
```

**Logo placement:**
```tsx
// In sidebar header — always use dark logo variant on navy bg
<img src="/logo-dark.svg" alt="Yusi Time" className="h-8 w-auto" />

// In auth pages (light bg) — use light logo variant
<img src="/logo-light.svg" alt="Yusi Time" className="h-10 w-auto" />
```

---

## 1.2 — The Exact Brand Colors (From Logo SVG Analysis)

The brand orange extracted directly from the SVG files is `#fe6900`.
Note: this is `#FE6900` not `#F06900`. Use the exact value below.

```css
/* AUTHORITATIVE BRAND VALUES — extracted from logo SVG */
--brand-orange:       #FE6900;   /* Logo orange — PRIMARY ACCENT */
--brand-orange-hover: #E55E00;   /* 10% darker for hover states */
--brand-orange-light: #FFF3EA;   /* 6% tint for bg highlights */
--brand-navy:         #252F50;   /* Logo navy — from logo-light.svg st0 fill */
--brand-navy-light:   #EEF0F6;   /* Navy 6% tint */
```

**Why this matters:** `#FE6900` is slightly redder and more vibrant than
`#F06900`. On screen, especially in dark mode, it reads warmer and more alive.
Using the wrong hex creates a subtle but persistent visual dissonance.

---

# PART 2 — THE COMPLETE CSS VARIABLE SYSTEM

This is the authoritative color system. Every single color in the application
must trace back to one of these variables. Zero raw hex values in components.

```css
/* web/src/styles/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* ── BRAND (always the same, theme-independent) ─── */
    --brand-orange:        #FE6900;
    --brand-orange-hover:  #E55E00;
    --brand-orange-light:  #FFF3EA;
    --brand-navy:          #252F50;
    --brand-navy-light:    #EEF0F6;

    /* ── LIGHT THEME SURFACES ────────────────────────── */
    --background:          0 0% 98.5%;      /* #FBFBFB — off-white, not pure white */
    --surface:             0 0% 100%;       /* #FFFFFF — card bg */
    --surface-raised:      220 14% 97%;     /* #F7F8FA — hover, alternating rows */
    --surface-overlay:     220 14% 94%;     /* #EDEEF2 — active/pressed */
    --card:                var(--surface);
    --card-foreground:     220 47% 15%;
    --popover:             0 0% 100%;
    --popover-foreground:  220 47% 15%;

    /* ── SIDEBAR (always brand navy) ────────────────── */
    --sidebar-background:  220 35% 23%;     /* #252F50 brand navy */
    --sidebar-foreground:  220 20% 68%;     /* muted blue-gray text */
    --sidebar-primary:     24 100% 50%;     /* #FE6900 orange */
    --sidebar-accent:      220 35% 28%;     /* lighter navy for hover */
    --sidebar-border:      220 35% 28%;     /* subtle separator */

    /* ── PRIMARY = ORANGE ────────────────────────────── */
    --primary:             24 100% 50%;     /* #FE6900 */
    --primary-foreground:  0 0% 100%;
    --primary-hover:       24 100% 45%;     /* #E55E00 */
    --primary-muted:       24 100% 95%;     /* #FFF3EA */

    /* ── SECONDARY = NAVY ────────────────────────────── */
    --secondary:           220 35% 23%;     /* #252F50 */
    --secondary-foreground: 0 0% 100%;

    /* ── SEMANTIC COLORS ─────────────────────────────── */
    --success:             142 71% 38%;     /* #16A34A */
    --success-muted:       142 76% 93%;     /* #DCFCE7 */
    --success-foreground:  142 71% 38%;

    --warning:             38 92% 50%;      /* #F59E0B */
    --warning-muted:       48 96% 89%;      /* #FEF9C3 */
    --warning-foreground:  38 92% 50%;

    --destructive:         0 84% 60%;       /* #EF4444 */
    --destructive-foreground: 0 0% 100%;
    --destructive-muted:   0 86% 94%;       /* #FEE2E2 */

    /* ── ENTRY STATUS COLORS ─────────────────────────── */
    --status-running:      24 100% 50%;     /* orange — same as primary */
    --status-running-muted: 24 100% 95%;
    --status-draft:        220 9% 46%;      /* neutral gray */
    --status-draft-muted:  220 14% 94%;
    --status-pending:      258 90% 66%;     /* #8B5CF6 violet */
    --status-pending-muted: 258 100% 96%;   /* #F5F3FF */
    --status-approved:     142 71% 38%;     /* green */
    --status-approved-muted: 142 76% 93%;

    /* ── TEXT HIERARCHY ──────────────────────────────── */
    --foreground:          220 47% 15%;     /* #1C2540 — near-navy primary text */
    --foreground-2:        220 15% 35%;     /* secondary text */
    --foreground-3:        220 9% 52%;      /* tertiary / muted text */
    --foreground-4:        220 9% 70%;      /* placeholder */
    --muted:               220 14% 96%;
    --muted-foreground:    220 9% 46%;
    --accent:              220 14% 96%;
    --accent-foreground:   220 47% 15%;

    /* ── BORDERS & INPUTS ────────────────────────────── */
    --border:              220 13% 90%;     /* default border */
    --border-strong:       220 13% 80%;     /* emphasized border */
    --input:               220 13% 90%;
    --ring:                24 100% 50%;     /* orange focus ring */
    --radius:              0.625rem;        /* 10px default border-radius */
  }

  .dark {
    /* ── DARK THEME SURFACES ─────────────────────────── */
    --background:          222 28% 7%;      /* #0D1117 — deep blue-black */
    --surface:             222 25% 11%;     /* #151C28 — card bg */
    --surface-raised:      222 22% 15%;     /* #1C2535 — hover */
    --surface-overlay:     222 20% 19%;     /* #242E42 — active */
    --card:                var(--surface);
    --card-foreground:     0 0% 94%;
    --popover:             222 25% 13%;
    --popover-foreground:  0 0% 94%;

    /* ── SIDEBAR (deeper navy in dark) ──────────────── */
    --sidebar-background:  222 35% 8%;      /* very deep navy */
    --sidebar-foreground:  220 20% 55%;
    --sidebar-primary:     24 100% 55%;     /* slightly brighter orange */
    --sidebar-accent:      222 28% 13%;
    --sidebar-border:      222 28% 14%;

    /* ── PRIMARY = ORANGE (brighter in dark) ─────────── */
    --primary:             24 100% 55%;     /* slightly brighter in dark */
    --primary-foreground:  0 0% 100%;
    --primary-hover:       24 100% 48%;
    --primary-muted:       24 70% 13%;      /* dark orange tint */

    /* ── SECONDARY ───────────────────────────────────── */
    --secondary:           222 25% 18%;
    --secondary-foreground: 0 0% 92%;

    /* ── SEMANTIC (adjusted for dark) ───────────────── */
    --success:             142 71% 42%;
    --success-muted:       142 60% 9%;
    --warning:             38 92% 50%;
    --warning-muted:       38 80% 9%;
    --destructive:         0 84% 60%;
    --destructive-foreground: 0 0% 100%;
    --destructive-muted:   0 70% 11%;

    /* ── ENTRY STATUS (dark adjusted) ───────────────── */
    --status-draft:        220 9% 50%;
    --status-draft-muted:  222 25% 14%;
    --status-pending:      258 90% 70%;
    --status-pending-muted: 258 50% 11%;
    --status-approved:     142 71% 45%;
    --status-approved-muted: 142 60% 9%;

    /* ── TEXT (dark) ─────────────────────────────────── */
    --foreground:          0 0% 94%;
    --foreground-2:        220 10% 70%;
    --foreground-3:        220 8% 50%;
    --foreground-4:        220 8% 35%;
    --muted:               222 25% 15%;
    --muted-foreground:    220 10% 50%;
    --accent:              222 25% 15%;
    --accent-foreground:   0 0% 94%;

    /* ── BORDERS (dark) ──────────────────────────────── */
    --border:              222 25% 18%;
    --border-strong:       222 22% 26%;
    --input:               222 25% 18%;
    --ring:                24 100% 55%;
  }
}

@layer base {
  * {
    @apply border-border;
    box-sizing: border-box;
  }
  body {
    @apply bg-background text-foreground;
    font-feature-settings: "rlig" 1, "calt" 1, "ss01" 1;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
  }
  /* Smooth scrolling everywhere */
  html {
    scroll-behavior: smooth;
  }
  /* Custom scrollbar — thin and brand-colored */
  ::-webkit-scrollbar { width: 5px; height: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb {
    background: hsl(var(--border-strong));
    border-radius: 99px;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: hsl(var(--primary) / 0.5);
  }
}
```

---

# PART 3 — TAILWIND CONFIGURATION

```typescript
// web/tailwind.config.ts — COMPLETE configuration
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
        mono: ['DM Mono', 'ui-monospace', 'Menlo', 'monospace'],
      },
      fontSize: {
        // These are the ONLY font sizes permitted in the app
        'display':  ['1.875rem', { lineHeight: '1.1', letterSpacing: '-0.04em', fontWeight: '700' }],
        'heading':  ['1.25rem',  { lineHeight: '1.3', letterSpacing: '-0.03em', fontWeight: '600' }],
        'title':    ['1rem',     { lineHeight: '1.4', letterSpacing: '-0.01em', fontWeight: '600' }],
        'body':     ['0.875rem', { lineHeight: '1.6', fontWeight: '400' }],
        'caption':  ['0.75rem',  { lineHeight: '1.5', fontWeight: '400' }],
        'label':    ['0.625rem', { lineHeight: '1.4', letterSpacing: '0.06em', fontWeight: '500' }],
        // Mono scale
        'mono-hero':  ['1.875rem', { lineHeight: '1.1', letterSpacing: '-0.02em', fontWeight: '700' }],
        'mono-stat':  ['1.5rem',   { lineHeight: '1.2', letterSpacing: '-0.02em', fontWeight: '700' }],
        'mono-table': ['0.875rem', { lineHeight: '1.4', fontWeight: '500' }],
        'mono-sm':    ['0.75rem',  { lineHeight: '1.4', fontWeight: '500' }],
      },
      colors: {
        brand: {
          orange:       '#FE6900',
          'orange-hover': '#E55E00',
          'orange-light': '#FFF3EA',
          navy:         '#252F50',
          'navy-light':  '#EEF0F6',
        },
        background:  'hsl(var(--background))',
        foreground:  'hsl(var(--foreground))',
        surface:     'hsl(var(--surface))',
        'surface-raised': 'hsl(var(--surface-raised))',
        'surface-overlay': 'hsl(var(--surface-overlay))',
        primary: {
          DEFAULT:    'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
          hover:      'hsl(var(--primary-hover))',
          muted:      'hsl(var(--primary-muted))',
        },
        secondary: {
          DEFAULT:    'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        success: {
          DEFAULT:    'hsl(var(--success))',
          muted:      'hsl(var(--success-muted))',
          foreground: 'hsl(var(--success-foreground))',
        },
        warning: {
          DEFAULT:    'hsl(var(--warning))',
          muted:      'hsl(var(--warning-muted))',
          foreground: 'hsl(var(--warning-foreground))',
        },
        destructive: {
          DEFAULT:    'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
          muted:      'hsl(var(--destructive-muted))',
        },
        status: {
          running:          'hsl(var(--status-running))',
          'running-muted':  'hsl(var(--status-running-muted))',
          draft:            'hsl(var(--status-draft))',
          'draft-muted':    'hsl(var(--status-draft-muted))',
          pending:          'hsl(var(--status-pending))',
          'pending-muted':  'hsl(var(--status-pending-muted))',
          approved:         'hsl(var(--status-approved))',
          'approved-muted': 'hsl(var(--status-approved-muted))',
        },
        muted: {
          DEFAULT:    'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        border:  'hsl(var(--border))',
        'border-strong': 'hsl(var(--border-strong))',
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
        xl:  '0.875rem',   /* 14px — cards */
        lg:  'var(--radius)',  /* 10px — default */
        md:  'calc(var(--radius) - 2px)', /* 8px */
        sm:  'calc(var(--radius) - 4px)', /* 6px */
        xs:  '4px',            /* badges, chips */
      },
      boxShadow: {
        /* Cards — subtle elevation without Airbnb-era shadows */
        'card':  '0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.04)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.05)',
        /* Floating elements — dropdowns, modals */
        'float': '0 8px 24px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.08)',
        /* Orange glow — primary CTA only */
        'orange-glow': '0 4px 14px rgba(254,105,0,0.30)',
        'orange-glow-lg': '0 6px 20px rgba(254,105,0,0.40)',
        /* Inset for active states */
        'inset-orange': 'inset 0 0 0 1.5px rgba(254,105,0,0.40)',
        /* Dark mode variants */
        'card-dark': '0 1px 3px rgba(0,0,0,0.20), 0 1px 2px rgba(0,0,0,0.15)',
        'float-dark': '0 8px 24px rgba(0,0,0,0.40), 0 2px 8px rgba(0,0,0,0.25)',
      },
      animation: {
        'timer-pulse': 'timer-pulse 2s ease-in-out infinite',
        'fade-in':     'fade-in 0.18s ease-out',
        'slide-up':    'slide-up 0.22s ease-out',
        'scale-in':    'scale-in 0.20s ease-out',
        'spin-slow':   'spin 3s linear infinite',
      },
      keyframes: {
        'timer-pulse': {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.4' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to:   { opacity: '1' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        'scale-in': {
          from: { opacity: '0', transform: 'scale(0.96)' },
          to:   { opacity: '1', transform: 'scale(1)' },
        },
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
export default config
```

---

# PART 4 — TYPOGRAPHY: THE DESIGN SYSTEM'S BACKBONE

Typography does the work that decoration used to do. Get this right and
you need almost nothing else.

## 4.1 — The Scale (Non-Negotiable)

```
DISPLAY     font-sans text-display      30px  -0.04em  700  → Stat card hero numbers
HEADING     font-sans text-heading      20px  -0.03em  600  → Page titles, section headers
TITLE       font-sans text-title        16px  -0.01em  600  → Card headings, group labels
BODY        font-sans text-body         14px  normal   400  → All body text, descriptions
CAPTION     font-sans text-caption      12px  normal   400  → Metadata, timestamps, helper text
LABEL       font-sans text-label        10px  +0.06em  500  → Table headers (UPPERCASE)

MONO HERO   font-mono text-mono-hero    30px  -0.02em  700  → Running timer display
MONO STAT   font-mono text-mono-stat    24px  -0.02em  700  → Stat card values
MONO TABLE  font-mono text-mono-table   14px  normal   500  → Duration columns, amounts
MONO SMALL  font-mono text-mono-sm      12px  normal   500  → Inline badges, meta values
```

**The golden rule of Yusi Time typography:**
Every number that represents time, money, or quantity MUST be `font-mono`.
This means:
- `5h 30m` → `font-mono`
- `$1,250.00` → `font-mono text-success`
- `42 entries` → the `42` must be `font-mono`
- `85%` progress → the `85` must be `font-mono`
- Every column in a data table with numeric values → `font-mono`

Non-numeric text (names, descriptions, labels) → always `font-sans`.

## 4.2 — Text Color Hierarchy

```tsx
// PRIMARY — main content, headings
className="text-foreground"

// SECONDARY — supporting text, subtitles
className="text-foreground-2"   // does not exist as a token — use:
className="text-muted-foreground"

// TERTIARY — helper text, metadata, timestamps
className="text-muted-foreground text-caption"

// PLACEHOLDER — empty inputs
className="placeholder:text-foreground-4"

// ACCENT — links, active labels
className="text-primary"   // i.e., brand-orange

// SUCCESS — positive values, approved states, money
className="text-success"

// DANGER — errors, destructive actions
className="text-destructive"
```

## 4.3 — Heading Patterns (Exact Implementations)

```tsx
// Page title (used in every page header)
<h1 className="text-heading font-semibold tracking-tight text-foreground">
  Dashboard
</h1>

// Section title within a card
<h2 className="text-title font-semibold text-foreground">
  Top Projects
</h2>

// Card stat value — THE most important number on any card
<span className="font-mono text-mono-stat font-bold text-foreground tabular-nums">
  5h 30m
</span>

// Table header label — always uppercase, always tracking-wider
<th className="text-label font-medium uppercase tracking-wider text-muted-foreground">
  DURATION
</th>

// Timestamp or helper text
<span className="text-caption text-muted-foreground">
  2 hours ago
</span>
```

---

# PART 5 — SPATIAL SYSTEM: THE 4PT GRID

All spacing follows a strict 4pt grid. The following values are the only
permitted spacing values. No `p-7`, no `mt-3.5`, no irregular values.

```
4px  → gap-1, p-1, m-1    (micro: icon to label, chip internal)
8px  → gap-2, p-2, m-2    (small: icon button padding, tag padding)
12px → gap-3, p-3, m-3    (compact: tight table rows, small cards)
16px → gap-4, p-4, m-4    (standard: card padding, form fields)
20px → gap-5, p-5, m-5    (comfortable: main card padding)
24px → gap-6, p-6, m-6    (spacious: page section gaps)
32px → gap-8, p-8, m-8    (large: major section separators)
48px → gap-12, py-12      (hero sections)
```

**Card padding rule:** Always `p-4` for compact cards (stat cards, small widgets).
Always `p-5` for content cards (member lists, settings sections). Always `p-6`
for hero-level containers (landing sections, primary content areas).

**Page padding rule:** Always `px-6 py-6` on the main content area inside
the app shell. Never `px-4` for the main content — that is for mobile only.

---

# PART 6 — COMPONENT ANATOMY: THE DESIGNER'S COOKBOOK

Every component has a precise recipe. Follow these exactly.

## 6.1 — Stat Cards (Dashboard, Reports)

Stat cards are the most visible elements on data pages. They must feel premium.

```tsx
// The anatomy of a perfect Yusi Time stat card
function StatCard({
  label, value, unit, delta, icon: Icon, iconColor = 'text-primary'
}: StatCardProps) {
  return (
    <div className={cn(
      "bg-surface rounded-xl border border-border p-4",
      "hover:border-border-strong hover:shadow-card-hover",
      "transition-all duration-200 ease-out",
      "group"
    )}>
      {/* Header: label + icon */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-label uppercase tracking-wider text-muted-foreground font-medium">
          {label}
        </span>
        {/* Icon container — tinted background, always consistent */}
        <div className={cn(
          "w-8 h-8 rounded-lg flex items-center justify-center",
          "bg-primary/8 group-hover:bg-primary/12 transition-colors duration-200"
        )}>
          <Icon className={cn("w-4 h-4", iconColor)} />
        </div>
      </div>

      {/* Main value — the hero of the card */}
      <div className="flex items-baseline gap-1.5 mb-1">
        <span className="font-mono text-mono-stat font-bold text-foreground tabular-nums">
          {value}
        </span>
        {unit && (
          <span className="text-caption text-muted-foreground font-sans">{unit}</span>
        )}
      </div>

      {/* Delta indicator */}
      {delta && (
        <div className={cn(
          "flex items-center gap-1 text-caption font-medium",
          delta.positive ? "text-success" : "text-destructive"
        )}>
          {delta.positive ? (
            <TrendingUp className="w-3 h-3" />
          ) : (
            <TrendingDown className="w-3 h-3" />
          )}
          <span>{delta.label}</span>
        </div>
      )}
    </div>
  )
}
```

**Designer notes for stat cards:**
- The icon container must always be `w-8 h-8 rounded-lg` — not `rounded-xl`,
  not `rounded-full`. The slight corner rounding is deliberate: it matches the
  card's border-radius hierarchy.
- The icon color inside is ALWAYS `text-primary` (orange) unless it is a
  destructive metric (then `text-destructive`). Green/success icons are for
  money-positive metrics only.
- The delta row uses a tiny `TrendingUp`/`TrendingDown` icon at `w-3 h-3`.
  This is the smallest lucide icon should ever appear in the app.
- Hover: the card border gets slightly stronger and a subtle shadow lifts it.
  This 200ms transition makes the card feel "alive" without being distracting.

## 6.2 — The Sidebar (The App's Spine)

The sidebar is the most-seen element in the entire app. It must be
flawless in both light and dark modes.

```tsx
// Active nav item — the Yusi Time signature
const navItemClass = (isActive: boolean) => cn(
  "flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm",
  "transition-all duration-150 ease-out cursor-pointer",
  "select-none",
  isActive
    ? [
        "bg-primary/10 text-white font-medium",
        "border-l-[2.5px] border-primary pl-[10px]",  // 2.5px left border accent
        "shadow-[inset_0_0_0_0.5px_rgba(254,105,0,0.12)]" // extremely subtle inner glow
      ]
    : [
        "text-sidebar-foreground",
        "hover:bg-sidebar-accent hover:text-white",
        "active:scale-[0.98]"  // physical press feedback
      ]
)

// The left-border accent is THE visual signature of Yusi Time's navigation.
// It must ALWAYS be present on the active item. Never use background alone.
// The combination of: tinted bg + white text + orange left border = perfect.
```

**Designer notes for sidebar:**
- The sidebar background is ALWAYS `bg-[hsl(var(--sidebar-background))]` —
  which maps to the deep navy. Never override this.
- Section labels like "WORKSPACE" and "SETTINGS" are `text-label` (10px),
  `uppercase`, `tracking-wider`, `text-sidebar-foreground/40` — they should
  barely be visible, acting as organizational landmarks, not visual elements.
- The workspace switcher at the top (below the logo) shows the workspace name
  in `text-caption text-sidebar-foreground/60` with a `ChevronDown` at `w-3 h-3`.
  On hover, the row gets a subtle `hover:bg-sidebar-accent` background.
- The user footer at the bottom gets `border-t border-sidebar-border` separator.
  Avatar at `w-7 h-7`, name in `text-caption text-sidebar-foreground/60`,
  ThemeToggle as ghost icon-only, logout icon-only.

## 6.3 — The TimerBar (The App's Pulse)

The TimerBar is the heartbeat of Yusi Time. It sits at the top of every
protected page. When the timer is running, the entire bar should feel ALIVE.

```
HEIGHT: h-[52px] — slightly taller than standard nav for breathing room
BACKGROUND: bg-surface border-b border-border
SHADOW: none — the border-b is sufficient separation
```

**State-based color system for the elapsed display:**
```tsx
// NOT running
<span className="font-mono text-mono-table font-semibold text-muted-foreground tabular-nums">
  00:00:00
</span>

// RUNNING — this is THE most important colored text in the app
<span className="font-mono text-mono-table font-semibold text-primary tabular-nums animate-none">
  {elapsed}
</span>

// IDLE — user has been away, timer is still running
<span className="font-mono text-mono-table font-semibold text-warning tabular-nums">
  {elapsed}
</span>
```

**The running indicator dot:**
```tsx
// Appears left of the elapsed time when running
{isRunning && (
  <span className="w-2 h-2 rounded-full bg-primary animate-timer-pulse" />
)}
```

**Start/Stop button specification:**
```tsx
// START button — the primary action of the entire app
<Button
  className={cn(
    "h-8 px-4 text-sm font-semibold rounded-lg",
    "bg-primary hover:bg-primary-hover text-white",
    "shadow-orange-glow hover:shadow-orange-glow-lg",  // the glow is what makes it premium
    "transition-all duration-150",
    "active:scale-[0.97] active:shadow-none"  // physical press
  )}
>
  <Play className="w-3.5 h-3.5 mr-1.5 fill-current" />
  Start
</Button>

// STOP button
<Button
  className={cn(
    "h-8 px-4 text-sm font-semibold rounded-lg",
    "bg-destructive hover:bg-destructive/90 text-destructive-foreground",
    "transition-all duration-150",
    "active:scale-[0.97]"
  )}
>
  <Square className="w-3.5 h-3.5 mr-1.5 fill-current" />
  Stop
</Button>
```

**The orange glow shadow on the Start button is MANDATORY.** It is what
elevates it from "a button" to "the primary action". Without the glow,
the TimerBar looks like any generic form. With it, the user's eye immediately
finds the most important action.

## 6.4 — Data Tables

Tables are where users spend most of their time in Yusi Time. They must be
scannable, comfortable, and interactive.

```
ROW HEIGHT:          h-[52px] for data rows (48px minimum)
HEADER HEIGHT:       h-[40px]
HEADER BG:           bg-surface-raised
ROW HOVER:           hover:bg-surface-raised transition-colors duration-100
BORDER:              divide-y divide-border (row separators)
COLUMN PADDING:      px-4 (standard), px-3 (compact)
```

**Designer decision — no outer border on tables:**
Use only `divide-y divide-border` between rows. No outer border on the table
container (the card wrapper provides that). This creates a cleaner, more
editorial look.

**Financial columns (non-viewer):**
```tsx
<TableCell className="font-mono text-mono-table text-success tabular-nums text-right">
  $125.00
</TableCell>
```

**Duration columns (everyone):**
```tsx
<TableCell className="font-mono text-mono-table text-foreground tabular-nums text-right">
  2h 15m
</TableCell>
```

**The `text-right` + `tabular-nums` combination is non-negotiable for numeric
columns.** Numbers that shift left-right as they update create visual instability.
`tabular-nums` ensures equal character widths so the column stays locked.

## 6.5 — Badges and Status Indicators

Status badges carry significant information density. Design them precisely.

```tsx
// The StatusBadge component — use this pattern for ALL status indicators
const statusConfig = {
  draft: {
    className: "bg-status-draft-muted text-status-draft",
    label: "Draft"
  },
  running: {
    className: "bg-status-running-muted text-primary",
    label: "Running"
  },
  pending: {
    className: "bg-status-pending-muted text-status-pending",
    label: "Pending"
  },
  approved: {
    className: "bg-status-approved-muted text-status-approved",
    label: "Approved"
  },
}

// Role badges
const roleConfig = {
  admin:   { className: "bg-primary/8 text-primary border border-primary/20", label: "Admin" },
  manager: { className: "bg-warning-muted text-warning-foreground", label: "Manager" },
  member:  { className: "bg-muted text-muted-foreground", label: "Member" },
  viewer:  { className: "bg-muted text-muted-foreground", label: "Viewer" },
}

// The badge itself
<span className={cn(
  "inline-flex items-center px-2 py-0.5",
  "text-[10px] font-medium",
  "rounded-[4px]",          // xs radius — rectangular, not pill-shaped
  statusConfig[status].className
)}>
  {statusConfig[status].label}
</span>
```

**Why `rounded-[4px]` not `rounded-full`?** Pill-shaped badges look dated
and make everything feel like a tag. Rectangular badges with minimal radius
look technical, precise, and modern — which is exactly what Yusi Time is.

## 6.6 — Form Fields and Settings Rows

The settings pages were identified as a weak point in the current implementation.
This spec fixes that permanently.

**Settings Row Pattern (Vercel-style horizontal layout):**
```tsx
// Each setting is a horizontal row with label on left, control on right
// This is COMPLETELY DIFFERENT from the vertical stacking in the current build
function SettingRow({
  label,
  description,
  children,
  disabled = false
}: SettingRowProps) {
  return (
    <div className={cn(
      "flex items-start justify-between gap-6 py-4",
      "border-b border-border last:border-b-0"
    )}>
      {/* Left: label + description */}
      <div className="flex-1 min-w-0 max-w-sm">
        <p className={cn(
          "text-body font-medium text-foreground",
          disabled && "text-muted-foreground"
        )}>
          {label}
        </p>
        {description && (
          <p className="text-caption text-muted-foreground mt-0.5 leading-relaxed">
            {description}
          </p>
        )}
      </div>

      {/* Right: the control */}
      <div className="flex-shrink-0">
        {children}
      </div>
    </div>
  )
}

// Usage:
<SettingRow
  label="Rounding Mode"
  description="How timer durations are rounded when saving entries."
>
  <Select value={rounding} onValueChange={setRounding}>
    {/* options */}
  </Select>
</SettingRow>

<SettingRow
  label="Idle Detection"
  description="Auto-pause timer when user has been inactive."
>
  <Switch
    checked={idleEnabled}
    onCheckedChange={setIdleEnabled}
    className="data-[state=checked]:bg-primary"
  />
</SettingRow>
```

**Why this matters:** The current build stacks everything vertically, creating
a generic "form" look. The horizontal layout creates clear visual columns —
labels on the left (what it does), controls on the right (how to change it).
This is how Linear, Vercel, and Stripe build their settings.

**Input focus states — THE critical detail:**
```tsx
// Every text input and select must have this focus treatment
className={cn(
  "h-9 rounded-lg border border-input bg-background px-3 text-body",
  "transition-all duration-150",
  // Focus: border color shifts to orange, subtle ring
  "focus:outline-none focus:border-primary focus:ring-2",
  "focus:ring-primary/15 focus:ring-offset-0",
  // Hover: border gets slightly darker
  "hover:border-border-strong",
)}
```

The ring is `primary/15` not `primary/30` — very subtle. Just enough to
show the field is active without dominating the visual. This subtlety is
what separates "designed" from "default shadcn."

## 6.7 — The Idle Modal (Zero-Dismiss)

Per PRD §3.4 and AGENT.md §11: The idle modal CANNOT be dismissed.
Here is the complete implementation pattern:

```tsx
<Dialog open={isIdle} onOpenChange={() => {}}>
  <DialogContent
    className="sm:max-w-[380px] [&>button]:hidden"
    onPointerDownOutside={(e) => e.preventDefault()}
    onEscapeKeyDown={(e) => e.preventDefault()}
  >
    {/* Visual indicator — amber pulsing icon */}
    <div className="flex flex-col items-center text-center pt-2 pb-1">
      <div className="w-14 h-14 rounded-2xl bg-warning-muted flex items-center justify-center mb-4">
        <Clock className="w-7 h-7 text-warning animate-timer-pulse" />
      </div>
      <DialogTitle className="text-title font-semibold text-foreground">
        You've been idle
      </DialogTitle>
      <DialogDescription className="text-body text-muted-foreground mt-1">
        No activity for {idleMinutes} {idleMinutes === 1 ? 'minute' : 'minutes'}.
        Your timer is still running.
      </DialogDescription>
    </div>

    {/* Three options — vertical stack, clearly differentiated */}
    <div className="flex flex-col gap-2 mt-2">
      {/* Option 1: Keep & Continue — subtle, least consequential */}
      <Button
        variant="outline"
        className="w-full justify-start gap-3 h-11 text-body"
        onClick={onKeepAndContinue}
      >
        <Play className="w-4 h-4 text-primary" />
        <div className="text-left">
          <div className="font-medium">Keep time & continue</div>
          <div className="text-[11px] text-muted-foreground font-normal">
            Count idle time as work
          </div>
        </div>
      </Button>

      {/* Option 2: Discard & Stop */}
      <Button
        variant="outline"
        className="w-full justify-start gap-3 h-11 text-body hover:border-destructive/40 hover:text-destructive"
        onClick={onDiscardAndStop}
      >
        <Square className="w-4 h-4" />
        <div className="text-left">
          <div className="font-medium">Discard idle & stop</div>
          <div className="text-[11px] text-muted-foreground font-normal">
            Save entry at {format(idleStartTime, 'h:mm a')}
          </div>
        </div>
      </Button>

      {/* Option 3: Discard & Continue — primary action, most common */}
      <Button
        className={cn(
          "w-full justify-start gap-3 h-11 text-body",
          "bg-primary hover:bg-primary-hover text-white",
          "shadow-orange-glow"
        )}
        onClick={onDiscardAndContinue}
      >
        <RefreshCw className="w-4 h-4" />
        <div className="text-left">
          <div className="font-medium">Discard idle & continue</div>
          <div className="text-[11px] text-white/70 font-normal">
            New timer starts now
          </div>
        </div>
      </Button>
    </div>
  </DialogContent>
</Dialog>
```

## 6.8 — Empty States (Design Opportunities)

Empty states are the first thing new users see on every section. They set the
tone. Treat them as mini landing pages, not error messages.

```tsx
// The universal Yusi Time empty state pattern
function EmptyState({
  icon: Icon,
  heading,
  description,
  action,
  size = 'default'
}: EmptyStateProps) {
  return (
    <div className={cn(
      "flex flex-col items-center justify-center text-center",
      size === 'default' ? "py-16 px-6" : "py-8 px-4"
    )}>
      {/* Icon — tinted container, not just a raw icon */}
      <div className={cn(
        "rounded-xl bg-primary/8 flex items-center justify-center mb-4",
        size === 'default' ? "w-12 h-12" : "w-10 h-10"
      )}>
        <Icon className={cn(
          "text-primary",
          size === 'default' ? "w-6 h-6" : "w-5 h-5"
        )} />
      </div>

      <h3 className={cn(
        "font-semibold text-foreground mb-1.5",
        size === 'default' ? "text-title" : "text-body"
      )}>
        {heading}
      </h3>

      <p className="text-caption text-muted-foreground max-w-[260px] leading-relaxed mb-5">
        {description}
      </p>

      {action}
    </div>
  )
}
```

**Empty state copywriting philosophy:**
- Heading: State what is missing, not what went wrong. "No time entries yet" ✅
  "Nothing to see here" ❌ "Error: empty state" ❌
- Description: Tell the user what to do, not what is missing.
  "Start a timer above to log your first entry." ✅ "There are no entries." ❌
- Action: The CTA should be specific and orange. "Start Timer" ✅ "Go" ❌

## 6.9 — Loading Skeletons

Skeletons must match the exact dimensions of the real content.
A mismatched skeleton causes layout shift and looks cheap.

```tsx
// Skeleton base utility
const Skeleton = ({ className }: { className?: string }) => (
  <div className={cn(
    "animate-pulse rounded-md bg-muted",
    className
  )} />
)

// Stat card skeleton — matches the 6.1 card dimensions exactly
function StatCardSkeleton() {
  return (
    <div className="bg-surface rounded-xl border border-border p-4">
      <div className="flex items-center justify-between mb-3">
        <Skeleton className="h-3 w-16" />      {/* label */}
        <Skeleton className="h-8 w-8 rounded-lg" />  {/* icon container */}
      </div>
      <Skeleton className="h-8 w-28 mb-1.5" />  {/* value */}
      <Skeleton className="h-3 w-20" />          {/* delta */}
    </div>
  )
}

// Table row skeleton — matches 52px row height
function TableRowSkeleton() {
  return (
    <div className="flex items-center gap-3 px-4 h-[52px] border-b border-border">
      <Skeleton className="w-16 h-3" />           {/* date */}
      <div className="flex items-center gap-2 flex-1">
        <Skeleton className="w-2 h-2 rounded-full flex-shrink-0" />
        <div className="space-y-1.5">
          <Skeleton className="w-28 h-3" />       {/* project */}
          <Skeleton className="w-20 h-2.5" />     {/* task */}
        </div>
      </div>
      <Skeleton className="w-32 h-3" />           {/* description */}
      <Skeleton className="w-14 h-3" />           {/* duration */}
      <Skeleton className="w-16 h-5 rounded-[4px]" />  {/* badge */}
    </div>
  )
}
```

---

# PART 7 — MOTION: PHYSICS-BASED, PURPOSEFUL ANIMATION

Animation philosophy: **Every animation should feel like physics, not Flash.**
Movement should decelerate naturally, not abruptly stop. Objects should respond
to user intent immediately. Nothing should bounce or spin for decoration.

## 7.1 — The Animation Budget

```
Each screen gets ONE animated moment.
Each component gets ONE transition type.
Total animation duration: NEVER exceed 300ms for UI transitions.
```

## 7.2 — Framer Motion Configuration (Root Layout)

```tsx
// In web/src/app/layout.tsx
import { MotionConfig } from 'framer-motion'

// This single config governs ALL motion in the app
<MotionConfig
  reducedMotion="user"  // respects prefers-reduced-motion
  transition={{
    type: "tween",
    ease: [0.4, 0, 0.2, 1],  // custom ease-in-out — feels natural
    duration: 0.18
  }}
>
  {children}
</MotionConfig>
```

## 7.3 — Page Transitions

```tsx
// Apply to every page component's root element
// This creates the "each page slides in" feeling
const pageVariants = {
  initial: { opacity: 0, y: 6 },
  animate: { opacity: 1, y: 0 },
  exit:    { opacity: 0 },
}

// In the page component:
<motion.div
  variants={pageVariants}
  initial="initial"
  animate="animate"
  exit="exit"
  transition={{ duration: 0.18, ease: [0.4, 0, 0.2, 1] }}
>
  {/* page content */}
</motion.div>
```

## 7.4 — List Item Stagger (Stat Cards, Recent Entries)

```tsx
// Container — orchestrates the stagger
const containerVariants = {
  animate: { transition: { staggerChildren: 0.05 } }
}

// Each child
const itemVariants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.22 } }
}

// Usage — applies to stat card grid, recent entry list (max 5 items)
<motion.div
  className="grid grid-cols-4 gap-3"
  variants={containerVariants}
  initial="initial"
  animate="animate"
>
  {cards.map(card => (
    <motion.div key={card.id} variants={itemVariants}>
      <StatCard {...card} />
    </motion.div>
  ))}
</motion.div>
```

**Stagger only on first load.** Once the data is cached and the page is
revisited, the stagger should not replay. Use `initial={false}` on the
container when data already exists.

## 7.5 — Modal / Dialog Entry

```tsx
// shadcn Dialog's overlay and content get these CSS classes via globals.css
// The default shadcn animations are good — enhance them with scale

// In globals.css (inside @layer base)
@keyframes dialog-overlay-show {
  from { opacity: 0; }
  to   { opacity: 1; }
}
@keyframes dialog-content-show {
  from { opacity: 0; transform: translate(-50%, -48%) scale(0.96); }
  to   { opacity: 1; transform: translate(-50%, -50%) scale(1); }
}

// Override shadcn dialog animations:
[data-state="open"].DialogOverlay   { animation: dialog-overlay-show 0.15s ease-out; }
[data-state="open"].DialogContent   { animation: dialog-content-show 0.20s ease-out; }
[data-state="closed"].DialogContent { animation: dialog-content-show 0.15s ease-in reverse; }
```

## 7.6 — The Rounding Toast (Critical UX Moment)

The rounding toast is one of Yusi Time's most important UI moments.
It confirms the timer stopped AND communicates the rounded value.
It must feel satisfying.

```tsx
// In lib/rounding-toast.ts
import { toast } from 'sonner'
import { formatDuration } from './utils'

export function showRoundingToast(rounding: RoundingResult): void {
  const wasRounded = rounding.raw_seconds !== rounding.rounded_seconds
  const roundedLabel = formatDuration(rounding.rounded_seconds)
  const rawLabel = formatDuration(rounding.raw_seconds)

  if (wasRounded) {
    toast.success(`Saved as ${roundedLabel}`, {
      description: `${rawLabel} → rounded ${rounding.rounding_mode} to nearest ${rounding.rounding_interval_minutes}m`,
      duration: 5000,
      // sonner supports icon
      icon: <Clock className="w-4 h-4" />,
    })
  } else {
    toast.success(`Saved: ${roundedLabel}`, {
      duration: 3000,
    })
  }
}
```

**sonner Toaster configuration in layout.tsx:**
```tsx
<Toaster
  position="bottom-right"
  richColors
  closeButton
  toastOptions={{
    classNames: {
      toast: "border border-border shadow-float font-sans text-body",
      title: "font-semibold",
      description: "text-caption text-muted-foreground",
    }
  }}
/>
```

## 7.7 — Micro-Interactions Catalog

These are the physical interactions that make the UI feel alive:

```tsx
// Button press — applied to ALL buttons via cn() utility
// Add this to the base Button variant in shadcn component:
"active:scale-[0.97] transition-transform duration-75"

// Card hover — applied to interactive cards (project cards, submission cards)
"hover:border-border-strong hover:shadow-card-hover transition-all duration-200"

// Nav item hover — in the sidebar
"hover:bg-sidebar-accent transition-colors duration-120"

// Row hover — in all tables
"hover:bg-surface-raised transition-colors duration-100 cursor-pointer"

// Switch toggle — the orange thumb snap
// In shadcn Switch, add:
"data-[state=checked]:bg-primary transition-colors duration-200"

// Chevron rotation — for expandable sections
// Wrap in motion.div:
<motion.div
  animate={{ rotate: isOpen ? 180 : 0 }}
  transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
>
  <ChevronDown className="w-4 h-4" />
</motion.div>

// Continue button on entry rows
// The ▶ button is invisible until row hover, then fades in:
"opacity-0 group-hover:opacity-100 transition-opacity duration-150"

// Timer running pulse dot
<span className="w-2 h-2 rounded-full bg-primary animate-timer-pulse" />
// animate-timer-pulse is defined in tailwind.config.ts keyframes above
```

---

# PART 8 — PAGE-BY-PAGE DESIGN DECISIONS

The following are design decisions specific to each page of Yusi Time.
These are not in the UI/UX Blueprint — these are the designer's notes
on WHY each decision was made and HOW to implement it to match the aesthetic.

## 8.1 — Dashboard: The Information Architecture

The Dashboard is the most visited page. Every element must earn its position.

**The grid hierarchy:**
```
Row 1: 4 stat cards (equal width grid)
  ← Today's Hours | This Week | Billable Amount (non-viewer) | Running Timer
  
Row 2: Split 60/40
  ← Top Projects (with mini horizontal bars) | Quick Actions + Recent Entries

These proportions matter. The 60/40 split gives the data visualization
(projects) more space than the action panel. This communicates that Yusi Time
is data-first, actions-second.
```

**The Running Timer card deserves special treatment:**
```tsx
// When timer IS running — the card glows orange
<div className={cn(
  "bg-surface rounded-xl border p-4 transition-all duration-300",
  isRunning
    ? "border-primary/30 shadow-[0_0_0_1px_rgba(254,105,0,0.12),0_4px_12px_rgba(254,105,0,0.10)]"
    : "border-border hover:border-border-strong"
)}>
```

This subtle orange halo around the running timer card is the ONE decorative
use of color as a signal in the entire app. It says "something is happening."

## 8.2 — Timesheet Grid: The Data Density Challenge

The timesheet grid is the most complex layout in the app. Here are the
specific design decisions that make it work:

**Today's column special treatment:**
```tsx
// Today column header — orange circle around the date number
<th className={cn("px-3", isToday && "relative")}>
  {isToday ? (
    <div className="flex flex-col items-center">
      <span className="text-label uppercase text-muted-foreground">
        {format(day, 'EEE')}
      </span>
      <span className="w-7 h-7 rounded-full bg-primary text-white text-caption font-semibold flex items-center justify-center mt-0.5">
        {format(day, 'd')}
      </span>
    </div>
  ) : (
    <div className="flex flex-col items-center">
      <span className="text-label uppercase text-muted-foreground">
        {format(day, 'EEE')}
      </span>
      <span className="text-caption font-medium text-foreground mt-0.5">
        {format(day, 'd')}
      </span>
    </div>
  )}
</th>
```

**Cell state visual hierarchy** (ordered by visual weight):
1. Running cell: `bg-primary/8 border border-primary/20` — most prominent
2. Pending cell: `bg-status-pending-muted` with violet dot — warning
3. Approved cell: `bg-status-approved-muted` — settled/calm
4. Draft with hours: `bg-surface` — neutral, editable
5. Empty: `bg-surface` with `+` on hover — invitation to add

## 8.3 — Settings Pages: The Horizontal Layout Revolution

The settings pages in the current build are the weakest area. The fix is
architectural: switch from vertical form fields to horizontal setting rows.

**Page structure:**
```
Settings page
├── Left nav (200px, sticky)  ← the Settings "mini-sidebar"
└── Right content area
    ├── Section heading + description
    ├── Card (bg-surface border border-border rounded-xl overflow-hidden)
    │   └── Setting rows (with border-b between each, no border on last)
    └── Danger Zone card (border-destructive/20)
```

**The "Save Changes" button position:**
```tsx
// Always at the BOTTOM of a section, right-aligned
// NOT at the top of the page (the current build's mistake)
<div className="flex justify-end pt-4 mt-4 border-t border-border">
  <Button
    type="submit"
    disabled={!isDirty || isSubmitting}
    className="bg-primary hover:bg-primary-hover text-white shadow-orange-glow"
  >
    {isSubmitting ? (
      <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Saving...</>
    ) : (
      'Save Changes'
    )}
  </Button>
</div>
```

## 8.4 — Members Page: The Invite State Machine

The invite flow has two distinct states. The transition between them must
be animated to feel like a genuine response to user action.

```tsx
// State A → State B transition using Framer Motion layout animation
<AnimatePresence mode="wait">
  {inviteState === 'form' ? (
    <motion.div
      key="form"
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      transition={{ duration: 0.18 }}
    >
      <InviteForm onSuccess={() => setInviteState('success')} />
    </motion.div>
  ) : (
    <motion.div
      key="success"
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.18 }}
    >
      <InviteSuccess onReset={() => setInviteState('form')} />
    </motion.div>
  )}
</AnimatePresence>
```

---

# PART 9 — THE FORBIDDEN LIST

These are absolute prohibitions. Every item here was forbidden for a reason.
Do not negotiate with this list.

## 9.1 — Color Prohibitions

```
❌ bg-blue-*, text-blue-*, border-blue-*          → Use brand-orange for actions
❌ bg-[#FE6900], text-[#252F50]                    → Use CSS variable tokens
❌ purple gradients for decorative purposes         → Use brand colors
❌ box-shadow on cards in light mode               → Use border only
❌ box-shadow on sidebar                           → Use border-r only
❌ text-white hardcoded (except on brand-navy bg)  → Use semantic tokens
❌ dark: hardcoded values without semantic token   → All dark values in CSS vars
```

## 9.2 — Typography Prohibitions

```
❌ Inter, Roboto, system-ui as the primary font     → Use DM Sans only
❌ Numbers without font-mono                        → All quantities are mono
❌ Time values without tabular-nums                 → Always add tabular-nums
❌ ALL CAPS body text                               → Only for table headers (label scale)
❌ Underlined text for non-links                    → Never decorative underlines
❌ font-bold on body text                           → Use font-semibold at most
```

## 9.3 — Layout Prohibitions

```
❌ Inline styles (style={{}})                       → Always Tailwind classes
❌ Fixed pixel widths on flex children              → Use Tailwind flex/grid utilities
❌ z-index values above 50 except modals           → Use shadcn's z-index system
❌ overflow-hidden on page body                     → Allow natural page scroll
❌ Negative margins for layout tricks               → Use gap-* for spacing
```

## 9.4 — Animation Prohibitions

```
❌ Animation duration > 300ms for UI transitions   → Hard limit
❌ Animating width, height, padding, margin        → Only opacity and transform
❌ bounce or elastic easing on data updates        → Only ease-out or ease-in-out
❌ Decorative spinning elements (loading spinners  
   as design elements, not loading indicators)     → Purposeful motion only
❌ Multiple simultaneous animations on same screen → One animated moment per screen
❌ Page load animation that replays on re-visit    → initial={false} when data cached
```

## 9.5 — Component Prohibitions (Per PRD/TRD)

```
❌ window.confirm() for confirmations              → Always shadcn AlertDialog
❌ Native <select> elements                        → Always shadcn Select
❌ Custom modal implementations                    → Always shadcn Dialog
❌ shadcn Toast (the built-in one)                 → Always sonner
❌ Any icon library except lucide-react            → Zero exceptions
❌ Default exports on non-page components          → Always named exports
❌ Barrel imports from @/components/ui             → Individual imports only
❌ financial fields visible to Viewer role         → Absent from DOM (not hidden)
❌ Continue/Duplicate on pending entries           → Absent from DOM (not disabled)
❌ X button on Idle Modal                          → Absent from DOM ([&>button]:hidden)
❌ Idle modal dismissible by backdrop/Escape       → Both prevented explicitly
❌ localStorage/sessionStorage for auth tokens     → In-memory only
❌ Direct fetch() or axios in components           → Through apiClient service only
```

---

# PART 10 — THE FOUR COMPONENT STATES (MANDATORY)

Every single data-driven component must implement all four states before it is
considered complete. No exceptions.

```tsx
// The mandatory state pattern for every data component
function TimeEntryList({ workspaceId }: { workspaceId: string }) {
  const { data, isLoading, isError, error, refetch } = useTimeEntries(workspaceId)

  // STATE 1: LOADING — skeleton matches real content shape exactly
  if (isLoading) {
    return (
      <div className="divide-y divide-border">
        {Array.from({ length: 5 }).map((_, i) => (
          <TableRowSkeleton key={i} />
        ))}
      </div>
    )
  }

  // STATE 2: ERROR — message + retry button
  if (isError) {
    return (
      <div className="flex flex-col items-center py-12 gap-3">
        <div className="w-10 h-10 rounded-xl bg-destructive-muted flex items-center justify-center">
          <AlertCircle className="w-5 h-5 text-destructive" />
        </div>
        <p className="text-body font-medium text-foreground">Something went wrong</p>
        <p className="text-caption text-muted-foreground">
          {error instanceof Error ? error.message : 'Failed to load entries'}
        </p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          className="mt-1"
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
          Try again
        </Button>
      </div>
    )
  }

  // STATE 3: EMPTY — icon + heading + description + CTA
  if (!data?.length) {
    return (
      <EmptyState
        icon={Clock}
        heading="No time entries yet"
        description="Start a timer or add a manual entry to begin tracking your work."
        action={
          <Button className="bg-primary hover:bg-primary-hover text-white shadow-orange-glow">
            <Play className="w-4 h-4 mr-2" />
            Start Timer
          </Button>
        }
      />
    )
  }

  // STATE 4: DATA — the real content
  return <TimeEntryTable entries={data} />
}
```

---

# PART 11 — ACCESSIBILITY: NON-NEGOTIABLE DETAILS

## 11.1 — Focus Ring System

Every interactive element must have a visible focus ring. This is both
accessibility-required and, when done right, aesthetically pleasing.

```tsx
// Universal focus ring — applied via Tailwind in globals or component base
"focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"

// For elements on dark backgrounds (sidebar items):
"focus-visible:ring-white/50"

// For icon-only buttons — must have aria-label
<button
  aria-label="Edit entry"
  className="... focus-visible:ring-2 focus-visible:ring-primary/40"
>
  <Pencil className="w-4 h-4" />
</button>
```

## 11.2 — ARIA Requirements

```tsx
// Status badges must communicate to screen readers
<span
  role="status"
  aria-label={`Entry status: ${status}`}
  className={statusBadgeClass}
>
  {statusLabel}
</span>

// Running timer — update frequency
<span
  aria-live="polite"
  aria-atomic="true"
  className="font-mono text-primary"
>
  {elapsed}
</span>

// Loading states
<div aria-busy="true" aria-label="Loading entries">
  <TableRowSkeleton />
</div>

// Disabled interactive elements — always include why
<button
  disabled={isLocked}
  title={isLocked ? "Entry is locked for editing" : undefined}
  aria-disabled={isLocked}
>
```

---

# PART 12 — THEME SYSTEM: LIGHT AND DARK

Both themes are equally first-class. Every component must look intentional
in both modes. Test in dark first — it is harder to get right.

## 12.1 — ThemeProvider Setup

```tsx
// web/src/components/ThemeProvider.tsx
'use client'
import { ThemeProvider as NextThemesProvider } from 'next-themes'
import type { ThemeProviderProps } from 'next-themes'

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
}

// In app/layout.tsx:
<ThemeProvider
  attribute="class"
  defaultTheme="system"
  enableSystem
  disableTransitionOnChange
>
```

## 12.2 — ThemeToggle Component

```tsx
'use client'
import { useTheme } from 'next-themes'
import { Sun, Moon, Monitor } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent,
  DropdownMenuItem, DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'

export function ThemeToggle({ className }: { className?: string }) {
  const { setTheme } = useTheme()
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className={cn("h-8 w-8 text-sidebar-foreground hover:text-white hover:bg-sidebar-accent", className)}
          aria-label="Toggle theme"
        >
          <Sun className="w-4 h-4 rotate-0 scale-100 transition-transform dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute w-4 h-4 rotate-90 scale-0 transition-transform dark:rotate-0 dark:scale-100" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-36">
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

---

# PART 13 — THE PRE-DELIVERY CHECKLIST

Before presenting any screen for review, run every item:

## Visual Quality
- [ ] Logo uses the correct SVG file for the background context
- [ ] Brand orange is `#FE6900` (verified via browser color picker)
- [ ] Brand navy is `#252F50` in sidebar and on dark surfaces
- [ ] ALL numeric values use `font-mono` + `tabular-nums`
- [ ] ALL time values (Xh Ym, H:MM:SS) use `font-mono text-primary` when running
- [ ] ALL monetary amounts use `font-mono text-success`
- [ ] No raw hex colors in any component file
- [ ] Both light AND dark mode tested (open Chrome DevTools → Rendering → Emulate media)
- [ ] Hover states visible on all interactive elements
- [ ] Focus rings visible and orange on all interactive elements
- [ ] Start/Stop button has orange glow shadow
- [ ] Running timer card has subtle orange border glow
- [ ] Active sidebar nav item has orange left border + tinted background

## Settings Pages Specifically
- [ ] Settings use HORIZONTAL layout (label left, control right)
- [ ] Each setting row has a description below the label
- [ ] Rows separated by border-b, last row has no bottom border
- [ ] Save button is at the BOTTOM of the section, right-aligned
- [ ] shadcn Switch thumb turns orange when checked

## Business Rules (From PRD/AGENT.md)
- [ ] Financial fields completely absent (not hidden) for Viewer role
- [ ] Continue/Duplicate buttons absent (not disabled) on pending entries
- [ ] Idle modal: no X button in DOM, backdrop doesn't dismiss, Escape doesn't dismiss
- [ ] Rounding toast fires on EVERY timer stop and entry save
- [ ] Invite button absent (not disabled) for non-Admin roles
- [ ] Submit Week button uses Tooltip when disabled (not just disabled)
- [ ] is_superadmin Super Admin nav link: absent from DOM for non-super-admin users

## Code Quality
- [ ] Zero `any` TypeScript types
- [ ] All API calls through apiClient (zero direct fetch/axios in components)
- [ ] All forms use React Hook Form + Zod
- [ ] All interactive components use shadcn primitives
- [ ] All icons from lucide-react only
- [ ] Named exports on all non-page components
- [ ] No barrel imports from @/components/ui
- [ ] `cn()` used for all conditional class merging
- [ ] `pnpm tsc --noEmit` → 0 errors
- [ ] `pnpm lint` → 0 warnings
- [ ] `pnpm build` → success

## Four Component States
- [ ] Loading: skeleton matches real content shape and dimensions
- [ ] Error: icon + message + retry button
- [ ] Empty: orange icon container + heading + description + CTA
- [ ] Data: real content with all interactions working

---

# PART 14 — DOCUMENT ALIGNMENT NOTES

This document is fully aligned with and subordinate to the following documents
in the hierarchy defined by MASTER_PROMPT.md §2:

| Document | How this skill relates |
|----------|----------------------|
| **PRD v1.3** | All business rules referenced in Parts 8–10 come from the PRD. This skill never overrides PRD behavior. |
| **DB Schema v2.2 + API Spec v1.1** | Financial field isolation, entry status values, role names are all aligned with the schema's enums and API response shapes. |
| **TRD v1.2** | Stack is identical: Next.js 14, TypeScript strict, Tailwind CSS 3, shadcn/ui, next-themes, lucide-react, Framer Motion, TanStack Query v5, Zustand, React Hook Form + Zod. |
| **UI/UX Blueprint v2.0** | This skill is the "how to build it beautifully" companion to the Blueprint's "what to build." When the Blueprint specifies a component state or layout, this skill specifies the exact class names, animation values, and design decisions. |
| **AGENT.md v1.1** | All forbidden patterns in Part 9 are cross-referenced with AGENT.md §11 business rules. |
| **MASTER_PROMPT.md** | All forbidden technology choices (Supabase, localStorage for tokens, non-lucide icons, etc.) are preserved. |

**Conflict resolution:** When this skill specifies a visual detail that could
be interpreted to conflict with the UI/UX Blueprint, the Blueprint wins on
WHAT to show; this skill wins on HOW it should look and animate. When this skill
references business rules, the PRD is always the authoritative source.

---

---

# PART 15 — PROJECTS PAGE: CARD GRID DESIGN

The Projects page uses a card grid. Cards are not plain boxes. Each one
is a miniature dashboard for that project.

## 15.1 — Project Card Anatomy

```tsx
function ProjectCard({ project, role }: ProjectCardProps) {
  const budgetPct = project.budget_hours
    ? Math.min((project.hours_logged / project.budget_hours) * 100, 100)
    : null

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.97 }}
      transition={{ duration: 0.18 }}
      className={cn(
        "bg-surface rounded-xl border border-border p-4",
        "hover:border-border-strong hover:shadow-card-hover",
        "transition-all duration-200 cursor-pointer group",
        "flex flex-col gap-3"
      )}
      onClick={() => router.push(`/projects/${project.id}`)}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5 min-w-0">
          {/* Color dot — the project's identity signal */}
          <span
            className="w-2.5 h-2.5 rounded-full flex-shrink-0 mt-0.5"
            style={{ backgroundColor: project.color ?? '#94A3B8' }}
          />
          <div className="min-w-0">
            <p className="text-body font-semibold text-foreground truncate">
              {project.name}
            </p>
            {project.client_name && (
              <p className="text-caption text-muted-foreground truncate">
                {project.client_name}
              </p>
            )}
          </div>
        </div>

        {/* Actions — only visible on hover, Admin/Manager */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-150">
          {project.visibility === 'private' && (
            <Lock className="w-3.5 h-3.5 text-muted-foreground" />
          )}
          {(role === 'admin' || role === 'manager') && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  className="p-1 rounded-md hover:bg-surface-raised text-muted-foreground hover:text-foreground transition-colors"
                  aria-label="Project actions"
                  onClick={e => e.stopPropagation()}
                >
                  <MoreHorizontal className="w-4 h-4" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={e => { e.stopPropagation(); onEdit(project) }}>
                  <Pencil className="w-4 h-4 mr-2" /> Edit
                </DropdownMenuItem>
                <DropdownMenuItem onClick={e => { e.stopPropagation(); onArchive(project) }}>
                  <Archive className="w-4 h-4 mr-2" /> Archive
                </DropdownMenuItem>
                {role === 'admin' && (
                  <DropdownMenuItem
                    className="text-destructive focus:text-destructive"
                    onClick={e => { e.stopPropagation(); onDelete(project) }}
                  >
                    <Trash2 className="w-4 h-4 mr-2" /> Delete
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-4">
        <div>
          <p className="text-label uppercase tracking-wider text-muted-foreground mb-0.5">
            Hours
          </p>
          <p className="font-mono text-mono-sm font-semibold text-foreground tabular-nums">
            {formatDuration(project.hours_logged_seconds ?? 0)}
          </p>
        </div>
        {role !== 'viewer' && project.budget_hours && (
          <div>
            <p className="text-label uppercase tracking-wider text-muted-foreground mb-0.5">
              Budget
            </p>
            <p className="font-mono text-mono-sm font-semibold text-foreground tabular-nums">
              {project.budget_hours}h
            </p>
          </div>
        )}
      </div>

      {/* Budget progress bar — only for Admin/Manager with budget set */}
      {role !== 'viewer' && budgetPct !== null && (
        <div className="space-y-1">
          <Progress
            value={budgetPct}
            className={cn(
              "h-1.5 rounded-full",
              budgetPct >= 100
                ? "[&>div]:bg-destructive"
                : budgetPct >= 80
                ? "[&>div]:bg-warning"
                : "[&>div]:bg-primary"
            )}
          />
          <p className="text-[10px] text-muted-foreground tabular-nums font-mono">
            {budgetPct.toFixed(0)}% of budget used
          </p>
        </div>
      )}
    </motion.div>
  )
}
```

## 15.2 — The New Project Dialog Color Picker

```tsx
// 8 preset colors — chosen for visual distinctiveness on both themes
const PROJECT_COLORS = [
  '#FE6900', // orange (brand)
  '#3B82F6', // blue
  '#8B5CF6', // violet
  '#EC4899', // pink
  '#10B981', // emerald
  '#F59E0B', // amber
  '#EF4444', // red
  '#64748B', // slate
]

// The swatch grid
<div className="grid grid-cols-8 gap-1.5">
  {PROJECT_COLORS.map(color => (
    <button
      key={color}
      type="button"
      onClick={() => field.onChange(color)}
      className={cn(
        "w-7 h-7 rounded-lg transition-all duration-150",
        "hover:scale-110 active:scale-95",
        field.value === color && "ring-2 ring-primary ring-offset-2 ring-offset-background scale-110"
      )}
      style={{ backgroundColor: color }}
      aria-label={`Select color ${color}`}
    />
  ))}
</div>
```

---

# PART 16 — APPROVALS PAGE: SUBMISSION CARDS

Approvals is a power-user page. Managers and Admins live here during review
cycles. The design must communicate urgency without anxiety.

## 16.1 — Submission Card Design

```tsx
function SubmissionCard({ submission, role }: SubmissionCardProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className={cn(
      "bg-surface rounded-xl border transition-all duration-200",
      submission.status === 'pending'
        ? "border-status-pending/30 hover:border-status-pending/50"
        : "border-border hover:border-border-strong"
    )}>
      {/* Card header — always visible */}
      <div className="flex items-center gap-4 p-4">
        {/* Member identity */}
        <Avatar className="w-9 h-9 flex-shrink-0">
          <AvatarImage src={submission.user_avatar_url ?? undefined} />
          <AvatarFallback className="bg-primary/10 text-primary text-xs font-semibold">
            {getInitials(submission.user_name)}
          </AvatarFallback>
        </Avatar>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-body font-semibold text-foreground">
              {submission.user_name}
            </p>
            <StatusBadge status={submission.status} />
          </div>
          <p className="text-caption text-muted-foreground mt-0.5">
            Week of {format(parseISO(submission.week_start), 'MMM d')} –{' '}
            {format(addDays(parseISO(submission.week_start), 6), 'MMM d, yyyy')}
          </p>
        </div>

        {/* Stats — desktop only */}
        <div className="hidden md:flex items-center gap-6 mr-4">
          <div className="text-right">
            <p className="text-label uppercase tracking-wider text-muted-foreground">
              Entries
            </p>
            <p className="font-mono text-mono-sm font-semibold text-foreground tabular-nums">
              {submission.entry_count}
            </p>
          </div>
          <div className="text-right">
            <p className="text-label uppercase tracking-wider text-muted-foreground">
              Total
            </p>
            <p className="font-mono text-mono-sm font-semibold text-foreground tabular-nums">
              {formatDuration(submission.total_seconds)}
            </p>
          </div>
          {role !== 'viewer' && submission.total_billable_amount && (
            <div className="text-right">
              <p className="text-label uppercase tracking-wider text-muted-foreground">
                Billable
              </p>
              <p className="font-mono text-mono-sm font-semibold text-success tabular-nums">
                ${submission.total_billable_amount}
              </p>
            </div>
          )}
        </div>

        {/* Action buttons */}
        {submission.status === 'pending' && (
          <div className="flex items-center gap-2 flex-shrink-0">
            <Button
              size="sm"
              className="h-8 bg-success/10 hover:bg-success/20 text-success border border-success/20 text-xs font-semibold"
              onClick={() => onApprove(submission.id)}
            >
              <Check className="w-3.5 h-3.5 mr-1" />
              Approve
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="h-8 text-destructive border-destructive/30 hover:bg-destructive/5 text-xs font-semibold"
              onClick={() => onReject(submission.id)}
            >
              <X className="w-3.5 h-3.5 mr-1" />
              Reject
            </Button>
          </div>
        )}

        {/* Expand toggle */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="p-1.5 rounded-md hover:bg-surface-raised text-muted-foreground transition-colors"
          aria-label={expanded ? 'Collapse' : 'Expand'}
        >
          <motion.div
            animate={{ rotate: expanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown className="w-4 h-4" />
          </motion.div>
        </button>
      </div>

      {/* Expandable entry table */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
            className="overflow-hidden"
          >
            <div className="border-t border-border">
              {/* entry rows rendered here */}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
```

**Designer note on the Approve button color:** It uses `bg-success/10` with
`text-success` — NOT a solid green button. This is deliberate. Solid green
buttons feel like "go" signals that can cause accidental approvals. The tinted
outline style says "this is a meaningful action, pause and confirm."

---

# PART 17 — REPORTS: DATA VISUALIZATION GUIDELINES

Reports pages are where Yusi Time earns trust with data. The charts must be
readable, not decorative.

## 17.1 — Recharts Color System

```tsx
// All chart colors must come from CSS variables, never raw hex
// Define them as constants that read from the computed style

const CHART_COLORS = {
  primary:     '#FE6900',  // brand orange — billable bars, primary series
  muted:       'hsl(220 14% 94%)',  // non-billable, secondary series (light)
  mutedDark:   'hsl(222 25% 18%)',  // non-billable in dark mode
  success:     '#16A34A',  // approved amounts
  pending:     '#8B5CF6',  // pending amounts
}

// Recharts tooltip style — must match card design
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface border border-border rounded-xl p-3 shadow-float text-sm">
      <p className="text-caption text-muted-foreground mb-2">{label}</p>
      {payload.map(entry => (
        <div key={entry.name} className="flex items-center gap-2">
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-muted-foreground text-caption">{entry.name}:</span>
          <span className="font-mono text-mono-sm font-semibold text-foreground tabular-nums">
            {entry.value}
          </span>
        </div>
      ))}
    </div>
  )
}
```

## 17.2 — Bar Chart Pattern (Summary Report)

```tsx
<ResponsiveContainer width="100%" height={220}>
  <BarChart
    data={chartData}
    barSize={28}
    barGap={4}
    margin={{ top: 4, right: 4, left: -20, bottom: 0 }}
  >
    <CartesianGrid
      strokeDasharray="3 3"
      stroke="hsl(var(--border))"
      vertical={false}      // horizontal lines only — cleaner
    />
    <XAxis
      dataKey="label"
      tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))', fontFamily: 'DM Sans' }}
      axisLine={false}
      tickLine={false}
    />
    <YAxis
      tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))', fontFamily: 'DM Sans' }}
      axisLine={false}
      tickLine={false}
      tickFormatter={v => `${v}h`}
    />
    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(var(--surface-raised))' }} />
    <Bar dataKey="billable_hours" name="Billable" fill="#FE6900" radius={[4, 4, 0, 0]} />
    <Bar dataKey="non_billable_hours" name="Non-billable" fill="hsl(var(--muted))" radius={[4, 4, 0, 0]} />
  </BarChart>
</ResponsiveContainer>
```

**Key decisions:**
- `vertical={false}` on CartesianGrid — horizontal lines only, no vertical gridlines
- `axisLine={false}` and `tickLine={false}` on both axes — clean, modern
- `radius={[4, 4, 0, 0]}` on bars — rounded top corners only
- `barSize={28}` — not too thin, not too fat; substantial but not dominating

## 17.3 — Weekly Report Grid Interaction

The weekly grid's clickable cells are one of the richest interactions in the app.

```tsx
// The cell Popover — appears on click, lightweight
function WeeklyCell({ entry, onClick }: WeeklyCellProps) {
  const isEmpty = !entry || entry.total_seconds === 0
  const isToday = isSameDay(entry.date, new Date())

  return (
    <td
      className={cn(
        "text-center tabular-nums transition-colors duration-100",
        isToday && "bg-primary/4",
        isEmpty
          ? "text-muted-foreground/30"
          : cn(
              "cursor-pointer hover:bg-primary/6",
              "text-foreground"
            )
      )}
      onClick={isEmpty ? undefined : onClick}
    >
      <span className={cn(
        isEmpty ? "text-caption" : "font-mono text-mono-sm font-semibold"
      )}>
        {isEmpty ? '—' : formatHoursDecimal(entry.total_seconds)}
      </span>
    </td>
  )
}
```

---

# PART 18 — LANDING PAGE: MARKETING POLISH

The landing page is the first thing potential users see. It must communicate
quality immediately. The aesthetic must match the app's premium feel.

## 18.1 — Hero Section Key Implementation Details

```tsx
// The orange glow blob — MUST use pointer-events-none
// and very low opacity (6-8%) to stay ambient, not garish
<div
  aria-hidden="true"
  className={cn(
    "absolute -top-20 right-0 w-[500px] h-[500px]",
    "rounded-full pointer-events-none",
    "bg-primary/6 blur-[100px]",   // large blur radius = ambient, not sharp
  )}
/>

// The dot grid pattern — CSS-only, no SVG
<div
  aria-hidden="true"
  className="absolute inset-0 pointer-events-none"
  style={{
    backgroundImage: `radial-gradient(circle, hsl(var(--border-strong)) 1px, transparent 1px)`,
    backgroundSize: '28px 28px',
    opacity: 0.4,
  }}
/>
```

## 18.2 — Logo Placement in Landing Nav

```tsx
// In the landing nav — light logo on light background
<Link href="/" className="flex items-center">
  <img
    src="/logo-light.svg"
    alt="Yusi Time"
    className="h-8 w-auto"
    draggable={false}
  />
</Link>
```

## 18.3 — CTA Button Hierarchy on Landing

Landing pages need exactly TWO button levels:

```tsx
// PRIMARY CTA — one per hero section, orange with glow
<Button
  asChild
  className={cn(
    "h-12 px-8 text-base font-semibold rounded-xl",
    "bg-primary hover:bg-primary-hover text-white",
    "shadow-orange-glow-lg hover:shadow-orange-glow",
    "transition-all duration-200",
    "active:scale-[0.98]"
  )}
>
  <Link href="/signup">Start Tracking Free</Link>
</Button>

// SECONDARY CTA — ghost, for "watch demo" / "sign in" type actions
<Button
  variant="ghost"
  asChild
  className="h-12 px-8 text-base font-medium text-foreground hover:text-primary"
>
  <Link href="/login">Sign in →</Link>
</Button>
```

---

# PART 19 — RESPONSIVE DESIGN RULES

Yusi Time is web-first but must work down to 375px mobile.

## 19.1 — Breakpoint Behavior

```
375px (mobile) : Single column. Sidebar hidden. TimerBar compressed.
640px (sm)     : Sidebar as Sheet (hamburger trigger). Basic 2-col grids.
768px (md)     : Sidebar visible, icon-only (w-14). Grid items expand.
1024px (lg)    : Full sidebar (w-60). Full layout as designed.
1280px (xl)    : Max-content-width container (max-w-7xl mx-auto).
```

## 19.2 — Responsive Patterns Per Component

**Sidebar:**
```tsx
// Desktop: always visible w-60
// Tablet: icon-only w-14, tooltip shows full label
// Mobile: hidden, Sheet overlay on hamburger click
<Sheet>
  <SheetTrigger asChild>
    <Button variant="ghost" size="icon" className="lg:hidden">
      <Menu className="w-5 h-5" />
    </Button>
  </SheetTrigger>
  <SheetContent side="left" className="w-[260px] p-0 bg-sidebar">
    <SidebarContent />
  </SheetContent>
</Sheet>
```

**Stat cards grid:**
```tsx
// 1 col mobile → 2 col sm → 4 col lg
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
```

**Settings layout:**
```tsx
// Stack on mobile, sidebar + content on md+
<div className="flex flex-col md:flex-row gap-6">
  <nav className="md:w-[200px] md:flex-shrink-0">...</nav>
  <div className="flex-1 min-w-0">...</div>
</div>
```

**TimerBar on mobile:**
```tsx
// Full bar on md+, compressed on mobile (project name + timer + stop only)
<div className="flex items-center gap-2 h-[52px] px-4 border-b border-border bg-surface">
  {/* Always visible */}
  <div className="flex items-center gap-2 flex-1 min-w-0">
    <span className="text-caption text-muted-foreground truncate hidden sm:block">
      {currentProject?.name ?? 'No project'}
    </span>
  </div>

  {/* Timer display — always visible */}
  <span className={cn(
    "font-mono text-mono-table font-semibold tabular-nums flex-shrink-0",
    isRunning ? "text-primary" : "text-muted-foreground"
  )}>
    {elapsed}
  </span>

  {/* Controls — compressed on mobile */}
  <div className="hidden sm:flex items-center gap-2">
    {/* ProjectSelector, TaskSelector, DescriptionInput, TagSelector */}
  </div>

  {/* Start/Stop always visible */}
  <StartStopButton />
</div>
```

---

# PART 20 — UTILITY FUNCTIONS: THE DESIGN SYSTEM'S HELPERS

These functions must exist in `web/src/lib/utils.ts` and be used consistently.

```typescript
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

// The universal class merger — use for ALL conditional classes
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Duration formatter — used everywhere time is displayed
// Returns "5h 30m" format for hours+minutes, "45m" for under 1 hour
export function formatDuration(seconds: number): string {
  if (seconds <= 0) return '0m'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

// Timer display — H:MM:SS for the running timer bar
export function formatElapsed(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

// Hours as decimal — for weekly report cells
export function formatHoursDecimal(seconds: number): string {
  return (seconds / 3600).toFixed(1)
}

// Money formatter — always 2dp string
export function formatMoney(cents: number | null | undefined): string {
  if (cents == null) return '—'
  return `$${(cents / 100).toFixed(2)}`
}

// Initials for Avatar — max 2 chars
export function getInitials(name: string): string {
  return name
    .split(' ')
    .map(n => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

// Description draft key — scoped per user + workspace
export function descriptionDraftKey(userId: string, workspaceId: string): string {
  return `yt_desc_draft_${userId}_${workspaceId}`
}

// Truncate with ellipsis
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str
  return str.slice(0, maxLength - 1) + '…'
}
```

---

# PART 21 — THE DESIGN REVIEW MENTAL MODEL

When reviewing your own work, use this exact process. Do not skip steps.

## Step 1: The 3-Second Test
Open the page. Close your eyes. Open them. What did you see first?
If it was not the most important element on the page, the hierarchy is wrong.
On Dashboard: you should see the timer status first.
On Timesheet: you should see the week dates first.
On Approvals: you should see the pending count first.

## Step 2: The Color Count
Count how many distinct colors appear on the page (not counting text).
If the count is more than 4, something is wrong.
Acceptable palette: background, surface, brand-orange (accent), one semantic
color (success/warning/destructive for status indicators).
Every additional color is visual noise.

## Step 3: The Typography Audit
Look at every number on the page.
Is it `font-mono`? If not — fix it immediately.
Is it `tabular-nums`? If not in a column — fix it.

## Step 4: The Interaction Audit
Hover over every interactive element.
Does it respond visually? (color change, border change, subtle lift?)
Does it do so in under 150ms? (should feel instant)
Does clicking it give immediate feedback? (button press, state change)
If any element doesn't respond, it feels broken.

## Step 5: The Dark Mode Audit
Switch to dark mode. Check:
- Are surfaces truly dark (not just grey)?
- Do borders have enough contrast to be visible?
- Is the orange still vibrant (it should be slightly brighter)?
- Are text hierarchy levels still distinguishable?
- Are skeleton loading states visible against the dark surface?

## Step 6: The Empty State Audit
Clear all data (or imagine the page with no entries).
Does the page communicate what to do next?
Is the empty state visually consistent with the filled state?
Does the CTA button lead to the right action?

---

*FRONTEND_SKILL.md v3.0 — Designer Edition*
*Aligned with: PRD v1.3 · TRD v1.2 · DB Schema v2.2 · API Spec v1.1 · UI/UX Blueprint v2.0 · MASTER_PROMPT.md v1.0*
*Brand colors verified against: logo-dark.svg (#FE6900 orange, #252F50 navy) and logo-light.svg*
*Design inspiration analyzed: Tasko Dashboard, UXBooster Analytics Dashboard, VetCRM Dashboard*
*Author: YusiTime Architect — Senior Frontend Design Intelligence Document*
