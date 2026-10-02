# ORBIT — Design System & UI Specification

## Brand Identity

| Element | Specification |
|---------|---------------|
| **Product Name** | ORBIT |
| **Tagline** | Your Goal. Your Path. Your ORBIT. |
| **Logo** | `/public/orbit-logo.svg` — orbiting rings with indigo/cyan/emerald gradient |
| **Favicon** | Same as logo |

---

## Color Palette (CSS Custom Properties)

```css
:root {
  /* Dark theme (only supported theme) */
  --color-surface: #0F131D;
  --color-surface-container: #1A1F2E;
  --color-surface-container-low: #151A2A;
  --color-surface-container-lowest: #0F131D;
  --color-surface-container-high: #23293A;
  --color-surface-container-highest: #2D3448;

  --color-on-surface: #E8EAF0;
  --color-on-surface-variant: #9AA3B2;
  --color-on-surface-variant-muted: #6E7681;

  --color-primary: #4F46E5;        /* Indigo */
  --color-primary-container: #3A35C4;
  --color-on-primary: #FFFFFF;

  --color-secondary: #4CD7F6;      /* Cyan */
  --color-secondary-container: #0EA5C8;
  --color-on-secondary: #0F131D;

  --color-tertiary: #4EDEA3;       /* Emerald */
  --color-tertiary-container: #0EB87A;
  --color-on-tertiary: #0F131D;

  --color-outline: #3D4455;
  --color-outline-variant: #2D3448;

  --color-error: #F43F5E;          /* Rose */
  --color-error-container: #9F1239;

  --color-warning: #F59E0B;        /* Amber */
  --color-warning-container: #92400E;

  /* Status colors (mapped to semantic tokens) */
  --color-verified: var(--color-tertiary);
  --color-verified-bg: rgba(78, 222, 163, 0.15);
  --color-in-progress: var(--color-warning);
  --color-in-progress-bg: rgba(245, 158, 11, 0.15);
  --color-available: var(--color-secondary);
  --color-available-bg: rgba(76, 215, 246, 0.15);
  --color-locked: var(--color-outline);
  --color-locked-bg: rgba(35, 41, 58, 0.8);
}
```

### Tailwind Mapping (`tailwind.config.js`)
```js
theme: {
  extend: {
    colors: {
      surface: 'var(--color-surface)',
      'surface-container': 'var(--color-surface-container)',
      // ... all tokens mapped
      primary: 'var(--color-primary)',
      'primary-container': 'var(--color-primary-container)',
      secondary: 'var(--color-secondary)',
      tertiary: 'var(--color-tertiary)',
      outline: 'var(--color-outline)',
      'outline-variant': 'var(--color-outline-variant)',
    },
    fontFamily: {
      headline: ['Plus Jakarta Sans', 'sans-serif'],
      body: ['Inter', 'sans-serif'],
    },
  }
}
```

---

## Typography

| Role | Font | Weight | Size | Line Height |
|------|------|--------|------|-------------|
| Headline Large | Plus Jakarta Sans | 700 | 2.25rem (36px) | 1.2 |
| Headline Medium | Plus Jakarta Sans | 600 | 1.5rem (24px) | 1.3 |
| Headline Small | Plus Jakarta Sans | 600 | 1.125rem (18px) | 1.4 |
| Body Large | Inter | 400 | 1.125rem (18px) | 1.6 |
| Body Medium | Inter | 400 | 1rem (16px) | 1.6 |
| Body Small | Inter | 400 | 0.875rem (14px) | 1.5 |
| Caption | Inter | 500 | 0.75rem (12px) | 1.4 |
| Mono | JetBrains Mono / SF Mono | 400 | 0.875rem | 1.5 |

### Utility Classes
```css
.font-headline-lg { font-family: var(--font-headline); font-weight: 700; font-size: 2.25rem; }
.font-headline-md { font-family: var(--font-headline); font-weight: 600; font-size: 1.5rem; }
.font-headline-sm { font-family: var(--font-headline); font-weight: 600; font-size: 1.125rem; }
.font-body-md { font-family: var(--font-body); font-weight: 400; font-size: 1rem; }
.font-body-sm { font-family: var(--font-body); font-weight: 400; font-size: 0.875rem; }
.font-mono { font-family: 'JetBrains Mono', 'SF Mono', monospace; }
```

---

## Spacing & Layout

| Scale | Value | Usage |
|-------|-------|-------|
| `--space-1` | 4px | Icon gaps, tight padding |
| `--space-2` | 8px | Button padding, small gaps |
| `--space-3` | 12px | Card padding, form gaps |
| `--space-4` | 16px | Section padding, modal padding |
| `--space-5` | 20px | Large card padding |
| `--space-6` | 24px | Page section gaps |
| `--space-8` | 32px | Major section separation |
| `--space-10` | 40px | Hero/marketing sections |

### Container
```css
.container { max-width: 80rem (1280px); margin: 0 auto; padding: 0 1.5rem; }
```
Responsive breakpoints: `sm: 640px`, `md: 768px`, `lg: 1024px`, `xl: 1280px`

---

## Components

### Buttons
```css
/* Primary — main CTA */
.btn-primary { @apply bg-primary text-on-primary font-bold rounded-xl px-6 py-3 shadow-lg shadow-indigo-900/30 hover:bg-primary/90 transition-all; }

/* Secondary — alternative actions */
.btn-secondary { @apply bg-secondary-container/50 text-secondary border border-secondary/50 font-bold rounded-xl px-6 py-3 hover:bg-secondary-container/70 transition-all; }

/* Ghost — subtle actions */
.btn-ghost { @apply text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest transition-colors; }

/* Danger — destructive */
.btn-danger { @apply bg-rose-500 text-white font-bold rounded-xl px-6 py-3 hover:bg-rose-600 transition-colors; }

/* Disabled */
.btn-disabled { @apply opacity-50 cursor-not-allowed; }
```

### Cards
```css
.card { @apply rounded-2xl bg-surface-container border border-outline-variant/60 shadow-xl; }
.card-elevated { @apply card shadow-2xl; }
.card-interactive { @apply card hover:border-primary/40 transition-all cursor-pointer; }
```

### Form Inputs
```css
.input { @apply w-full p-3 rounded-xl bg-surface-container-high border border-outline-variant/60 text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-all; }
.input-error { @apply input border-rose-500/60 focus:ring-rose-500/40; }
.label { @apply block text-sm font-semibold text-on-surface mb-1.5; }
```

### Status Pills
```css
.pill-verified { @apply bg-tertiary-container/30 text-tertiary border border-tertiary/40 px-2.5 py-0.5 rounded-full text-xs font-bold; }
.pill-in-progress { @apply bg-amber-950/40 text-amber-400 border border-amber-500/40 px-2.5 py-0.5 rounded-full text-xs font-bold; }
.pill-available { @apply bg-surface-container-highest text-secondary border border-secondary/30 px-2.5 py-0.5 rounded-full text-xs font-bold; }
.pill-locked { @apply bg-surface-container-low text-outline border border-outline-variant/40 px-2.5 py-0.5 rounded-full text-xs font-bold; }
.pill-online { @apply bg-tertiary-container/30 text-tertiary border border-tertiary/30 px-2 py-0.5 rounded-full text-[10px] font-bold; }
.pill-offline { @apply bg-amber-950/40 text-amber-400 border border-amber-500/40 px-2 py-0.5 rounded-full text-[10px] font-bold; }
```

### Modals
```css
.modal-overlay { @apply fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4; }
.modal-content { @apply w-full max-w-2xl bg-surface-container border border-outline-variant/60 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]; }
.modal-header { @apply p-5 bg-surface-container-high border-b border-outline-variant/50 flex items-center justify-between shrink-0; }
.modal-body { @apply p-6 overflow-y-auto flex flex-col gap-5; }
```

---

## Iconography

- **Library**: Lucide React (consistent 24x24 grid)
- **Sizes**: `w-3.5 h-3.5` (14px) default, `w-4 h-4` (16px) buttons, `w-5 h-5` (20px) headers
- **Colors**: Inherit `currentColor` (text color) or explicit semantic color

### Key Icons by Feature
| Feature | Icon |
|---------|------|
| Goal/Intake | `Compass` |
| Diagnostic | `Zap` |
| Route/Graph | `Layers` |
| Verification | `Award` / `ShieldCheck` |
| Replan | `RotateCcw` |
| Unlock | `Unlock` / `Lock` |
| Verified | `CheckCircle2` |
| Warning | `AlertCircle` |
| Loading | `Loader2` |

---

## Motion & Animation

| Animation | Duration | Easing | Usage |
|-----------|----------|--------|-------|
| `transition-all` | 200ms | `ease-out` | Default for all interactive elements |
| `animate-spin` | 1s | linear | Loading spinners |
| `animate-ping` | 1s | ease-in-out | Online status indicator |
| `animate-pulse` | 2s | ease-in-out | Selection ring on graph nodes |
| `animate-fadeIn` | 300ms | ease-out | Modal/receipt appear |

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Accessibility

### WCAG AA Compliance
- **Contrast**: All text ≥ 4.5:1 (verified in dark theme)
- **Focus**: Visible ring on all interactive elements (`focus:ring-2 focus:ring-primary/40`)
- **ARIA**: `role="alert"` for errors, `aria-label` on icon buttons
- **Keyboard**: All modals trap focus, `Esc` closes, `Tab` navigates
- **Screen readers**: Semantic HTML (`<nav>`, `<main>`, `<section>`, `<button>`)

### Color Blind Safe
- Status colors verified with deuteranopia/protanopia simulation
- Never rely on color alone — always include icon + text label

---

## Responsive Behavior

| Component | Mobile (< 768px) | Desktop (≥ 768px) |
|-----------|------------------|-------------------|
| Header | Stacked brand + nav scroll | Side-by-side, fixed |
| Diagnostic | Full-width question | 2/3 question + 1/3 progress |
| Route | Stacked phases | Full timeline |
| Graph | Scrollable SVG | 2/3 canvas + 1/3 detail panel |
| Modals | Full-screen (90vh) | Centered (max-w-2xl/4xl) |

---

## Loading & Empty States

### Loading Skeleton
```jsx
<div className="w-full min-h-[200px] rounded-2xl bg-surface-container-lowest border border-outline-variant/60 flex flex-col items-center justify-center gap-3">
  <Loader2 className="w-10 h-10 text-primary animate-spin" />
  <p className="text-sm font-bold text-on-surface">Loading…</p>
  <p className="text-xs text-on-surface-variant">Context-specific message</p>
</div>
```

### Empty State
```jsx
<div className="w-full min-h-[200px] rounded-2xl bg-surface-container-lowest border border-outline-variant/60 flex flex-col items-center justify-center text-center gap-2">
  <Icon className="w-10 h-10 text-outline" />
  <h4 className="text-base font-bold text-on-surface">Empty Title</h4>
  <p className="text-xs text-on-surface-variant max-w-md">Helpful description</p>
  <button className="mt-4 px-4 py-2 rounded-xl bg-primary text-on-primary text-xs font-bold">Action</button>
</div>
```

### Error State
```jsx
<div className="w-full p-8 rounded-2xl bg-rose-950/30 border border-rose-500/50 flex flex-col items-center justify-center text-center gap-3">
  <AlertCircle className="w-10 h-10 text-rose-400" />
  <h4 className="text-base font-bold text-rose-300">Operation Failed</h4>
  <p className="text-xs text-on-surface-variant max-w-md">Friendly message</p>
  <button className="px-4 py-2 rounded-xl bg-rose-500 hover:bg-rose-600 text-white text-xs font-bold">Retry</button>
</div>
```

---

## Future: Landing Page (Post-Hackathon)

### Planned Sections
1. **Hero** — Tagline + animated orbit logo + "Start Free" CTA
2. **How It Works** — 4-step illustrated workflow (Goal → Graph → Diagnose → Verify)
3. **Demo Graph** — Interactive SVG preview (static fallback)
4. **Testimonials** — Placeholder for beta users
5. **Footer** — GitHub, Twitter, Privacy, Terms

### Design Tokens for Landing
- Extend current system (same colors, fonts, spacing)
- Add gradient backgrounds: `bg-gradient-to-br from-indigo-900/50 via-surface to-cyan-900/20`
- Animation: Framer Motion for scroll reveals
- Responsive: Mobile-first, max-width 1280px

### NOT in Scope for Hackathon
- No marketing copywriting
- No SEO/meta tags beyond basics
- No analytics/tracking
- No waitlist/form backend

---

## Design QA Checklist (Pre-Demo)

- [ ] Dark theme only — no light mode flashes
- [ ] All buttons have hover/focus/disabled states
- [ ] Modals trap focus, close on Esc/overlay click
- [ ] Graph SVG renders at all viewport widths
- [ ] Route cards don't overflow on mobile
- [ ] Status pills use correct semantic colors
- [ ] Confetti fires on verification pass
- [ ] No console errors in production build
- [ ] Lint: 0 errors (warnings OK)