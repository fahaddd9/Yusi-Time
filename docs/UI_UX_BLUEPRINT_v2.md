# Yusi Time — UI/UX Blueprint
**Version:** 2.1 (Super Admin Dashboard Added — Full Spec)
**Date:** 2026-05-26
**Status:** Finalized ✅
**Aligned With:** PRD v1.4 · TRD v1.3 · DB Schema v2.2 · API Spec v1.2 · FRONTEND_SKILL.md

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2026-05-26 | Initial final version — logo colors, 5 new features, landing page, all 21 screens |
| 2.1 | 2026-05-31 | Part 14 added — complete Super Admin Dashboard specification (Phase 7.5). Route inventory updated. Component tree updated. Screen count updated to 26. |

---
**Stack:** Next.js 14 App Router · TypeScript strict · Tailwind CSS (darkMode:class) · shadcn/ui · next-themes · lucide-react · Framer Motion · TanStack Query v5 · Zustand · React Hook Form + Zod

---

## BRAND COLOR SYSTEM (Extracted from Logo)

### Logo Analysis
The Yusi Time logo uses two primary brand colors:
- **Navy Blue** `#252F50` — "YUSI" wordmark, primary dark color
- **Orange** `#FE6900` — "TIME" wordmark, rounded-rect border, stopwatch icon

These two colors define the entire design language. Everything flows from them.

### Complete Color Token System

```css
/* globals.css — Full dual-theme CSS variable system */

:root {
  /* ── BRAND ─────────────────────────────────── */
  --brand-navy:        #252F50;   /* Logo navy — primary dark */
  --brand-orange:      #FE6900;   /* Logo orange — primary accent */
  --brand-orange-hover:#E55E00;   /* Orange darkened 10% for hover */
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
  --sidebar-background: 220 47% 18%;     /* #252F50 brand navy */
  --sidebar-foreground: 220 20% 72%;     /* muted blue-gray */
  --sidebar-primary:    24 100% 47%;     /* #FE6900 orange */
  --sidebar-active-bg:  rgba(240,105,0,0.12);
  --sidebar-active-border: #FE6900;
  --sidebar-accent:     220 40% 22%;     /* slightly lighter navy */
  --sidebar-border:     rgba(255,255,255,0.06);

  /* Brand primary = orange */
  --primary:            24 100% 47%;     /* #FE6900 */
  --primary-foreground: 0 0% 100%;       /* white on orange */
  --primary-hover:      24 100% 42%;     /* #E55E00 */
  --primary-muted:      24 100% 95%;     /* #FFF0E6 */

  /* Secondary = navy */
  --secondary:          220 47% 18%;     /* #252F50 */
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
  --foreground:         220 47% 18%;     /* #252F50 — brand navy as primary text */
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
```

### Tailwind Color Mapping

```typescript
// tailwind.config.ts additions
colors: {
  brand: {
    navy:         '#252F50',
    'navy-light': '#EEF1F7',
    orange:       '#FE6900',
    'orange-hover': '#E55E00',
    'orange-light': '#FFF0E6',
  },
  primary: {
    DEFAULT:    'hsl(var(--primary))',
    foreground: 'hsl(var(--primary-foreground))',
    hover:      'hsl(var(--primary-hover))',
    muted:      'hsl(var(--primary-muted))',
  },
  // ... rest of tokens
}
```

### Design Language Rules Derived from Brand Colors

```
ORANGE (#FE6900) is the ACTION color:
  → Primary CTA buttons
  → Active nav item indicator
  → Running timer display
  → Focus rings on inputs
  → Links
  → Hover accents on key elements
  → Progress bar fills

NAVY (#252F50) is the STRUCTURE color:
  → Sidebar background
  → Primary text color (light mode)
  → Page headings
  → The app shell's backbone
  → Secondary buttons on dark surfaces

NEVER use blue (#3B82F6) — it conflicts with the brand palette.
Replace every `text-blue-*` and `bg-blue-*` from the generic system
with orange (actions) or navy (structure).
```

---

## PART 0 — APP FLOW & NAVIGATION MAP

### 0.1 Complete App Flow

```
Browser visits yusitime.com
        │
        ▼
  / (root page) — Landing Page (PUBLIC)
        │
   ┌────┴────┐
   │         │
 No auth    Auth confirmed
   │         │
   ▼         ▼
Landing   /dashboard
  page
  (CTA → /signup or /login)
        │
   middleware.ts checks token
        │
   ┌────┴────┐
   │         │
 No token   Token valid
   │         │
POST /auth/refresh   Protected app
   │
  Fail → /login?redirect=...
```

### 0.2 Route Inventory

| Route | File | Auth | Min Role | Description |
|-------|------|------|----------|-------------|
| `/` | `app/page.tsx` | No | — | **Landing page** — public marketing + CTA |
| `/login` | `app/(auth)/login/page.tsx` | No | — | Sign in |
| `/signup` | `app/(auth)/signup/page.tsx` | No | — | Register |
| `/forgot-password` | `app/(auth)/forgot-password/page.tsx` | No | — | Reset request |
| `/reset-password` | `app/(auth)/reset-password/page.tsx` | No | — | Consume token |
| `/join/[token]` | `app/join/[token]/page.tsx` | No | — | Invite acceptance |
| `/dashboard` | `app/(app)/dashboard/page.tsx` | Yes | viewer | Dashboard |
| `/timesheet` | `app/(app)/timesheet/page.tsx` | Yes | member | Weekly grid |
| `/projects` | `app/(app)/projects/page.tsx` | Yes | viewer | Project list |
| `/projects/[id]` | `app/(app)/projects/[id]/page.tsx` | Yes | viewer | Project detail |
| `/reports/summary` | `app/(app)/reports/summary/page.tsx` | Yes | viewer | Summary report |
| `/reports/detailed` | `app/(app)/reports/detailed/page.tsx` | Yes | viewer | Detailed report |
| `/reports/weekly` | `app/(app)/reports/weekly/page.tsx` | Yes | viewer | Weekly report (NEW) |
| `/approvals` | `app/(app)/approvals/page.tsx` | Yes | manager | Approval queue |
| `/settings/workspace` | `app/(app)/settings/workspace/page.tsx` | Yes | viewer | Workspace config |
| `/settings/members` | `app/(app)/settings/members/page.tsx` | Yes | viewer | Members + invites |
| `/settings/clients` | `app/(app)/settings/clients/page.tsx` | Yes | manager | Clients |
| `/settings/tags` | `app/(app)/settings/tags/page.tsx` | Yes | manager | Tags |
| `/settings/webhooks` | `app/(app)/settings/webhooks/page.tsx` | Yes | admin | Webhooks |
| `/settings/profile` | `app/(app)/settings/profile/page.tsx` | Yes | viewer | Profile |
| `/superadmin` | `app/superadmin/page.tsx` | Yes | superadmin | SA Stats Dashboard |
| `/superadmin/workspaces` | `app/superadmin/workspaces/page.tsx` | Yes | superadmin | SA All Workspaces |
| `/superadmin/workspaces/[id]` | `app/superadmin/workspaces/[id]/page.tsx` | Yes | superadmin | SA Workspace Detail |
| `/superadmin/users` | `app/superadmin/users/page.tsx` | Yes | superadmin | SA All Users |
| `/superadmin/users/[id]` | `app/superadmin/users/[id]/page.tsx` | Yes | superadmin | SA User Detail |

### 0.3 Global Component Tree

```
app/layout.tsx (Server)
  └── ThemeProvider (next-themes, attribute="class", defaultTheme="system")
      └── QueryClientProvider
          └── Toaster (sonner, position="bottom-right")
              └── MotionConfig (reducedMotion="user")
                  │
                  ├── app/(auth)/layout.tsx → AuthLayout (centered card)
                  │
                  ├── app/page.tsx → LandingPage (standalone, no shell)
                  │
                  └── app/(app)/layout.tsx → AppShell
                      ├── Sidebar (w-60, bg-brand-navy)
                      │   ├── Logo (YusiTime SVG mark)
                      │   ├── WorkspaceSwitcher
                      │   ├── NavItems (role-filtered, orange active state)
                      │   └── UserFooter + ThemeToggle
                      ├── TimerBar (h-[50px], bg-surface, border-b)
                      │   ├── ProjectSelector (Command)
                      │   ├── TaskSelector (Select)
                      │   ├── DescriptionInput + draft auto-save
                      │   ├── TagSelector
                      │   ├── BillableToggle
                      │   ├── IdleIndicator (amber, conditional)
                      │   ├── ElapsedDisplay (DM Mono, orange when running)
                      │   └── StartStopButton (orange=start, red=stop)
                      ├── NotificationBell → Sheet panel
                      ├── IdleModal (blocks all interaction, no dismiss)
                      └── <main> → page content
                  └── app/superadmin/layout.tsx → SuperAdminShell (Phase 7.5)
                      ├── SuperAdminSidebar
                      │   ├── Logo (YT mark + "Super Admin" label)
                      │   ├── SuperAdminNav (Stats / Workspaces / Users)
                      │   └── UserFooter + ThemeToggle + "← Back to App" link
                      └── <main> → superadmin page content
```

---

## PART 1 — LANDING PAGE (PUBLIC)

### L1 — Landing Page
**File:** `app/page.tsx`
**Type:** Server Component with client islands
**Goal:** Convert visitors to signups. Beat Clockify's generic landing page with
a modern, bold, premium aesthetic. First impression must communicate:
precision, trust, speed.

---

#### Step 1 — Page Structure Overview

```
LandingPage
├── LandingNav          (sticky top, transparent → solid on scroll)
├── HeroSection         (full viewport height, animated)
├── SocialProofStrip    (logos/stats, seamless scroll)
├── FeaturesSection     (3-column feature grid)
├── TimerDemoSection    (interactive live demo widget)
├── ComparisonSection   (Yusi Time vs competitors)
├── TestimonialsSection (3 cards)
├── PricingTeaser       (MVP: free during beta CTA)
├── FinalCTA            (full-width conversion banner)
└── Footer
```

---

#### Step 2 — LandingNav Component
**File:** `features/landing/components/LandingNav.tsx`

```
Navbar (fixed top-0, w-full, z-50)
  Initial state: bg-transparent, backdrop-blur-0
  On scroll >80px: bg-background/95 backdrop-blur-md border-b border-border
  Transition: all 300ms ease

Layout (max-w-7xl mx-auto px-6 h-16 flex items-center justify-between):

LEFT:
  Logo: YusiTime SVG mark
  "YUSI" in font-bold text-brand-navy (light) / text-foreground (dark)
  "TIME" in font-bold text-brand-orange
  Stopwatch icon from logo mark (24px SVG inline)

CENTER (hidden on mobile, visible md+):
  Nav links: Features | How it Works | Pricing | Blog
  Each: text-sm text-foreground-3 hover:text-foreground transition-colors

RIGHT:
  "Sign in" ghost button → /login
  "Start Free" primary button (bg-brand-orange hover:bg-brand-orange-hover
    text-white px-5 h-9 rounded-lg font-medium text-sm)
  ThemeToggle (Sun/Moon ghost icon)

Mobile (<md): hamburger Sheet menu showing all nav links + CTAs
```

**Hover interaction:** Nav links get a bottom border in orange on hover:
`hover:border-b-2 hover:border-brand-orange`

---

#### Step 3 — HeroSection Component
**File:** `features/landing/components/HeroSection.tsx`

**Visual concept:** Split layout. Left = copy + CTAs. Right = animated app
preview. Background: deep navy (`#252F50`) with subtle grid pattern overlay
(5% white opacity). Orange accent elements.

```
Section (min-h-screen bg-brand-navy relative overflow-hidden):

BACKGROUND ELEMENTS (decorative, non-interactive):
  1. Subtle dot grid pattern (CSS background-image, 1px dots, 6% white opacity)
  2. Large orange glow blob (position: absolute, top-right quadrant,
     w-[600px] h-[600px], bg-brand-orange/8, rounded-full, blur-[120px])
  3. Smaller navy-lighter shape bottom-left (decorative geometry)

CONTENT (max-w-7xl mx-auto px-6, grid grid-cols-1 lg:grid-cols-2 gap-16
          items-center min-h-screen py-24):

LEFT COLUMN:
  Eyebrow badge:
    inline-flex items-center gap-2 bg-brand-orange/10 border border-brand-orange/20
    text-brand-orange text-xs font-medium px-3 py-1.5 rounded-full mb-6
    "✦ Free during Beta — No credit card required"

  Headline (text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1]):
    "Track time." → text-white
    "Invoice faster." → text-white
    "Get paid." → text-brand-orange (the orange word is the hook)

  Subheadline (text-lg text-white/60 mt-6 max-w-lg leading-relaxed):
    "Yusi Time gives freelancers and agencies a smarter way to track
     billable hours, manage approvals, and understand where every
     minute goes."

  CTA row (flex items-center gap-4 mt-10):
    Primary CTA: "Start Tracking Free"
      bg-brand-orange hover:bg-brand-orange-hover text-white
      px-8 h-12 rounded-xl font-semibold text-base
      shadow-[0_0_24px_rgba(240,105,0,0.35)] (orange glow shadow)
      hover:shadow-[0_0_32px_rgba(240,105,0,0.5)]
      Framer Motion: whileHover scale-[1.02], whileTap scale-[0.98]

    Secondary CTA: "Watch Demo →"
      bg-white/8 hover:bg-white/12 text-white border border-white/15
      px-8 h-12 rounded-xl font-medium text-base
      (ghost on dark background)

  Trust signals (flex items-center gap-6 mt-8):
    "✓ No credit card required"
    "✓ 5-minute setup"
    "✓ Free forever plan"
    Each: text-xs text-white/45 flex items-center gap-1.5

RIGHT COLUMN (lg only):
  AppPreviewCard:
    Dark card (bg-white/5 border border-white/10 rounded-2xl p-1
               shadow-2xl backdrop-blur-sm)
    Shows a static/animated screenshot of the dashboard
    OR a live mini-demo of the timer running

    Mini browser chrome at top (3 colored dots, url bar showing "app.yusitime.com")

    Inner content (the app preview):
      bg-[#121825] rounded-xl overflow-hidden
      Shows: TimerBar with "Website Redesign" project running
             "01:23:47" in DM Mono orange
             Below: 3 stat cards in miniature
             Below: 3 entry rows with project dots

    Framer Motion:
      Initial: { opacity: 0, y: 20, rotateX: 5 }
      Animate: { opacity: 1, y: 0, rotateX: 0 }
      Duration: 0.6s, easeOut
      Subtle floating: y: [0, -8, 0], duration: 4s, repeat: Infinity

SCROLL INDICATOR (absolute bottom-8, centered):
  Animated chevron-down (bouncing) + "Scroll to explore" text-white/30 text-xs
```

---

#### Step 4 — SocialProofStrip Component
**File:** `features/landing/components/SocialProofStrip.tsx`

```
Section (bg-brand-navy/50 border-y border-white/6 py-8):
  Content (max-w-7xl mx-auto px-6):

  "Trusted by teams at" (text-xs text-white/30 uppercase tracking-widest
   text-center mb-6)

  Stats row (grid grid-cols-3 gap-8 text-center):
    Stat 1: "10,000+" → text-3xl font-bold text-white
            "Hours tracked" → text-xs text-white/40
    Stat 2: "500+" → text-3xl font-bold text-brand-orange
            "Active workspaces" → text-xs text-white/40
    Stat 3: "98%" → text-3xl font-bold text-white
            "User satisfaction" → text-xs text-white/40

  Stats use Framer Motion counter animation when scrolled into view:
    count up from 0 to final value over 1.5s easing
```

---

#### Step 5 — FeaturesSection Component
**File:** `features/landing/components/FeaturesSection.tsx`

```
Section (bg-background py-24):
  Content (max-w-7xl mx-auto px-6):

  Section header (text-center mb-16):
    Eyebrow: "WHY YUSI TIME" (text-xs font-semibold text-brand-orange
              uppercase tracking-widest)
    Heading: "Everything you need to track,"
             "nothing you don't." (text-4xl font-bold tracking-tight text-foreground)
    Sub: "Built for freelancers, agencies, and growing teams."
         (text-base text-muted-foreground mt-4)

  Feature grid (grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4):

  Each FeatureCard (bg-surface border border-border rounded-2xl p-6
                    hover:border-brand-orange/30 hover:bg-brand-orange/3
                    transition-all duration-200 cursor-default):

    Icon container: w-11 h-11 rounded-xl bg-brand-orange/10 flex items-center
                    justify-center mb-4
    Icon: lucide icon, text-brand-orange, w-5 h-5

    Title: text-base font-semibold text-foreground mb-2
    Description: text-sm text-muted-foreground leading-relaxed

  6 feature cards:
  1. Timer icon → "One-Click Timer"
     "Start tracking in seconds. Switch projects seamlessly. Your timer
      persists across tabs and browser restarts."

  2. Clock icon → "Idle Detection"
     "Step away? We notice. Choose to keep, discard, or split idle time
      with three smart options — no lost time, no phantom hours."

  3. CheckSquare icon → "Approval Workflows"
     "Submit weeks for manager review. Entries lock instantly on submit.
      Approve or reject with one click and mandatory notes."

  4. BarChart3 icon → "Powerful Reports"
     "Summary, detailed, and weekly reports. Export to CSV. Saved views
      for instant access to your favorite filters."

  5. Users icon → "Team Management"
     "Four role levels. Private projects. Client viewer access. Invite
      via shareable link — no email setup required."

  6. Zap icon → "Continue & Duplicate"
     "Restart yesterday's entry in one click. Duplicate recurring tasks
      instantly. Never retype the same project twice."

  Framer Motion: cards stagger in from below (y: 20→0) as section scrolls into view
```

---

#### Step 6 — TimerDemoSection Component
**File:** `features/landing/components/TimerDemoSection.tsx`

```
Section (bg-brand-navy py-24 relative overflow-hidden):
  Background: same dot grid + orange glow as hero (consistent brand section)

  Content (max-w-5xl mx-auto px-6 text-center):

  Heading: "See it in action"
  (text-4xl font-bold text-white tracking-tight)
  Sub: "An interactive timer. No signup required."
  (text-base text-white/50 mt-3)

  DemoWidget (mt-12, bg-white/5 border border-white/10 rounded-2xl p-6
              max-w-2xl mx-auto):

    Mini TimerBar replica (interactive, client-side only — no API):
      Project dropdown (static options: "Website Redesign", "Mobile App", "Consulting")
      Description input ("What are you working on?")
      Start button (orange, Play icon)

    On Start click:
      Button changes to Stop (red)
      Timer starts counting (client-side setInterval, DM Mono orange)
      Entry appears below in a mini table

    On Stop click:
      Toast-like feedback appears: "Saved: 0h 02m 14s"
      Entry row appears in the demo table

    Demo table (3 static + any live entries):
      Shows project dot + name + duration in DM Mono + green $ badge

    "Ready to track real time?" below the widget
    → "Create Free Account" button (orange primary)
```

---

#### Step 7 — ComparisonSection Component
**File:** `features/landing/components/ComparisonSection.tsx`

```
Section (bg-background py-24):
  Content (max-w-4xl mx-auto px-6):

  Heading: "More thoughtful than the alternatives"
  (text-4xl font-bold tracking-tight text-center)

  Comparison table (mt-12, bg-surface border border-border rounded-2xl
                    overflow-hidden):
    Table header row (bg-muted):
      Feature | Yusi Time | Clockify | Generic Tools

    Rows (alternating bg-surface / bg-surface-raised):
      Each row: feature name | ✓ orange | ✓/✗ gray | ✗ red

    Features compared:
      "Idle time detection with 3 options" → ✓ | ✗ | ✗
      "Shareable invite links (no email setup)" → ✓ | ✗ | ✗
      "Rounding confirmation toast" → ✓ | ✗ | ✗
      "Viewer role (client access)" → ✓ | Paid only | ✗
      "Continue & Duplicate entries" → ✓ | ✓ | ✗
      "Weekly team grid report" → ✓ | Paid only | ✗
      "Description draft auto-save" → ✓ | ✗ | ✗
      "Approval workflow" → ✓ | Paid only | ✗

  Note below: "* Comparison based on publicly available information.
  Features may vary."
```

---

#### Step 8 — FinalCTA Section
**File:** `features/landing/components/FinalCTA.tsx`

```
Section (bg-brand-navy py-24 relative overflow-hidden):
  Orange glow top-center (w-[500px] h-[300px] blur-[100px] opacity-15)

  Content (max-w-3xl mx-auto px-6 text-center):
    "Start tracking smarter today."
    (text-5xl font-bold text-white tracking-tight)

    "Free during beta. No credit card. Setup in 5 minutes."
    (text-lg text-white/50 mt-4)

    "Create your free account" button:
      bg-brand-orange hover:bg-brand-orange-hover
      text-white px-10 h-14 rounded-xl font-semibold text-lg mt-10
      shadow-[0_0_40px_rgba(240,105,0,0.4)]

    "Already have an account? Sign in →" (text-sm text-white/30 mt-4)
```

---

#### Step 9 — Footer
**File:** `features/landing/components/LandingFooter.tsx`

```
Footer (bg-brand-navy border-t border-white/6 py-12):
  Content (max-w-7xl mx-auto px-6):

  Top row (grid grid-cols-2 md:grid-cols-4 gap-8):
    Col 1: Logo + "Smart time tracking for modern teams."
           (text-xs text-white/30 mt-3 max-w-[180px])
    Col 2: Product (Features, Changelog, Roadmap)
    Col 3: Company (About, Blog, Contact)
    Col 4: Legal (Privacy, Terms, Security)

  Bottom row (border-t border-white/6 mt-10 pt-6
              flex justify-between items-center):
    "© 2026 Yusi Time. All rights reserved." (text-xs text-white/25)
    ThemeToggle (ghost, icon only)
```

---

## PART 2 — AUTH SCREENS

**Auth Layout:** All auth pages use a centered card layout:
```
bg-background min-h-screen flex items-center justify-center p-4

Background: subtle dot grid pattern (same as landing but very faint)
            + small orange glow blob top-right corner

AuthCard: max-w-[420px] w-full bg-surface border border-border
          rounded-2xl p-8 shadow-[0_8px_40px_rgba(0,0,0,0.08)]
```

---

### A1 — Login Page
**File:** `app/(auth)/login/page.tsx`
**API:** `POST /auth/login`, `GET /auth/google`

#### Step 1 — Logo Area
```
Logo (centered, mb-8):
  YT mark (40px, bg-brand-orange rounded-xl, white "YT" text font-bold)
  "Yusi" (text-xl font-bold text-foreground) + "Time" (text-xl font-bold text-brand-orange)
```

#### Step 2 — Headings
```
"Welcome back" (text-2xl font-bold tracking-tight text-center text-foreground)
"Sign in to your workspace" (text-sm text-muted-foreground text-center mt-1)
```

#### Step 3 — Google OAuth Button
```
Button (full-width, variant="outline", h-11, rounded-xl, gap-3):
  Google SVG icon (20px) + "Continue with Google"
  hover:bg-surface-raised hover:border-brand-orange/40
  transition-all duration-150
```

#### Step 4 — Divider
```
<div className="relative my-5">
  <div className="absolute inset-0 flex items-center">
    <span className="w-full border-t border-border" />
  </div>
  <div className="relative flex justify-center text-xs text-muted-foreground">
    <span className="bg-surface px-3">or continue with email</span>
  </div>
</div>
```

#### Step 5 — Login Form (React Hook Form + Zod)
```
Schema:
  email: z.string().email("Enter a valid email address")
  password: z.string().min(1, "Password is required")

Fields:
  Email:
    Label "Email address" (text-sm font-medium text-foreground)
    Input type="email" autocomplete="email" h-10 rounded-xl
    focus: ring-2 ring-brand-orange/30 border-brand-orange

  Password:
    Label row: "Password" (left) + "Forgot password?" link
               (right, text-xs text-brand-orange hover:underline → /forgot-password)
    Input type="password" autocomplete="current-password" h-10 rounded-xl
    Eye/EyeOff toggle button (right side, icon-only, 16px, text-muted-foreground)

  Error state (inline, below field):
    AlertCircle icon (12px) + error message (text-xs text-destructive)

Submit button:
  "Sign in" full-width bg-brand-orange hover:bg-brand-orange-hover
  text-white h-11 rounded-xl font-semibold
  Loading: Loader2 spinner + "Signing in..."
  active:scale-[0.99] transition
```

#### Step 6 — Footer
```
"Don't have an account?" (text-sm text-muted-foreground text-center mt-6)
"Sign up free →" (text-sm text-brand-orange font-medium hover:underline)
```

#### Step 7 — States
```
Loading: button disabled + spinner, all inputs disabled
Error 401: amber alert banner below form (not inline on fields)
  AlertTriangle + "Invalid email or password. Please try again."
Error 422: field-level via form.setError()
Success: store token → redirect to /dashboard or ?redirect param
```

---

### A2 — Signup Page
**File:** `app/(auth)/signup/page.tsx`
**API:** `POST /auth/signup`

#### Step 1 — Same card layout as Login

#### Step 2 — Schema
```typescript
signupSchema = z.object({
  full_name: z.string().min(1, "Name is required").max(100).trim(),
  email: z.string().email("Enter a valid email address").max(254),
  password: z.string().min(8, "Minimum 8 characters"),
})
```

#### Step 3 — Fields
```
Full Name input (autocomplete="name")
Email input (autocomplete="email")
Password input with:
  - show/hide toggle
  - Strength bar (h-[3px] below input, rounded, transitions):
    < 8 chars: bg-destructive w-1/4
    8-11 chars: bg-warning w-2/4
    12+ chars: bg-success w-full
    (visual only — no enforcement per PRD)

Submit: "Create free account" (orange primary, full-width, h-11)

Terms note (text-xs text-muted-foreground text-center mt-4):
  "By signing up you agree to our Terms & Privacy Policy"
```

#### Step 4 — Post-signup
Success → store token → redirect to `/dashboard`. New user sees
onboarding empty state on dashboard.

---

### A3 — Forgot Password Page
**File:** `app/(auth)/forgot-password/page.tsx`

#### Step 1 — Default state
```
Back link (← Login, text-sm text-brand-orange, top-left of card)
Heading: "Reset your password"
Sub: "Enter your email and we'll send you a reset link."
Email input + "Send Reset Link" button (orange primary, full-width)
```

#### Step 2 — Success state (replaces form)
```
CheckCircle2 (48px, text-success, centered, with scale bounce animation)
"Check your email" (text-xl font-semibold text-center)
"If an account exists for {email}, we've sent a reset link."
"The link expires in 1 hour." (text-xs text-muted-foreground)
"Back to login" link (text-brand-orange)
```

---

### A4 — Reset Password Page
**File:** `app/(auth)/reset-password/page.tsx`

#### Step 1 — On load
Read `?token=` from URL. If absent → show expired state immediately.

#### Step 2 — Schema
```typescript
resetPasswordSchema = z.object({
  new_password: z.string().min(8, "Minimum 8 characters"),
  confirm_password: z.string(),
}).refine(d => d.new_password === d.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
})
```

#### Step 3 — States
```
Valid token: form with two password fields + "Update password" button
Success: CheckCircle2 + "Password updated! Sign in with your new password." + login link
Invalid/expired: XCircle (text-warning) + "This link is invalid or expired."
  + "Request a new link →" (text-brand-orange → /forgot-password)
```

---

### A5 — Invite Accept Page
**File:** `app/join/[token]/page.tsx`

#### Step 1 — Call `GET /invites/{token}` on load

#### Step 2 — Valid state
```
Shield icon (48px, text-brand-orange, centered)
"You've been invited to join" (text-sm text-muted-foreground)
Workspace name (text-2xl font-bold text-foreground)
Role badge (orange variant for the invited role)
"Expires {date}" (text-xs text-muted-foreground)

If NOT authenticated:
  "Create your account" → /signup?invite={token} (orange primary, full-width)
  "Sign in instead →" (text-sm text-brand-orange) → /login?invite={token}

If authenticated:
  User avatar + "Signed in as {name}" (text-xs text-muted-foreground)
  "Join {workspace}" (orange primary, full-width)
  → POST /invites/{token}/accept → /dashboard
```

#### Step 3 — Error states
```
Expired: AlertCircle (text-warning) + "This invite link has expired."
         "Please ask your workspace Admin to generate a new one."

Used/Revoked: XCircle (text-destructive) + "This invite link is no longer valid."
              "It may have already been used or revoked by an Admin."
```

---

## PART 3 — APP SHELL COMPONENTS

### G1 — App Shell Layout
**File:** `app/(app)/layout.tsx`

#### Step 1 — Auth guard
On mount call `POST /auth/refresh`. Show full-screen skeleton while in-flight.
Never show app content before auth confirmed.

#### Step 2 — Layout
```tsx
<div className="flex h-screen overflow-hidden bg-background">
  <Sidebar />                     {/* w-60 fixed, bg-brand-navy */}
  <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
    <TimerBar />                  {/* h-[50px] */}
    <NotificationBell />          {/* positioned inside TimerBar right */}
    <main className="flex-1 overflow-y-auto">
      {children}
    </main>
  </div>
  <IdleModal />
</div>
```

#### Step 3 — Responsive
- **lg+:** Sidebar always visible (w-60)
- **md (768–1023px):** Sidebar icon-only (w-14), hover expands as overlay
- **sm (<768px):** Sidebar hidden, hamburger → Sheet overlay

---

### G2 — Sidebar
**File:** `features/layout/components/Sidebar.tsx`

#### Step 1 — Brand identity section (top, h-16)
```
bg-brand-navy border-b border-white/6
padding: px-4

Logo row (flex items-center gap-2.5):
  YT mark: 30px rounded-lg bg-brand-orange flex items-center justify-center
           "YT" text-white text-xs font-bold letter-spacing-[-0.5px]
  Text: "Yusi" text-sm font-bold text-white + "Time" text-sm font-bold
         text-brand-orange (matches logo exactly)

Below logo: workspace name text-[11px] text-white/35 truncate mt-0.5
WorkspaceSwitcher: ChevronDown icon on hover of workspace name row
```

#### Step 2 — Navigation
```
bg-brand-navy padding: px-3 py-2

Section label "WORKSPACE" (text-[9px] font-semibold text-white/25
               uppercase tracking-[0.08em] px-2 pt-3 pb-1)

NavItems (role-filtered):
  Default: flex items-center gap-2.5 px-2 py-2 rounded-lg text-[13px]
           text-white/45 hover:text-white/80 hover:bg-white/5
           transition-all duration-120

  Active: bg-brand-orange/12 text-white font-medium
          border-l-2 border-brand-orange pl-[6px]
          (the orange left-border accent is the key brand signature)

Nav items:
  LayoutDashboard → Dashboard
  CalendarClock → Timesheet
  FolderOpen → Projects
  BarChart2 → Reports (with sub-items on expand: Summary / Detailed / Weekly)
  [Admin/Manager only]:
  CheckSquare → Approvals

Section label "SETTINGS" (text-[9px] ...)
Settings → Settings
```

#### Step 3 — Reports sub-navigation
```
Reports item has a ChevronRight that rotates to ChevronDown on expand
Sub-items (indented 16px, smaller text):
  BarChart2 icon → Summary
  List icon → Detailed
  Grid icon → Weekly (NEW)
Active sub-item: same orange active state
```

#### Step 4 — Footer (border-t border-white/6)
```
flex items-center gap-2 px-3 py-3

Avatar (28px, initials, gradient bg)
User name (text-[12px] text-white/40 truncate flex-1)
ThemeToggle (Sun/Moon ghost button, text-white/30 hover:text-white/60)
```

---

### G3 — TimerBar
**File:** `features/timer/components/TimerBar.tsx`

#### Step 1 — Layout
```
h-[50px] bg-surface border-b border-border
flex items-center px-4 gap-2

LEFT: ProjectSelector (Command popover, min-w-[160px])
      TaskSelector (Select, min-w-[120px])
      DescriptionInput (flex-1, placeholder "What are you working on?")
RIGHT: TagChips (hidden <md)
       BillableToggle ($ Switch, hidden <md)
       IdleIndicator (amber pill, conditional)
       ElapsedDisplay (DM Mono font-semibold)
       StartStopButton
       NotificationBell (absolute right-4)
```

#### Step 2 — Color states
```
NOT RUNNING:
  ElapsedDisplay: "00:00:00" text-muted-foreground
  StartButton: bg-brand-orange hover:bg-brand-orange-hover text-white
               Play icon + "Start"

RUNNING:
  ElapsedDisplay: font-mono font-semibold text-brand-orange
                  (the orange timer is on-brand and highly visible)
  StopButton: bg-destructive hover:bg-destructive/90 text-white
              Square icon + "Stop"

IDLE:
  IdleIndicator: bg-warning-muted border border-warning/20 text-warning
                 AlertTriangle icon + "Idle {n}m"
  ElapsedDisplay: text-warning
```

#### Step 3 — ProjectSelector
```
shadcn Command inside Popover
Groups: "Recent" (last 3 used projects) + "All Active Projects"
Each option: color dot (6px, project.color) + project name + client (muted)
Keyboard: arrows navigate, Enter selects, Escape closes
Archived projects: hidden
```

#### Step 4 — Start/Stop logic
```typescript
// If mandatory_description and no description:
//   shake animation on DescriptionInput (Framer Motion x: [0,8,-8,8,-8,0])
//   tooltip: "Description required"
//   Do NOT call API

// On Start with force=true: stop running timer first, show rounding toast

// On Stop while idle: open IdleModal first (do not stop directly)
```

#### Step 5 — Continue entry flow (NEW)
```
Continue button appears on time entry rows (▶ icon, 14px, text-muted-foreground)
  hover: text-brand-orange bg-brand-orange/8

On click:
  If no running timer: POST /time-entries/{id}/continue directly
  If timer running: AlertDialog:
    "Switch active timer?"
    "Your current timer will be stopped and saved before starting this one."
    [Cancel] [Stop & Continue — orange primary]
    On confirm: POST /time-entries/{id}/continue { force: true }

On success: showRoundingToast only if force=true (previous timer was stopped)
            New timer starts, TimerBar updates immediately
```

#### Step 6 — Description draft auto-save (NEW)
```
useDescriptionDraft(userId, workspaceId) hook

On component mount:
  If currentTimer === null: restore draft from localStorage → populate description field
  If currentTimer exists: use server description, clear draft

On description input onChange (debounced 500ms):
  saveDraft(value) → localStorage key: yt_desc_draft_{userId}_{workspaceId}

On startTimer success: clearDraft()
On stopTimer success: clearDraft()
On input cleared: clearDraft()

Visual: no indicator shown — silent background operation
```

---

### G4 — IdleModal
**File:** `features/timer/components/IdleModal.tsx`

#### Step 1 — Dialog setup (NO DISMISS)
```tsx
<Dialog open={isIdle} onOpenChange={() => {}}>
  <DialogContent
    className="sm:max-w-sm [&>button]:hidden"
    onPointerDownOutside={e => e.preventDefault()}
    onEscapeKeyDown={e => e.preventDefault()}
  >
```

#### Step 2 — Content
```
AlertTriangle icon (40px, text-warning, centered, with subtle pulse animation)

"You've been idle" (text-lg font-semibold text-center)
"No activity for {n} minutes." (text-sm text-muted-foreground text-center)
"Your timer is still running." (text-xs text-muted-foreground text-center)

Three option buttons (flex-col gap-2 mt-4):

Option 1 — "Keep Time & Continue"
  variant="outline" full-width, Play icon left
  Sub: "Idle time counted as work" (text-[11px] text-muted-foreground mt-0.5)
  hover: border-brand-orange/40 bg-brand-orange/4

Option 2 — "Discard Idle & Stop"
  variant="outline" full-width, Square icon left
  Sub: "Saved at {idleStartTime}"
  hover: border-destructive/40 bg-destructive/4

Option 3 — "Discard Idle & Continue" [DEFAULT/PRIMARY]
  bg-brand-orange text-white full-width, RefreshCw icon left
  Sub: "New timer starts now" (text-[11px] text-white/70)
  hover: bg-brand-orange-hover
```

#### Step 3 — Loading state
On any option click: spinner on that button, all three disabled. On error: re-enable.

---

### G5 — NotificationBell
**File:** `features/notifications/components/NotificationBell.tsx`

#### Step 1 — Bell icon
```
Bell icon (20px, text-muted-foreground, hover:text-foreground)
Unread badge: w-4 h-4 bg-destructive rounded-full text-[9px] text-white
              absolute top-1 right-1
              Framer Motion: scale bounce when count increases
```

#### Step 2 — Sheet panel (side="right", w-[360px])
```
Header: "Notifications" font-semibold + "Mark all read" (text-brand-orange text-xs)

Notification items (divide-y divide-border):
  Unread dot: 6px bg-brand-orange rounded-full (left side)
  Icon by type:
    approved → CheckCircle2 text-success
    rejected → XCircle text-destructive
    submitted → Send text-status-pending
    timer_stopped → AlarmClock text-warning
    workspace_deleted → Trash2 text-destructive
  Title text-sm font-medium
  Message text-xs text-muted-foreground (2 lines)
  Time text-[10px] text-muted-foreground right
  Row hover: bg-surface-raised

Empty: BellOff icon (text-muted-foreground) + "No notifications yet"
```

---

## PART 4 — DASHBOARD

### C1 — Dashboard
**File:** `app/(app)/dashboard/page.tsx`

#### Step 1 — Page header
```
flex justify-between items-center mb-6

Left: "Dashboard" text-xl font-semibold tracking-tight text-foreground
Right: date text-xs text-muted-foreground "Monday, May 25, 2026"
```

#### Step 2 — Stat cards row
```
grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4

All cards: bg-surface border border-border rounded-xl p-4
           hover:border-brand-orange/20 transition-colors duration-200
```

**Card 1 — Today's Hours**
```
Label: "TODAY" text-[10px] uppercase tracking-wider text-muted-foreground
Value: "5h 30m" font-mono text-2xl font-bold text-foreground
Meta: "↑ +1h from yesterday" text-xs text-success
      OR "No entries yet" text-xs text-muted-foreground
```

**Card 2 — This Week**
```
Value: "23h 45m" font-mono text-2xl font-bold
Progress bar (shadcn Progress, h-[3px], bg-brand-orange fill):
  [className="[&>div]:bg-brand-orange"]
Meta: "59% of 40h goal" text-xs text-muted-foreground
If no goal: "Set a weekly goal →" text-brand-orange text-xs
```

**Card 3 — Billable Amount (ABSENT FOR VIEWER)**
```
{role !== 'viewer' && (
  <StatCard>
    Label: "BILLABLE"
    Value: "$1,781.25" font-mono text-2xl font-bold text-success
    Meta: "23h 45m billable" text-xs text-muted-foreground
  </StatCard>
)}
```

**Card 4 — Running Timer**
```
IF running:
  Pulse dot (6px bg-brand-orange animate-pulse) + project name text-xs text-brand-orange
  "01:23:47" font-mono text-xl font-bold text-brand-orange
  "Stop" button: destructive sm size inline

IF not running:
  Clock icon (28px text-muted-foreground)
  "No active timer" text-sm text-muted-foreground
  "Start Timer" button: bg-brand-orange text-white sm size
    onClick: focus ProjectSelector in TimerBar
```

#### Step 3 — Loading skeletons (4 cards)
```tsx
<Skeleton className="h-3 w-12" />    {/* label */}
<Skeleton className="h-8 w-24" />    {/* value */}
<Skeleton className="h-2.5 w-16" /> {/* meta */}
```

#### Step 4 — Two-column section
```
grid grid-cols-1 lg:grid-cols-5 gap-3 mb-4
```

**Left (col-span-3) — Top Projects**
```
Card: bg-surface border border-border rounded-xl p-4

Header: "Top Projects" text-sm font-semibold
        "View all →" text-xs text-brand-orange → /projects

Each project row (up to 5):
  flex justify-between items-center mb-2
  Left: color dot (6px project.color) + name text-sm font-medium
  Right: "12h 30m" font-mono text-xs text-muted-foreground
  Bar (full-width h-[2px] mt-1.5, bg-surface-raised):
    fill: bg-brand-orange/60 or project.color

  Row hover: bg-surface-raised -mx-2 px-2 rounded-lg transition-colors

Empty state: Clock (text-muted-foreground 40px) + "No time logged this week"
             + "Start Timer" (orange, sm)
```

**Right (col-span-2) — Quick Actions**
```
Card: bg-surface border border-border rounded-xl p-4

Header: "Quick Actions" text-sm font-semibold mb-3

Buttons (full-width, gap-1.5):
  ▶ "Start Timer" — bg-brand-orange text-white (primary)
  + "Add Entry" — variant="outline" hover:border-brand-orange/40
  ≡ "View Reports" — variant="outline"

Separator (my-3, border-t border-border)

"Recent" label (text-[10px] uppercase tracking-wider text-muted-foreground mb-2)

Last 5 entries (compact list — NEW shows 5 not 3):
  Each row: flex items-center gap-2 py-1.5 group
    color dot + project name (font-medium text-[12px]) + task (muted text-[11px])
    RIGHT: duration (font-mono text-[11px]) + Continue button ▶

  Continue button (▶ Play icon, 14px):
    opacity-0 group-hover:opacity-100 transition-opacity
    text-muted-foreground hover:text-brand-orange
    p-1 rounded hover:bg-brand-orange/8
    onClick: useContinueEntry(entry.id)
    Tooltip: "Continue this entry"

  Pending entry rows: ▶ button absent (not rendered)
```

#### Step 5 — Recent Entries Table
```
Card: bg-surface border border-border rounded-xl overflow-hidden

Header: "Recent Entries" text-sm font-semibold
        Week tabs: "This week" (active: bg-brand-orange/10 text-brand-orange
                                border border-brand-orange/20) | "Last week"

Table columns:
  DATE | PROJECT/TASK | DESCRIPTION | DURATION | BILL | STATUS | ACTIONS

DATE: text-[11px] text-muted-foreground
PROJECT: color dot + name (font-medium text-[12px]) / task (muted text-[11px])
DESCRIPTION: text-[11px] text-muted-foreground truncate
DURATION: font-mono text-sm font-semibold
BILL: $ (text-brand-orange) or — (text-muted-foreground/30)
      [ABSENT for Viewer]
STATUS: StatusBadge (uses CSS variable colors)
ACTIONS (visible on row hover — group-hover pattern):
  Continue ▶ (absent for pending)
  Edit ✎ (disabled + tooltip for pending/approved non-admin)
  Duplicate (in ... menu, absent for pending)
  Delete 🗑 (disabled for pending/approved non-admin)

Row hover: bg-surface-raised transition-colors duration-100
Locked rows: edit/delete opacity-30 cursor-not-allowed
```

#### Step 6 — Table empty state
```
<EmptyState
  icon={Clock}
  heading="No entries this week"
  description="Start a timer or add an entry to begin tracking."
  action={<Button className="bg-brand-orange text-white">Start Timer</Button>}
/>
```

#### Step 7 — Table loading
5 × `<TableRowSkeleton />` matching exact column widths.

---

## PART 5 — TIMESHEET

### D1 — Weekly Timesheet Grid
**File:** `app/(app)/timesheet/page.tsx`

#### Step 1 — Page header
```
flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-5

Left: "Timesheet" text-xl font-semibold tracking-tight

Right:
  Week navigator:
    ChevronLeft (ghost, icon-only, h-8 w-8 rounded-lg border hover:border-brand-orange/40)
    "May 18 – May 24, 2026" (text-sm font-medium min-w-[190px] text-center)
    ChevronRight (same)
    "Today" pill (bg-brand-orange/10 text-brand-orange border border-brand-orange/20
                  text-xs px-3 h-7 rounded-lg hover:bg-brand-orange/15)

  Submit Week button (when approval_workflow_enabled):
    bg-brand-orange text-white h-9 rounded-lg font-medium text-sm
    Disabled: opacity-50 cursor-not-allowed
    Tooltip when disabled: "No unlocked entries to submit this week"
    Enabled: "Submit Week (7)" — count in parentheses
```

#### Step 2 — Grid table structure
```
overflow-x-auto
Table (min-w-[700px] border-collapse)

HEADER ROW (bg-surface-raised border-b border-border sticky top-0 z-10):
  Col 1 (200px sticky left-0 bg-surface-raised): "Project / Task"
         (text-[10px] uppercase text-muted-foreground)
  Cols 2-8 (equal): Day headers
    Day abbrev (text-[10px] uppercase text-muted-foreground)
    Date number (text-base font-bold text-foreground)
    TODAY: date in circle (28px bg-brand-orange text-white rounded-full)
    TODAY column: subtle bg-brand-orange/4 tint on all cells
  Col 9 (64px): "Total" right-align

PROJECT GROUP ROW (bg-surface-raised border-b border-border h-10):
  Col 1: orange-dot (8px, project.color) + project name (font-semibold text-sm)
         + client (text-[11px] text-muted-foreground)
         + ChevronDown/Right collapse toggle
  Day cells: summed hours (font-mono text-xs text-muted-foreground)
  Total: font-mono text-xs font-semibold

TASK SUB-ROW (bg-surface border-b border-border/50 h-9):
  Col 1: 20px indent + task name (text-xs text-muted-foreground)
  Day cells: GRID CELLS (see Step 3)

DAY TOTAL ROW (bg-surface-raised border-t-2 border-border h-10):
  "Daily Total" (text-[10px] uppercase text-muted-foreground)
  Each day: font-mono text-sm font-bold text-foreground
```

#### Step 3 — Grid cell states
```
EMPTY CELL:
  bg-surface cursor-pointer
  hover: bg-brand-orange/5 show "+" (text-brand-orange/50, centered, 16px)
  click → opens AddEntrySheet prefilled with project + date
  focus ring: ring-1 ring-brand-orange/40

DRAFT/EDITABLE CELL:
  bg-surface
  Content: font-mono text-[12px] font-semibold text-foreground centered
  hover: bg-surface-raised + pencil icon (12px text-muted-foreground, top-right)
  click → EditEntrySheet

PENDING CELL:
  bg-status-pending-muted
  Content: font-mono text-[12px] font-semibold text-status-pending
  Top-right: 5px dot bg-status-pending rounded-full
  hover tooltip: "Submitted — awaiting approval"
  cursor: default (not editable by member)
  Admin: cursor-pointer → EditEntrySheet

APPROVED CELL:
  bg-status-approved-muted
  Content: font-mono text-[12px] font-semibold text-status-approved
  Top-right: 5px dot bg-status-approved rounded-full
  hover tooltip: "Approved"
  cursor: default
```

#### Step 4 — AddEntry / EditEntry Sheet
```
Sheet (side="right", w-[400px])

SheetHeader: "Add Time Entry" or "Edit Entry"
             CloseButton top-right (standard shadcn X)

Form fields (React Hook Form + Zod):
  Project (Select — prefilled, required)
    option hover: bg-brand-orange/6 text-brand-orange
    focus: border-brand-orange ring-brand-orange/20

  Task (Select — filtered by project)
  Date (Input type="date" — prefilled)
  Start Time (Input type="time" HH:MM)
  End Time (Input type="time" HH:MM)

  Duration preview (inline, below time fields):
    "Duration: 2h 15m" font-mono text-sm
    If rounding changes value: amber label
      "Will save as 2h 15m (↑ rounded to nearest 15 min)"
      text-[11px] text-warning bg-warning-muted px-2 py-1 rounded-md
    If no rounding: green label
      "Will save as 2h 15m (no rounding)" text-[11px] text-success

  Description (Textarea 3 rows, maxLength=500)
    If mandatory_description: required indicator + validation

  Billable (Switch — label "Billable", $ icon)
    Switch thumb: bg-brand-orange when checked

  Tags (Command popover multi-select, chips):
    Selected chips: bg-brand-orange/10 text-brand-orange border-brand-orange/20
                    rounded-full text-[11px] px-2 py-0.5

  Overlap warning (if has_overlap):
    AlertTriangle (text-warning) + "This entry overlaps another entry"
    bg-warning-muted rounded-lg p-2.5 text-[11px]

SheetFooter:
  Cancel (variant="ghost") + Save (bg-brand-orange text-white)
  Save shows Loader2 spinner during mutation
```

#### Step 5 — Submit Week Modal
```
AlertDialog:
  Header: "Submit Week for Approval"
          "May 18 – May 24, 2026" (text-sm text-muted-foreground)

  Info box (bg-brand-orange/6 border-l-4 border-brand-orange p-3 rounded-r-lg text-[12px]):
    "Submitted entries will be locked and cannot be edited until reviewed."

  Entries list (max-h-[240px] overflow-y-auto space-y-1):
    Section: "Submitting (7 entries)" (text-[11px] font-medium text-foreground mb-2)
    Each row: day + project dot + project name + font-mono duration
    [If approved entries exist in same week]:
      Separator + "Already approved (2) — excluded" (muted italic)

  Footer: Cancel + "Submit 7 Entries" (bg-brand-orange text-white)
```

#### Step 6 — Continue and Duplicate in timesheet (NEW)
```
Each task sub-row has a three-dot (MoreHorizontal) menu on hover:
  DropdownMenu items:
    ▶ Continue last entry (text-brand-orange) — POST /time-entries/{id}/continue
       [only if draft/approved entry exists for this project/task today or recently]
    ⊕ Duplicate last entry — POST /time-entries/{id}/duplicate
    [separator if entries in this row are pending:]
    ⚠ "Pending entries cannot be continued or duplicated" (disabled, muted)
```

---

## PART 6 — PROJECTS

### E1 — Projects List
**File:** `app/(app)/projects/page.tsx`

#### Step 1 — Header
```
PageHeader:
  "Projects" heading
  Right: search input + status filter (Active|Archived|All tabs)
         + client filter Select
         + [Manager/Admin] "New Project" (bg-brand-orange text-white)
```

#### Step 2 — Project cards grid
```
grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3

Each card:
  bg-surface border border-border rounded-xl p-4
  hover:border-brand-orange/30 hover:shadow-sm
  cursor-pointer → /projects/[id]
  transition-all duration-200

  Top: color dot (10px, project.color) + project name (font-semibold)
       [right]: three-dot menu (Manager/Admin only)
  Client: text-xs text-muted-foreground
  Budget bar (if set, HIDDEN for Viewer):
    Progress (h-[3px] [&>div]:bg-brand-orange)
    "45h / 200h" font-mono text-xs
    80%: [&>div]:bg-warning
    100%+: [&>div]:bg-destructive
  Bottom: hours this month (font-mono text-xs font-medium)
          Lock icon + "Private" (if private project)
```

#### Step 3 — New Project Dialog
```
Dialog (sm:max-w-lg):
  Fields: Name, Client (Select), Color (8 swatches + hex input),
          Visibility (Public/Private ToggleGroup),
          Default Billable (Switch — orange thumb),
          Hourly Rate (number input, $ prefix, ABSENT for Viewer),
          Budget Hours / Budget Amount

  Color swatches (grid grid-cols-8 gap-1.5):
    Each: w-6 h-6 rounded-full cursor-pointer ring-offset-2
    Selected: ring-2 ring-brand-orange

  Footer: Cancel + "Create Project" (bg-brand-orange text-white)
```

---

### E2 — Project Detail
**File:** `app/(app)/projects/[id]/page.tsx`

#### Step 1 — Header
```
Back link (ChevronLeft + "Projects") text-brand-orange text-sm
Project name text-2xl font-bold tracking-tight
Client text-sm text-muted-foreground
Color dot (12px inline)
[Manager/Admin]: Edit (PenLine ghost) + Archive (Archive ghost)
```

#### Step 2 — Budget progress (HIDDEN for Viewer)
```
Card with Progress bar (brand-orange fill)
Hours and amount in font-mono text-sm
80%+: warning color override
100%+: destructive color override + "Budget exceeded" badge
```

#### Step 3 — Tabs
```
shadcn Tabs: Overview | Tasks | Members (private) | Settings (Admin/Manager)
Active tab: text-brand-orange border-b-2 border-brand-orange
```

**Overview Tab:**
- Summary stats (total/billable hours, entry count)
- Recharts BarChart (bar fill: brand-orange)
- Recent entries table (same as Dashboard with Continue + Duplicate)

**Tasks Tab:**
- Task list (divide-y) with assignee, estimated hours, hours logged
- Continue and Duplicate available per task row (NEW)
- "Add Task" (brand-orange)

**Members Tab:** Member list + "Add Member"

**Settings Tab:** Edit form + Danger Zone

---

## PART 7 — REPORTS

### F1 — Summary Report
**File:** `app/(app)/reports/summary/page.tsx`

#### Step 1 — Tabs
```
"Summary" | "Detailed" | "Weekly" (NEW)
Active tab: text-brand-orange border-b-2 border-brand-orange
```

#### Step 2 — Filter bar
```
Card (bg-surface border border-border rounded-xl p-3)
flex flex-wrap gap-2 items-center

Date range picker (Popover with presets: Today, This Week, This Month, Last Month, Custom)
  Trigger: Calendar icon + date range text, hover:border-brand-orange/40

Group By Select: "Group by Project" | "Group by User" | "Group by Client" | "Group by Tag"
  Focus: border-brand-orange ring-brand-orange/20

Project / User / Billable / Status filters

"Clear Filters" (ghost, text-brand-orange, visible only when active)
"Save View" (Bookmark icon, bg-brand-orange/8 text-brand-orange border border-brand-orange/20)
"Export CSV" (Download icon, variant="outline")
```

#### Step 3 — Metric cards (4, BILLABLE AMOUNT ABSENT for Viewer)
```
Same style as Dashboard stat cards:
  hover:border-brand-orange/20
  Progress fills: bg-brand-orange
```

#### Step 4 — Bar chart (Recharts)
```
HorizontalBarChart:
  Billable bar fill: '#FE6900' (brand-orange)
  Non-billable bar fill: hsl(var(--muted))
  Tooltip: bg-surface border border-border rounded-lg shadow-lg
  Legend: orange square "Billable" + muted square "Non-billable"
```

#### Step 5 — Summary table
```
Sortable columns. Hover: bg-surface-raised.
Sort indicator: ChevronUp/Down in text-brand-orange
Header row: bg-surface-raised text-[10px] uppercase text-muted-foreground
Subtotal row: bg-surface-raised border-t-2 font-bold
BILLABLE AMOUNT column: ABSENT for Viewer
Click row → filtered detailed report
```

#### Step 6 — Saved views sidebar
```
w-[220px] right side (lg+, collapsible)
Active view: text-brand-orange font-medium bg-brand-orange/6
             border-l-2 border-brand-orange
Delete icon: appears on hover, text-destructive
```

---

### F2 — Detailed Report
**File:** `app/(app)/reports/detailed/page.tsx`

Same filter bar. Cursor-paginated table with Continue + Duplicate per row (NEW).
Financial columns absent for Viewer. Infinite scroll with AnimatePresence.

---

### F3 — Weekly Report (NEW — v1.3)
**File:** `app/(app)/reports/weekly/page.tsx`
**API:** `GET /reports/weekly`, `GET /reports/weekly/export`

#### Step 1 — Page header
```
PageHeader: "Weekly Report"
Right: date range picker (defaults to current week Mon–Sun)
       + User filter (Admin/Manager: "All Members" | list; Member/Viewer: own row only, hidden)
       + Project filter (optional)
       + Billable filter toggle
       + "Export CSV" (variant="outline", Download icon)
```

#### Step 2 — Weekly grid table
```
Card (bg-surface border rounded-xl overflow-hidden)

HEADER ROW (bg-surface-raised border-b border-border):
  Col 1 (180px sticky left-0): "Member" (text-[10px] uppercase text-muted-foreground)
  Day cols (7, equal width):
    Day abbrev + date "Mon 18", "Tue 19" etc
    TODAY column: orange tint header + bg-brand-orange/5 on all cells
  Summary cols:
    "Total" + [role !== 'viewer'] "Billable"

MEMBER ROWS:
  Col 1:
    Avatar (26px initials, gradient) + name (text-sm font-medium) + role badge
  Day cells:
    Zero hours: text-[11px] text-muted-foreground/30 "—" centered
    Has hours: font-mono text-[12px] font-semibold text-foreground centered
               hover: bg-brand-orange/6 cursor-pointer
               click → Popover with entry details for that user+day
    TODAY cell: subtle bg-brand-orange/4 tint
  Total cell: font-mono text-sm font-bold text-foreground
  Billable cell (ABSENT for Viewer): font-mono text-sm text-success

TOTALS ROW (bg-surface-raised border-t-2 border-border):
  "Team Total" (font-semibold text-sm)
  Day totals: font-mono text-sm font-bold
  Grand total: font-mono text-sm font-bold
  Grand billable (ABSENT for Viewer): font-mono text-sm text-success
```

#### Step 3 — Cell popover (click on any day cell)
```
Popover (no Portal, inline):
  "{User name} — {Day, Date}" (text-sm font-semibold)
  Entry list:
    Each: project dot + project name + task + font-mono duration
    Empty: "No entries" text-xs text-muted-foreground
  "View in Detailed Report →" link (text-xs text-brand-orange)
    → navigates to /reports/detailed filtered to that user + date
```

#### Step 4 — Loading state
Skeleton table: member rows with gray bars in each cell.

#### Step 5 — Empty state
```
<EmptyState icon={Grid} heading="No time logged" description="..." />
```

---

## PART 8 — APPROVALS

### G1 — Approvals Dashboard
**File:** `app/(app)/approvals/page.tsx`
**Access guard:** Manager/Admin only. Others → redirect to /dashboard.

#### Step 1 — Header
```
"Approvals" heading
Filter row:
  Status tabs: "Pending (4)" | "Approved" | "Rejected" | "All"
  Active tab: bg-brand-orange/10 text-brand-orange border border-brand-orange/20
  Member filter Select + Week filter Select
```

#### Step 2 — Submission card (default collapsed)
```
Card (bg-surface border border-border rounded-xl)
hover:border-brand-orange/20 transition-colors

CARD HEADER (flex justify-between p-4):
  LEFT:
    Avatar (34px, initials, gradient)
    Name (text-sm font-semibold) + role badge
    "Week of May 18–24, 2026" (text-xs text-muted-foreground)
    "Submitted 2h ago" (ClockIcon text-[11px] text-muted-foreground)

  CENTER (stats flex gap-5):
    "7 entries" (text-sm text-muted-foreground)
    "38h 30m" (font-mono text-sm font-semibold text-foreground)
    "$2,887.50" (font-mono text-sm text-success) — ABSENT for Viewer

  RIGHT (action buttons flex gap-2):
    Approve: bg-success text-white h-8 px-3 rounded-lg text-xs font-medium
             CheckIcon + "Approve"
             hover:bg-success/90

    Reject: variant="outline" text-destructive border-destructive/30 h-8 px-3
            rounded-lg text-xs XIcon + "Reject"
            hover:bg-destructive/5 hover:border-destructive

    Expand: ChevronDown ghost icon-only h-8 w-8 (rotates 180° when expanded)
```

#### Step 3 — Expanded card content (AnimatePresence slide-down)
```
Border-t border-border mx-4 mb-4

Entry table:
  Cols: DATE | PROJECT | TASK | DESCRIPTION | DURATION | BILLABLE
  text-[11px] rows, alternating bg-surface / bg-surface-raised
  Lock icon (12px text-muted-foreground/30) right of each row
  No rate/amount in per-entry rows
```

#### Step 4 — Approve confirmation (AlertDialog)
```
"Approve this timesheet?"
"Sam Lee's week of May 18–24 will be permanently approved and locked."
[Cancel] [Approve — bg-success text-white]
```

#### Step 5 — Rejection Dialog
```
Dialog (sm:max-w-sm):
  "Reject Timesheet" + "Sam Lee — May 18–24" subtext

  Amber info box (bg-warning-muted border-l-4 border-warning p-3 rounded-r-lg):
    "All entries will be unlocked and returned to Sam Lee for correction."

  Mandatory note:
    Label: "Rejection Note *" (required, red asterisk)
    Textarea (4 rows, maxLength=1000)
    Character counter (text-[10px] text-muted-foreground right-aligned)
    Counter → text-warning at 900+
    Error if blank: "A rejection note is required"
      (text-xs text-destructive flex items-center gap-1 mt-1)

  Footer: Cancel + "Confirm Rejection" (bg-destructive text-white)
```

#### Step 6 — Empty state
```
<EmptyState icon={CheckCircle2} heading="All caught up!"
  description="No pending timesheets to review." />
```

---

## PART 9 — SETTINGS

### H — Settings Shell
```
Settings layout (grid grid-cols-1 md:grid-cols-[200px_1fr] gap-6 p-6):
  Left: SettingsNav (sticky top-6)
  Right: content
```

**SettingsNav:**
```
Section "Workspace" (text-[10px] uppercase text-muted-foreground tracking-wider mb-1):
  General | Time Tracking | Compliance

Section "Team":
  Members | Clients | Tags

Section "Developer":
  Webhooks

Section "Account":
  Profile

Active item: text-brand-orange font-medium bg-brand-orange/8
             border-l-2 border-brand-orange pl-[6px]
```

---

### H1–H3 — Workspace Settings
**File:** `app/(app)/settings/workspace/page.tsx`
**Access:** All roles view (read-only for non-Admin). Admin can edit.

#### Step 1 — General Card
```
Card bg-surface border border-border rounded-xl p-5:
  "General" text-sm font-semibold mb-4
  Fields (all disabled if not Admin):
    Workspace Name (Input)
    Logo URL (Input type="url")
    Timezone (Command popover Select)
    Date Format (ToggleGroup: "MM/DD/YYYY" | "DD/MM/YYYY")
      Active segment: bg-brand-orange text-white
    Currency (Select, ISO 4217 list)
    Default Hourly Rate (number input $, ABSENT for Viewer)
  [Admin only] "Save" (bg-brand-orange text-white, right-aligned)
```

#### Step 2 — Time Tracking Card
```
Rounding Mode (ToggleGroup: None | Nearest | Up | Down)
  Active: bg-brand-orange text-white
Rounding Interval Select (disabled when None)
Mandatory Description Switch (orange thumb)
Max Timer Duration Select
Past Entry Limit Select
```

#### Step 3 — Compliance Card
```
Rolling Lock Period Select
Approval Workflow Switch:
  Checked: orange thumb + "Enabled" badge (bg-brand-orange/10 text-brand-orange)
  Toggling OFF → AlertDialog with amber warning box

Idle Detection Switch:
  When enabled: Idle Timeout Select appears (animated height transition)
```

#### Step 4 — Danger Zone Card
```
border-destructive/25 rounded-xl p-5
"Danger Zone" text-sm font-semibold text-destructive mb-3
"Delete Workspace" row:
  Description text-sm text-muted-foreground
  "Delete Workspace" button: variant="outline" border-destructive/40
                              text-destructive hover:bg-destructive/5
  → AlertDialog: type workspace name to confirm
```

---

### H4 — Members & Invites
**File:** `app/(app)/settings/members/page.tsx`

#### Step 1 — Header
```
"Members & Invites" heading
[Admin only] "Invite Member" (bg-brand-orange text-white, UserPlus icon)
```

#### Step 2 — Members table
```
Card overflow-hidden:
  Table: MEMBER | ROLE | JOINED | ACTIONS

  Each row (h-[52px]):
    Avatar (30px, initials + gradient) + name (font-medium) + email (muted)
    Role: [Admin] DropdownMenu (manager/member/viewer only, NOT admin)
          selected item gets brand-orange check indicator
    Joined date text-xs text-muted-foreground
    [Admin] "Remove" ghost text-destructive UserMinus icon
            disabled (opacity-40) for sole Admin
            → AlertDialog confirmation

  Loading: skeleton rows
```

#### Step 3 — Invite flow (Admin only — hidden for others)

**State A — Form:**
```
Card "Invite New Member":
  Email input (full-width)
  Role cards (3 horizontal cards):
    Each: border rounded-xl p-3 cursor-pointer transition-all
    Default: bg-surface border-border hover:border-brand-orange/30
    Selected: bg-brand-orange/8 border-brand-orange
    Role name (font-semibold text-sm) + description (text-xs text-muted-foreground)
  "Generate Invite Link" (bg-brand-orange text-white full-width Link2 icon)
```

**State B — Success:**
```
Animated transition (Framer Motion height expand):
  CheckCircle2 (32px text-success) + "Invite link ready"
  "Share this link with {email}:"
  Input (read-only, font-mono text-xs bg-surface-raised)
    + Copy button (Clipboard → Check "Copied!" for 2s in text-success)
  "Expires in 7 days — {date}"
    CalendarClock icon + text-warning
  "Invite another" (ghost) + "Done" (variant="outline")
```

#### Step 4 — Pending invites (Admin only)
```
Card "Pending Invites" + count badge:
  Table: EMAIL | ROLE | EXPIRES | ACTIONS
  Expiring soon: text-warning + "Expiring soon" (bg-warning-muted rounded text-[10px] px-1.5)
  "Revoke" ghost text-destructive XCircle icon
    → AlertDialog confirmation
  Empty: "No pending invites" muted text
```

---

### H5 — Clients
**File:** `app/(app)/settings/clients/page.tsx`

#### Step 1 — Table
```
"Clients" header + "Add Client" (bg-brand-orange text-white, Manager/Admin only)
Search input (hover:border-brand-orange/40 focus:border-brand-orange)
Table: NAME | EMAIL | PHONE | HOURLY RATE* | PROJECTS | ACTIONS
*ABSENT for Viewer. Edit + Delete icons on hover.
```

#### Step 2 — Add/Edit Client Sheet
```
Sheet (side="right" w-[380px]):
  Name, Email, Phone, Hourly Rate ($)
  Save (bg-brand-orange text-white)
```

---

### H6 — Tags
**File:** `app/(app)/settings/tags/page.tsx`

```
"Tags" header + "Add Tag" (bg-brand-orange text-white, Manager/Admin)
Tag grid (flex flex-wrap gap-2):
  Each pill: bg at 15% opacity of tag.color, text-[tag.color]
             border border-[tag.color]/20 rounded-full px-3 py-1 text-xs font-medium
  Hover (Manager/Admin): pencil + trash icons appear
```

---

### H7 — Webhooks
**File:** `app/(app)/settings/webhooks/page.tsx`
**Admin only.**

```
Webhook cards: URL (font-mono truncated) + event badges + active Switch (orange) + edit + delete
Add Webhook Sheet: URL, events checklist (checkbox orange), secret, active toggle
Delivery logs: expandable per webhook, status badges
```

---

### H8 — Profile Settings
**File:** `app/(app)/settings/profile/page.tsx`

```
Profile form: name, avatar URL, email (disabled), timezone, weekly hours goal
  Save (bg-brand-orange text-white)

Change Password card (email accounts only):
  Current + new + confirm password inputs

Danger Zone card (border-destructive/25):
  "Delete Account" — blocked if sole Admin
  → AlertDialog confirmation
```

---

## PART 10 — SHARED COMPONENTS

### S1 — StatusBadge
**File:** `components/shared/StatusBadge.tsx`
```
Uses CSS variable colors from the token system.
rounded-md (not rounded-full) — modern rectangular badges.
Each status maps to its semantic color pair (muted bg + colored text + border).
```

### S2 — EmptyState
**File:** `components/shared/EmptyState.tsx`
```
Icon container: w-11 h-11 rounded-xl bg-brand-orange/8 flex items-center justify-center
Icon: text-brand-orange w-5 h-5
heading: text-sm font-semibold text-foreground
description: text-xs text-muted-foreground max-w-xs leading-relaxed
CTA button: bg-brand-orange text-white
```

### S3 — PageHeader
```
title: text-xl font-semibold tracking-tight text-foreground
actions: flex items-center gap-2 (right-aligned)
```

### S4 — ConfirmDialog (reusable AlertDialog)
```
Confirm button variant drives color:
  default → bg-brand-orange text-white
  destructive → bg-destructive text-white
Loading: spinner on confirm button
```

### S5 — ContinueButton (NEW)
**File:** `components/shared/ContinueButton.tsx`
```tsx
interface ContinueButtonProps {
  entryId: string
  entryStatus: EntryStatus
  workspaceId: string
  hasRunningTimer: boolean
}

// Absent (not rendered) for pending entries
// Shows ▶ (Play icon, 14px) ghost button
// Tooltip: "Continue this entry"
// hover: text-brand-orange bg-brand-orange/8
// If hasRunningTimer: opens AlertDialog before calling API
```

### S6 — DuplicateMenuItem (NEW)
**File:** `components/shared/DuplicateMenuItem.tsx`
```
DropdownMenuItem inside three-dot menu
"Duplicate" text + Copy icon (14px)
Absent for pending entries
On click: useDuplicateEntry(entryId) → showRoundingToast on success
```

---

## PART 11 — FRONTEND CODE STANDARDS

### Step-by-Step Screen Build Process

For every screen:

1. **API layer first** — `features/[feature]/api.ts` with typed functions
2. **Zod schemas** — `features/[feature]/schemas.ts` mirroring Pydantic models
3. **React Query hooks** — query factories, correct stale times, mutation invalidation
4. **Skeleton first** — write skeleton component before real component
5. **Empty state** — define empty state before data-rendering code
6. **Real component** — shadcn primitives, brand color tokens, business rules
7. **Wire form** — React Hook Form + Zod, map 422 errors to fields
8. **Pre-delivery checklist** — FRONTEND_SKILL.md Part 8

### Brand Color Application Rules

```typescript
// PRIMARY ACTIONS — always brand-orange
className="bg-brand-orange hover:bg-brand-orange-hover text-white"

// ACTIVE STATES — orange tint + orange border
className="bg-brand-orange/10 text-brand-orange border border-brand-orange/20"

// ACTIVE NAV — orange left border (sidebar signature)
className="bg-brand-orange/12 text-white border-l-2 border-brand-orange"

// FOCUS RINGS — orange instead of blue
className="focus-visible:ring-2 focus-visible:ring-brand-orange/40
           focus-visible:ring-offset-2 focus-visible:outline-none"

// INPUT FOCUS — orange border
className="focus:border-brand-orange focus:ring-2 focus:ring-brand-orange/20"

// DATA VALUES — always DM Mono
className="font-mono text-sm font-semibold text-foreground"

// MONEY — DM Mono green
className="font-mono text-sm text-success"

// SIDEBAR — always brand-navy bg
className="bg-brand-navy" // or CSS var: bg-[hsl(var(--sidebar-background))]
```

### Forbidden Patterns

```typescript
// ❌ Blue primary colors (use brand-orange instead)
className="bg-blue-600 text-blue-600 border-blue-500"

// ❌ Raw hex in className
className="bg-[#252F50] text-[#FE6900]"    // use token classes

// ❌ Any type
const x: any = ...

// ❌ Financial data visible to Viewer
<td className={isViewer ? 'hidden' : ''}>${amount}</td>  // must be absent

// ❌ Server data in Zustand
timerStore.setState({ projects: data })

// ❌ Non-lucide icons
import { FaPlay } from 'react-icons/fa'

// ❌ Continue/Duplicate on pending entries (must not render, not disable)
{entry.status !== 'pending' && <ContinueButton />}   // ✅ correct
<ContinueButton disabled={entry.status === 'pending'} /> // ❌ wrong

// ❌ Barrel imports
import { Button, Input } from '@/components/ui'
```

### Required Patterns

```typescript
// ✅ Brand-orange primary actions
<Button className="bg-brand-orange hover:bg-brand-orange-hover text-white">

// ✅ All states implemented
if (isLoading) return <Skeleton... />
if (isError) return <ErrorState onRetry={refetch} />
if (!data?.length) return <EmptyState ... />
return <RealContent data={data} />

// ✅ Viewer isolation — absent, not hidden
{role !== 'viewer' && <TableCell>{billableAmount}</TableCell>}

// ✅ Continue/Duplicate absent (not disabled) for pending
{entry.status !== 'pending' && (
  <>
    <ContinueButton entryId={entry.id} />
    <DuplicateMenuItem entryId={entry.id} />
  </>
)}

// ✅ Rounding toast after every save
onSuccess: (data) => { showRoundingToast(data.rounding) }

// ✅ Tooltip on disabled interactive elements (not absent — but disabled)
<Tooltip>
  <TooltipTrigger asChild>
    <span><Button disabled /></span>
  </TooltipTrigger>
  <TooltipContent>Reason why disabled</TooltipContent>
</Tooltip>

// ✅ Description draft hook in TimerBar
const { getDraft, saveDraft, clearDraft } = useDescriptionDraft(userId, workspaceId)
```

---

## PART 12 — EDGE CASES & AMBIGUITY RESOLUTION

**Q: Continue button — rendered but disabled, or absent?**
A: ABSENT for pending entries. Not rendered at all. The ContinueButton component
returns `null` when `entry.status === 'pending'`. This follows the same principle
as financial data for Viewers — absent, not merely disabled.

**Q: Duplicate — rendered but disabled, or absent?**
A: ABSENT for pending entries. DuplicateMenuItem returns null for pending.

**Q: What does "Continue" do when the running timer is for the same entry?**
A: Cannot happen — a running entry has `status = 'running'`, not `draft`.
Continue is only shown on `draft` and `approved` entries. Running entries show
a Stop button instead.

**Q: Weekly Report — what if date_from is not a Monday?**
A: The API accepts any date range (not restricted to Monday starts).
The frontend date picker defaults to the current Mon–Sun week but allows
custom range. The `INVALID_WEEK_START` error code only applies to the
`POST /approvals/submit` endpoint, not the weekly report.

**Q: Description draft — what if the user has two browser tabs open?**
A: The last write wins — localStorage is shared across tabs for the same
origin. This is acceptable. The draft is a best-effort recovery mechanism.

**Q: Weekly report — Member opens /reports/weekly directly?**
A: They see only their own row. The `user_id` filter is locked server-side
to their own ID. The user filter dropdown is not rendered in the UI for Members.

**Q: ThemeToggle on landing page vs app shell?**
A: The landing nav has a ThemeToggle (top-right, ghost icon). The app shell
sidebar has a ThemeToggle in the footer. Both call the same `useTheme()` hook.
They are synchronized automatically by next-themes.

**Q: What color is the "Today" date circle in the timesheet grid?**
A: `bg-brand-orange text-white` — consistent with all primary active indicators.

**Q: Recharts chart colors — use brand-orange?**
A: Yes. Billable bars: `#FE6900`. Non-billable: `hsl(var(--muted))`.
Tooltip background: `hsl(var(--surface))` with `hsl(var(--border))` border.

---

## PART 13 — ABOUT OTHER DOCUMENTS: COLOR SCHEME UPDATE

### Do other files need updating for the new color scheme?

**FRONTEND_SKILL.md — YES, needs one update:**
The CSS variable system in Part 1.3 currently shows blue (`#3B82F6`) as the
primary color. This must be updated to the brand-orange/navy system shown in
Part 0 of this blueprint. The design philosophy (Part 0–2), stack rules (Part 3),
and business rules (Part 4–6) are all correct and need no changes. Only the
color token definitions in §1.3 and §2.1 need replacing.

**PRD v1.3 — NO change needed.**
PRD does not specify colors. It specifies behavior and features.

**TRD v1.2 — NO change needed.**
TRD §7.10 says "semantic CSS variable tokens in globals.css" and references
FRONTEND_SKILL.md — which correctly defers color decisions to the design layer.
The TRD is color-agnostic by design.

**API Spec v1.1 — NO change needed.**
Backend has zero awareness of colors.

**DB Schema v2.1 — NO change needed.**
`projects.color` column stores a hex string. `#FE6900` is a valid entry.
No constraint changes needed.

**AGENT.md v1.1 — NO change needed.**
Agent behavioral rules have no color dependencies.

**Conclusion:** Only FRONTEND_SKILL.md §1.3 and §2.1 need their color token
definitions updated from blue-primary to orange-primary. All other documents
are unaffected. The update is isolated to one section of one file.

---

*Blueprint v2.0 complete.*
*Screens: 20 + 1 Landing Page = 21 total screens*
*Components: 9 modal/overlay + 8 shared = 17 components*
*New features: Continue, Duplicate, Description Draft, Weekly Report, Dashboard Continue — all fully specified*
*Brand: Navy #252F50 + Orange #FE6900 applied consistently across all screens*
*Aligned to: PRD v1.4 · TRD v1.3 · DB Schema v2.2 · API Spec v1.2 · FRONTEND_SKILL.md*

---

## PART 14 — SUPER ADMIN DASHBOARD (Phase 7.5)

> **Implementation gate:** Do not build any component in this section until
> Phase 7 is completed and approved AND Phase 2 (Workspace & Members) is
> confirmed complete with real data. The backend endpoints in Step 7.5.1–7.5.4
> must exist before any frontend work begins.

### SA0 — Super Admin Design Language

The Super Admin dashboard uses a **deliberately distinct visual identity**
from the main application. This is intentional — it prevents confusion
between the platform-level view and a regular workspace view.
PRIMARY SURFACE:    bg-zinc-950   (#09090B) — deeper than main app dark bg
SECONDARY SURFACE:  bg-zinc-900   (#18181B) — cards and panels
ACCENT COLOR:       #FE6900       — same brand-orange (consistency)
DANGER COLOR:       #EF4444       — same destructive red
TEXT PRIMARY:       #FAFAFA       — near-white
TEXT MUTED:         #71717A       — zinc-500
BORDER:             #27272A       — zinc-800
BADGE — ACTIVE:     bg-green-950 text-green-400 border-green-800
BADGE — DELETED:    bg-red-950 text-red-400 border-red-800
BADGE — SUPERADMIN: bg-orange-950 text-brand-orange border-orange-800

**Visual signature:**
The sidebar uses `bg-zinc-950` (darker than the main app's `bg-brand-navy`)
with an amber/orange "SUPER ADMIN" pill label beneath the logo mark. This
immediately communicates to the operator that they are in a privileged
platform-level context, not a regular workspace.

**Typography:** Same DM Sans + DM Mono stack as the main application.
All aggregate numbers use `font-mono`.

---

### SA1 — Super Admin Shell Layout
**File:** `app/superadmin/layout.tsx`

#### Step 1 — Auth Guard
```tsx
'use client'
// On mount: GET /users/me
// If is_superadmin === false OR request fails: redirect to /dashboard
// Never show any superadmin content before auth confirmed
// Loading state: full-screen zinc-950 bg with centered brand-orange spinner
```

#### Step 2 — Shell Structure
```tsx
<div className="flex h-screen bg-zinc-950 overflow-hidden">
  <SuperAdminSidebar />           {/* w-56 fixed */}
  <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
    <SuperAdminTopBar />          {/* h-[48px] */}
    <main className="flex-1 overflow-y-auto p-6 bg-zinc-950">
      {children}
    </main>
  </div>
</div>
```

#### Step 3 — SuperAdminSidebar
bg-zinc-950 border-r border-zinc-800 w-56
TOP (h-16 border-b border-zinc-800 px-4):
YT mark (30px bg-brand-orange rounded-lg "YT" text-white font-bold)
"Yusi" text-sm font-bold text-white + "Time" text-sm font-bold text-brand-orange
Below: "SUPER ADMIN" pill
bg-orange-950 text-brand-orange text-[9px] font-bold uppercase
tracking-widest px-2 py-0.5 rounded-full border border-orange-800
NAV ITEMS (px-3 py-2):
Section label "PLATFORM" (text-[9px] uppercase text-zinc-600 tracking-wider px-2 pt-3 pb-1)
LayoutDashboard → "Dashboard"      /superadmin
Building2       → "Workspaces"     /superadmin/workspaces
Users           → "Users"          /superadmin/users
Active item: bg-brand-orange/12 text-white border-l-2 border-brand-orange
pl-[6px] font-medium
Default item: text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60
FOOTER (border-t border-zinc-800 px-3 py-3):
Avatar (26px initials, bg-brand-orange text-white)
Name text-[12px] text-zinc-400 truncate flex-1
ThemeToggle (ghost, text-zinc-500)
Separator (my-2 border-zinc-800)
"← Back to App" link
ArrowLeft icon (12px) + "Back to App" text-[11px] text-zinc-500
hover:text-zinc-300 → navigates to /dashboard

#### Step 4 — SuperAdminTopBar
h-[48px] bg-zinc-900 border-b border-zinc-800
flex items-center justify-between px-6
LEFT: Breadcrumb
Current page name text-sm font-medium text-zinc-200
Separator + section name text-xs text-zinc-500
RIGHT:
"SUPER ADMIN SESSION" amber pill
bg-amber-950 text-amber-400 border border-amber-800
text-[10px] font-semibold uppercase tracking-wider px-3 py-1 rounded-full
AlertTriangle icon (10px) left
This pill is a persistent reminder that the operator is in a privileged context
---

### SA2 — Super Admin Stats Dashboard
**File:** `app/superadmin/page.tsx`
**API:** `GET /admin/stats`

#### Step 1 — Page Header
"Platform Overview" text-xl font-semibold text-zinc-100 tracking-tight
"Real-time statistics across all workspaces and users."
text-sm text-zinc-500 mt-1

#### Step 2 — Stats Cards Grid
grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-6
All cards: bg-zinc-900 border border-zinc-800 rounded-xl p-4
hover:border-zinc-700 transition-colors duration-200

**Card 1 — Total Workspaces**
Building2 icon (20px text-brand-orange) top-right
"WORKSPACES" text-[10px] uppercase tracking-wider text-zinc-500
font-mono text-3xl font-bold text-zinc-100 (the count)
"+{n} last 30 days" text-xs text-green-400 mt-1

**Card 2 — Total Users**
Users icon (20px text-brand-orange) top-right
"USERS" label
font-mono text-3xl font-bold text-zinc-100
"+{n} last 30 days" text-xs text-green-400

**Card 3 — Total Time Entries**
Clock icon (20px text-brand-orange) top-right
"TIME ENTRIES" label
font-mono text-3xl font-bold text-zinc-100
"All time" text-xs text-zinc-500

**Card 4 — Active Timers Right Now**
Timer icon (20px) — pulsing orange dot indicator left of icon
dot: w-2 h-2 bg-brand-orange rounded-full animate-pulse
"ACTIVE TIMERS" label
font-mono text-3xl font-bold text-brand-orange (orange = live data)
"Live count" text-xs text-zinc-500
Refresh every 30s via refetchInterval

**Card 5 — New Workspaces (30 days)**
TrendingUp icon (20px text-green-400)
"NEW WORKSPACES" label
font-mono text-3xl font-bold text-zinc-100
"Last 30 days" text-xs text-zinc-500

**Card 6 — New Users (30 days)**
UserPlus icon (20px text-green-400)
"NEW USERS" label
font-mono text-3xl font-bold text-zinc-100
"Last 30 days" text-xs text-zinc-500

#### Step 3 — Quick Links
"Quick Access" text-sm font-semibold text-zinc-400 mb-3
Two cards side by side (grid grid-cols-2 gap-3):
Card A: "All Workspaces →"
bg-zinc-900 border border-zinc-800 rounded-xl p-4
Building2 icon (24px text-brand-orange) + count
hover:border-brand-orange/40 cursor-pointer → /superadmin/workspaces
Card B: "All Users →"
Users icon (24px text-brand-orange) + count
hover:border-brand-orange/40 cursor-pointer → /superadmin/users

#### Step 4 — Loading State
6 skeleton cards matching exact card shapes
Skeleton className="bg-zinc-800" (darker skeleton for dark bg)

#### Step 5 — Error State
AlertTriangle (40px text-amber-400) centered
"Could not load platform stats"
"Retry" button (bg-brand-orange text-white)

---

### SA3 — All Workspaces List
**File:** `app/superadmin/workspaces/page.tsx`
**API:** `GET /admin/workspaces`

#### Step 1 — Header
"Workspaces" text-xl font-semibold text-zinc-100
"{total} total" badge (bg-zinc-800 text-zinc-400 text-xs px-2 py-0.5 rounded-md ml-2)
Right side:
Search input (bg-zinc-900 border-zinc-700 text-zinc-200 placeholder:text-zinc-500
focus:border-brand-orange rounded-lg h-9 w-[260px])
MagnifyingGlass icon left inside input

#### Step 2 — Workspaces Table
bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden
Table columns:
WORKSPACE | MEMBERS | TIMEZONE | APPROVAL | CREATED | STATUS | ACTIONS
Each row (h-[52px] border-b border-zinc-800 hover:bg-zinc-800/50):
WORKSPACE:
Logo avatar (28px, initials, bg-brand-orange/20 text-brand-orange)
OR logo image if logo_url set
Workspace name font-medium text-sm text-zinc-100
workspace.id text-[10px] text-zinc-600 font-mono (below name, on hover)
MEMBERS:
font-mono text-sm text-zinc-300
Users icon (12px text-zinc-600) left
TIMEZONE:
text-xs text-zinc-400 font-mono
APPROVAL:
"Enabled" badge: bg-green-950 text-green-400 border-green-800 text-[10px]
"Disabled" badge: bg-zinc-800 text-zinc-500 text-[10px]
CREATED:
text-xs text-zinc-400 font-mono
Formatted as "May 26, 2026"
STATUS:
"Active" badge: bg-green-950 text-green-400 border border-green-800
"Deleted" badge: bg-red-950 text-red-400 border border-red-800
(deleted_at IS NOT NULL → Deleted)
ACTIONS:
Eye icon button → /superadmin/workspaces/{id}
hover: text-brand-orange bg-brand-orange/8 rounded-md p-1.5
Tooltip: "View workspace"

#### Step 3 — Pagination
Standard limit-offset pagination controls
"Showing {from}–{to} of {total}"
Previous / Next buttons (bg-zinc-800 border-zinc-700 text-zinc-300)
Active page: bg-brand-orange text-white

#### Step 4 — Loading State
10 × TableRowSkeleton with bg-zinc-800 skeleton color

#### Step 5 — Empty State
Building2 (40px text-zinc-600)
"No workspaces found"

---

### SA4 — Workspace Detail
**File:** `app/superadmin/workspaces/[id]/page.tsx`
**API:** `GET /admin/workspaces/{id}`
**Also uses:** `GET /workspaces/{id}` (via synthetic member bypass),
`GET /workspaces/{id}/members`

#### Step 1 — Header
Back link: "← All Workspaces" text-sm text-brand-orange → /superadmin/workspaces
Workspace name text-2xl font-bold text-zinc-100
workspace.id text-xs text-zinc-600 font-mono mt-0.5
Status badge + Created date text-xs text-zinc-500

#### Step 2 — Info Cards Row
grid grid-cols-2 md:grid-cols-4 gap-3 mb-5
Card: Members count (font-mono text-2xl font-bold text-zinc-100)
Card: Timezone (font-mono text-sm text-zinc-300)
Card: Currency (font-mono text-sm text-zinc-300)
Card: Approval Workflow (enabled/disabled badge)

#### Step 3 — Settings Panel
bg-zinc-900 border border-zinc-800 rounded-xl p-5 mb-4
"Workspace Settings" text-sm font-semibold text-zinc-400 mb-4
Two-column grid (grid-cols-2 gap-x-8 gap-y-3):
Each setting row:
Label text-xs text-zinc-500 uppercase tracking-wider
Value text-sm font-medium text-zinc-200 (or font-mono for numbers)
Settings shown:
Rounding Mode | Rounding Interval
Lock Period (days) | Past Entry Limit (days)
Mandatory Description | Max Timer Duration
Idle Detection | Idle Timeout
Approval Workflow | Date Format

#### Step 4 — Members Table
"Members ({count})" text-sm font-semibold text-zinc-400 mb-3
bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden
Columns: MEMBER | ROLE | JOINED | INVITED BY
Each row (h-[48px]):
Avatar (26px) + name text-sm text-zinc-200 + email text-[11px] text-zinc-500
Role badge (same status badge colors as main app but on dark zinc background)
Joined date text-xs text-zinc-400 font-mono
Invited by name text-xs text-zinc-500 (or "Workspace Creator")

#### Step 5 — Danger Zone Panel (READ ONLY in this pass)
border border-red-900/40 rounded-xl p-5
"Workspace Info" text-sm font-semibold text-red-400 mb-3
Shows deleted_at if set:
"Scheduled for deletion: {date}" bg-red-950 text-red-400 rounded-lg p-3
CalendarX icon + date font-mono
If not deleted:
"Workspace is active" bg-green-950 text-green-400 rounded-lg p-3
CheckCircle2 icon + "No deletion scheduled"
Note text-xs text-zinc-600:
"Workspace management actions (delete, restore) are performed
via direct database access in this phase."

---

### SA5 — All Users List
**File:** `app/superadmin/users/page.tsx`
**API:** `GET /admin/users`

#### Step 1 — Header
"Users" text-xl font-semibold text-zinc-100
"{total} total" badge (bg-zinc-800)
Right: Search input (same style as SA3)
+ Filter: "All" | "Super Admins" | "Inactive" (tab pills)

#### Step 2 — Users Table
bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden
Columns: USER | WORKSPACES | SUPER ADMIN | ACTIVE | JOINED | ACTIONS
Each row (h-[52px]):
USER:
Avatar (28px initials, gradient)
Name font-medium text-sm text-zinc-100
Email text-[11px] text-zinc-500
WORKSPACES:
font-mono text-sm text-zinc-300
Count of workspace memberships
SUPER ADMIN:
"Yes" badge: bg-orange-950 text-brand-orange border border-orange-800 text-[10px]
"No" text-zinc-600 text-[11px] (not a badge — de-emphasized)
ACTIVE:
"Active" badge: bg-green-950 text-green-400 border-green-800 text-[10px]
"Inactive" badge: bg-zinc-800 text-zinc-500 text-[10px]
(is_active=FALSE → Inactive, anonymized accounts)
JOINED:
text-xs text-zinc-400 font-mono
ACTIONS:
Eye icon → /superadmin/users/{id}
Tooltip: "View user"

#### Step 3 — Super Admin filter tab
"Super Admins" tab shows only users where is_superadmin=TRUE
Implemented as client-side filter on the fetched data
(platform will have very few super admins — no server-side filter needed)

---

### SA6 — User Detail
**File:** `app/superadmin/users/[id]/page.tsx`
**API:** `GET /admin/users/{id}`

#### Step 1 — Header
Back link: "← All Users" text-sm text-brand-orange
Avatar (48px, initials, gradient) + name text-2xl font-bold text-zinc-100
Email text-sm text-zinc-400 font-mono
user.id text-xs text-zinc-600 font-mono mt-0.5
Status badges row:
is_active badge (Active/Inactive)
is_superadmin badge (shown only if TRUE:
"SUPER ADMIN" bg-orange-950 text-brand-orange border-orange-800
Crown icon (12px) left)

#### Step 2 — Profile Info Card
bg-zinc-900 border border-zinc-800 rounded-xl p-5 mb-4
Two-column grid:
Full Name | Email
Timezone | Weekly Hours Goal
Google ID (font-mono text-xs, or "—" if null)
Created At | Last Updated

#### Step 3 — Workspace Memberships Table
"Workspace Memberships ({count})" text-sm font-semibold text-zinc-400 mb-3
bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden
Columns: WORKSPACE | ROLE | JOINED
Each row (h-[48px]):
Workspace name text-sm text-zinc-200
workspace_id text-[10px] text-zinc-600 font-mono (below name, de-emphasized)
Role badge (same colors as main app)
Joined date text-xs text-zinc-400 font-mono
"View →" link text-xs text-brand-orange → /superadmin/workspaces/{workspace_id}
Empty state:
"This user has no workspace memberships."
text-sm text-zinc-500 py-6 text-center

#### Step 4 — Account Status Panel
bg-zinc-900 border border-zinc-800 rounded-xl p-5
"Account Status" text-sm font-semibold text-zinc-400 mb-4
is_active:
Active: CheckCircle2 text-green-400 + "Account is active"
Inactive: XCircle text-red-400 + "Account has been anonymized"
+ anonymized email shown in font-mono text-xs text-zinc-600
is_superadmin:
TRUE: Crown icon text-brand-orange + "Platform Super Admin"
+ "This account has unconditional access to all platform endpoints."
text-xs text-zinc-500 mt-1
FALSE: (section hidden entirely)
Note text-xs text-zinc-600 mt-4:
"User management actions (anonymize, grant super admin) are performed
via direct database access in this phase."

---

### SA7 — Super Admin Navigation Addition to Main App Sidebar

The main app Sidebar (in the regular workspace shell) must show a subtle
Super Admin link for users where `is_superadmin=true`. This link is
**completely absent from the DOM** for all other users.

**File:** `web/src/features/layout/components/Sidebar.tsx`

Add at the bottom of the nav section, before the footer, only when `is_superadmin=true`:

```tsx
{currentUser?.is_superadmin && (
  <>
    <div className="mx-3 my-2 border-t border-white/6" />
    <div className="px-2 pb-1">
      <span className="text-[9px] font-semibold text-white/25 uppercase tracking-[0.08em] px-2">
        Platform
      </span>
    </div>
    <Link href="/superadmin">
      <div className={cn(
        "flex items-center gap-2.5 px-2 py-2 rounded-lg text-[13px] mx-1 transition-all duration-120",
        pathname.startsWith('/superadmin')
          ? "bg-brand-orange/12 text-white font-medium border-l-2 border-brand-orange pl-[6px]"
          : "text-white/45 hover:text-white/80 hover:bg-white/5"
      )}>
        <Crown className="w-4 h-4 flex-shrink-0" />
        <span>Super Admin</span>
        <span className="ml-auto text-[9px] bg-orange-950 text-brand-orange
                         border border-orange-800 px-1.5 py-0.5 rounded font-bold">
          SA
        </span>
      </div>
    </Link>
  </>
)}
```

**Key rules:**
- `{currentUser?.is_superadmin && ...}` — absent from DOM, not hidden
- The "SA" badge in the nav item serves as a persistent reminder
- Link goes to `/superadmin` (the stats dashboard home)
- Active state when `pathname.startsWith('/superadmin')`

---

### SA8 — Type Definitions

**File:** `web/src/features/superadmin/types.ts` *(new file)*

```typescript
export interface WorkspaceAdminView {
  id: string
  name: string
  logo_url: string | null
  default_timezone: string
  currency: string
  member_count: number
  approval_workflow_enabled: boolean
  deleted_at: string | null
  created_at: string
}

export interface UserAdminView {
  id: string
  full_name: string
  email: string
  is_superadmin: boolean
  is_active: boolean
  workspace_count: number
  created_at: string
}

export interface UserAdminDetail extends UserAdminView {
  avatar_url: string | null
  timezone: string | null
  workspaces: WorkspaceMembershipView[]
}

export interface WorkspaceMembershipView {
  workspace_id: string
  workspace_name: string
  role: string
  joined_at: string
}

export interface PlatformStats {
  total_workspaces: number
  total_users: number
  total_time_entries: number
  active_timers_now: number
  new_workspaces_last_30_days: number
  new_users_last_30_days: number
}
```

---

### SA9 — React Query Hooks

**File:** `web/src/features/superadmin/hooks.ts` *(new file)*

```typescript
export const superAdminKeys = {
  stats:      () => ['superadmin', 'stats'] as const,
  workspaces: (page: number) => ['superadmin', 'workspaces', page] as const,
  workspace:  (id: string) => ['superadmin', 'workspace', id] as const,
  users:      (page: number) => ['superadmin', 'users', page] as const,
  user:       (id: string) => ['superadmin', 'user', id] as const,
}

// Stale times:
// stats:      30_000 (30s, with refetchInterval: 30_000 for active timers)
// workspaces: 60_000
// workspace:  60_000
// users:      60_000
// user:       60_000
```

---

*Blueprint v2.1 complete.*
*Screens: 20 + 1 Landing Page + 5 Super Admin screens = 26 total screens*
*Components: 9 modal/overlay + 8 shared + 3 Super Admin shell = 20 components*
*New features (v2.1): Super Admin Dashboard — SA1 through SA9 fully specified*
*Brand: Navy #252F50 + Orange #FE6900 applied consistently. Super Admin uses Zinc palette with Orange accent.*
*Aligned to: PRD v1.4 · TRD v1.3 · DB Schema v2.2 · API Spec v1.2 · FRONTEND_SKILL.md*