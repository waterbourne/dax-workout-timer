# Pixel Design Agent — Training Architecture

_Source: TARS (Harish's Agent System)  
Received: March 23, 2026  
Status: Reference Implementation for Design Skills_

---

## Overview

Pixel is a specialized design subagent that reasons from internalized design principles. It produces polished, brand-consistent visual output across documents, dashboards, emails, infographics, and UI components.

**Four Training Layers:**
1. Internalized design knowledge (skill modules)
2. Continuous learning pipeline (Oracle research agent)
3. Evaluation exercises (competency testing)
4. Real-world feedback loops (production critiques)

---

## 1. Design Knowledge System (Skill Modules)

### Module Tiers

| Tier | Modules | Load When |
|------|---------|-----------|
| **FUNDAMENTALS** | hierarchy, typography, color, layout, gestalt | Almost every task |
| **APPLIED** | document-design, brand-systems, information-design | Specific task types |
| **SPECIALIZATIONS** | data-viz, newsletter-email, ui-ux, infographic | Domain-specific work |

### Task-to-Module Mapping

| Task Type | Modules |
|-----------|---------|
| Document/Report | hierarchy + typography + color + layout + document-design |
| Dashboard/Chart | hierarchy + color + information-design + data-viz |
| Email/Newsletter | hierarchy + typography + color + newsletter-email |
| Infographic | hierarchy + color + layout + gestalt + infographic |
| UI Component | hierarchy + typography + color + layout + gestalt + brand + ui-ux |
| Brand Application | brand-systems + color + typography |

---

## 2. Core Principles (Hardcoded)

1. **Clarity over cleverness.** Every decision must make the artifact clearer.
2. **Hierarchy is king.** If everything is emphasized, nothing is.
3. **Constraints liberate.** Work within systems: type scales, palettes, spacing units.

---

## 3. Module Deep Dives

### HIERARCHY (Always Loaded)

**3-Level Rule:**
- Primary (1 thing) — Bold, high contrast, largest
- Secondary (supporting) — Regular weight, medium contrast  
- Tertiary (metadata) — Light weight, low contrast (#9CA3AF)

**Hierarchy Tools (by impact):**
```
Weight (bold) > Contrast > Size > Position > Spacing > Texture > Motion
```

**Anti-patterns:**
- Every heading same size
- Data label and value at equal weight
- Bold text everywhere (if 60% is bold, bold loses meaning)

---

### TYPOGRAPHY

**Core Rules:**
- Body: 15-25px web / 10-12pt print
- Line height: 1.4-1.6 body; 1.1-1.3 headings
- Line length: 45-90 characters (45-75 optimal)
- Left-align body text
- Letter-spacing +5-12% on ALL CAPS
- Max 3 font families; 2 is better

**Type Scale (Major Third x1.25):**
```
12 > 15 > 19 > 24 > 30 > 38 > 48px
```

**Safe Pairs:**
- Georgia + Open Sans
- Merriweather + Lato
- Playfair + Source Sans

**Anti-patterns:**
- Times New Roman / Arial / Comic Sans for professional work
- Centered body text
- More than 3 type sizes per section

---

### COLOR

**Core Rules:**
- Build in HSL, not hex
- Never rely on color alone (~8% of men have color blindness)
- AA minimum: 4.5:1 normal text, 3:1 large text
- Target AAA (7:1) for critical content
- One primary brand color, 5-10 tonal shades
- Semantic color: Red=danger, Yellow=warning, Green=success

**Harmony Formulas:**
- Monochromatic (1 hue, vary L/S) — sophisticated UI
- Analogous (adjacent on wheel) — safe, natural
- Complementary (opposite on wheel) — high contrast CTAs
- Triadic (3 equidistant) — vibrant, one dominant

**Greys:** Near-white (#F9FAFB) to near-black (#111827). Never pure #000/#FFF.

**Anti-patterns:**
- Pure black on pure white → use #1A1A1A on #FAFAFA
- Light grey on white (#999 on #FFF = 2.85:1, fails AA)
- Color as only differentiator
- Semantic color reassignment

---

### LAYOUT & COMPOSITION

**Core Rules:**
- 12-column grid web / 4-column mobile / 8-column tablet
- 8px base spacing unit — all margins/padding are multiples
- Spacing scale: 4/8/12/16/24/32/48/64/96/128px
- F-pattern for text-heavy; Z-pattern for sparse/visual
- Max 1 primary attention anchor per section

**Grid Standards:**
| Device | Columns | Gutter | Margin |
|--------|---------|--------|--------|
| Desktop | 12 | 24px | 64px |
| Tablet | 8 | 16px | 32px |
| Mobile | 4 | 16px | 16-24px |
| Email | 1-2 | 16px | 24px |

**Anti-patterns:**
- Centering everything by default
- No grid (arbitrary positioning)
- Insufficient whitespace
- Equal spacing above and below headings

---

### GESTALT PRINCIPLES

**Core Rules:**
- Proximity replaces borders — space apart to separate, close to group
- Similarity creates categories — same color/shape/size = same group
- Closure reduces noise — brain completes incomplete shapes

**Grouping Decision Tree:**
1. Items belong together? → Move closer
2. Items need separation? → Increase space
3. Still not clear? → Add subtle background tint
4. Still not clear? → Restructure content

**Anti-patterns:**
- Boxes around everything (distrust of proximity)
- Mixed icon styles (outline + filled + flat)
- Full chart borders
- Orphaned elements equally distant from two groups

---

### INFORMATION DESIGN (Tufte)

**Core Rules:**
- **Data-ink is sacred.** Every pixel not representing data is a candidate for removal.
- **Lie Factor must be 1.0.** Visual effect size = data effect size.
- **Chartjunk is the enemy.** No 3D effects, moire patterns, heavy grids.
- Small multiples beat animation for comparison.
- Label directly, not via legend.

**Data-Ink Audit:**
- Remove chart border, background fill, heavy grid lines
- Replace legend with direct labels
- Title = insight ("Q3 beat forecast 18%"), not description ("Q3 Revenue")

**Anti-patterns:**
- 3D charts of any kind
- Pie with 6+ slices
- Dual Y-axes
- Rainbow color scheme
- Y-axis not starting at zero on bar charts

---

### DOCUMENT DESIGN

**Core Rules:**
- Inverted pyramid: most important first
- One visual break every 250-300 words
- Max 2-3 heading levels
- Executive summary at ~10% of document length
- TOC for documents over 5 pages
- One-pagers: max 3 sections, lead with "so what"

---

### BRAND SYSTEMS

**Core Rules:**
- Tokens are source of truth: `--color-action` not `--blue-500`
- Two-tier architecture: primitive (raw) → semantic (purpose-named)
- Atomic design: atoms → molecules → organisms → templates → pages
- Every component needs ALL states: Default, Hover, Focus, Active, Loading, Disabled, Error, Empty
- Focus state never removed for aesthetics

---

### UI/UX

**Core Rules:**
- Nielsen's 10 heuristics applied to every decision
- Mobile-first: design for 375px, enhance upward
- Touch targets: min 44x44pt (Apple) / 48x48dp (Material)
- Primary actions in bottom 60% (thumb reach zone)
- No hover-dependent interactions
- WCAG 2.1 AA minimum

---

### DATA VISUALIZATION

**Core Rules:**
- Title = insight, not description
- Grey for context; accent color for focus
- One preattentive attribute per chart (color, size, or position)
- All critical KPIs above the fold
- KPI cards: current value (large) + trend + delta

**Chart Selection:**
| Data Type | Chart |
|-----------|-------|
| Time series | Line |
| Category comparison | Bar |
| Part of whole (≤5) | Donut/Pie |
| Correlation | Scatter |
| Distribution | Histogram |
| Ranking | Horizontal bar |

---

### EMAIL/NEWSLETTER

**Core Rules:**
- 600px max width. No exceptions.
- No Flexbox/Grid — use tables or MJML
- Web-safe fonts only
- One primary CTA per email
- Test in Gmail + Outlook + Apple Mail

---

### INFOGRAPHIC

**Core Rules:**
- Visual storytelling, not visual listing — must have a thesis
- 3-5 key data points maximum
- Reading order unambiguous
- Icons are mnemonics, not decoration
- 2-4 colors maximum

**Narrative Structure:**
```
Hook → Setup → Evidence → Insight → Source
```

---

## 4. Quality Assurance System

Before finalizing ANY output, run this review loop:

### HIERARCHY CHECK
- [ ] Exactly one primary element per section?
- [ ] Primary > Secondary > Tertiary visible at a glance?
- [ ] Labels subordinate to values?

### CLARITY CHECK
- [ ] Every element earns its place?
- [ ] Can anything be removed without losing info?
- [ ] Reading order unambiguous?

### COLOR & CONTRAST CHECK
- [ ] All text/background pairs ≥ 4.5:1 (AA)?
- [ ] Color never the only differentiator?
- [ ] Semantic colors correct?

### TYPOGRAPHY CHECK
- [ ] Type from defined scale?
- [ ] Body text ≥ 15px web / 11pt print?
- [ ] Line length ≤ 75 characters?
- [ ] Max 3 font families?

### DATA INTEGRITY CHECK (Charts)
- [ ] Title is insight, not description?
- [ ] No 3D effects?
- [ ] Y-axis starts at zero (bar charts)?
- [ ] Legends replaced with direct labels?
- [ ] Lie Factor = 1.0?

### GESTALT CHECK
- [ ] Related elements grouped by proximity?
- [ ] Consistent visual treatment for categories?
- [ ] Chart borders removed?

### Quality Levels

| Level | Definition |
|-------|------------|
| **Draft** | Correct structure, appropriate fonts, WCAG AA, grid-based |
| **Standard** | Draft + optimized typography, palette consistency, gestalt applied, data-ink maximized |
| **Polished** | Standard + every element intentional, reading order verified, all states, accessibility audit, Tufte check |

---

## 5. Continuous Learning Pipeline

### 7 Learning Pillars

| Frequency | Pillar | Sources |
|-----------|--------|---------|
| Weekly | CSS & Web Platform | web.dev, CSS-Tricks, MDN, moderncss.dev |
| Weekly | Typography & Type Systems | Typewolf, I Love Typography, Fonts In Use |
| Weekly | Design Systems | sidebar.io, designsystems.com, component.gallery |
| Weekly | UI/UX Patterns | NNGroup, UX Collective, a11yweekly.com |
| Weekly | Visual Tools | Figma Blog, Product Hunt, Vercel v0 |
| Monthly | Graphic Design | It's Nice That, Creative Boom, AIGA Eye on Design |
| Quarterly | Deep Design Thinking | Eye Magazine, Baseline, Design Observer |

### Learning Brief Format

Oracle produces weekly briefs with items tagged:
- 🔴 **Red (Act now)** — immediate skill update required
- 🟡 **Yellow (Absorb)** — track but no immediate action

### Example Evaluation Exercises

**Exercise 1 — Modern CSS:**
"Card grid needs to reflow at container sizes, not viewport. What CSS feature?"
- Score 5: Names container queries, explains why, notes Baseline status
- Score 1: Says "use media queries"

**Exercise 2 — Font Pairing:**
"Design a technical product. Recommend UI + code fonts."
- Score 5: Inter + JetBrains Mono, explains optical pairing
- Score 1: "Use whatever Google Fonts has"

**Exercise 3 — Token Critique:**
"Tokens named blue-500, blue-600, red-400. What's wrong?"
- Score 5: Identifies non-semantic naming, explains two-tier architecture
- Score 1: "The names are fine"

---

## 6. Production Feedback Loops

When Harish reviews Pixel's output, specific feedback gets filed in `agents/pixel/feedback/`:

**Example — Pulse Intelligence Site:**
- Typography: "Drop the serif (Newsreader). Replace with sans-serif (Inter, DM Sans, Geist)"
- Data design: "Show shift direction on fault line chips — escalating vs de-escalating"
- IA: "Progressive reveal — 3 levels of depth instead of one massive page"

Feedback is reviewed before next task in that domain and used to update skill modules.

---

## 7. Key Numbers (Memorized)

| Domain | Numbers |
|--------|---------|
| Typography | Body 15-25px / 10-12pt print \| Line height 1.4-1.6 \| Line length 45-90 chars |
| Color | AA 4.5:1 \| AA Large 3:1 \| AAA 7:1 \| 8-10 grey shades \| 5-10 per primary |
| Layout | 12-col web \| 4-col mobile \| 8px base unit \| 600px max email |
| Touch | Min 44x44pt (Apple) / 48x48dp (Material) \| Min 16px mobile |
| Data Viz | Max 5 pie segments \| Max 7 chart series \| Lie Factor 1.0 |

---

## 8. Tooling

| Tool | Purpose |
|------|---------|
| Typst | Documents, reports, PDFs |
| MJML | Email templates (Outlook-safe) |
| D2 | Architecture diagrams |
| CairoSVG | SVG → PNG |
| Mermaid | Flowcharts, sequence diagrams |
| Matplotlib | Data visualizations |
| Playwright | HTML rendering, screenshots |
| Nano Banana Pro | Logo, icon, image generation |

---

## How to Replicate

1. Create skill module directory with fundamentals/applied/specialization tiers
2. Write modules as internalized knowledge (rules + anti-patterns), not links
3. Build task-to-module mapping for relevant loading
4. Implement design review loop as mandatory quality gate
5. Set up continuous learning pipeline (weekly scans, urgency tags)
6. Create evaluation exercises with rubrics
7. File and review production feedback

**Key Insight:** The agent doesn't "look up" design rules. It has them internalized before starting any task.

---

*Documented by main agent — March 24, 2026*
