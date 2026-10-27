# Deep UI Concept Research: NeuralCFO & Moonshot Mode
**Curated Research from Pinterest, Dribbble, Behance & Leading B2B Fintech Platforms**  
*Document Version: 1.0 · Target Application: `apps/web` (Next.js + Tailwind + Tokens)*

---

## 1. Executive Research Summary & Design Thesis

### The Product Challenge
**NeuralCFO** is not a generic accounting dashboard or crypto tracker. It is an **AI-powered deterministic CFO decision-support platform** with strict architectural constraints:
1. **The Model Never Calculates:** Numbers are deterministic Python calculations, not LLM hallucinations.
2. **The Baseline is Immutable:** What-if scenarios are delta projections against a cryptographically frozen baseline.
3. **Rigorous Traceability:** Every number links to exact source rows, formulas, and verification rules (V1 Numbers, V4 Scenarios, V5 Units).
4. **Dual Persona:** Conservative **CFO Mode** (deep teal `#0B6B74`, cash floors, runway preservation) and bold **Moonshot Mode** (rich iris `#5B49C0`, speculative bets, growth simulations with built-in skeptic analysis).

### Anti-Slop Design Thesis
To avoid generic *"AI SaaS template syndrome"* (purple gradient bubbles, floating cards with identical drop shadows, low-contrast text), NeuralCFO's visual identity draws from **High-Craft Architectural Modernism**:
* **Bloomberg Terminal meets Linear App:** High information density, razor-sharp 1px structural dividers, tabular monospaced numbers (`JetBrains Mono`), muted status badges with high contrast (>4.5:1 WCAG AA compliance).
* **Earnest & Calm Voice:** No exaggerated graphs or gamified confetti. Clean, high-legibility layout that evokes trust, auditability, and institutional rigor.

---

## 2. Four Dominant UI Archetypes (Pinterest & Design Hubs)

### Archetype A: The "Architectural Ledger" (Linear x Ramp Command Center)
* **Visual Signature:** Deep slate/navy dark mode (`#0A1624` page, `#12233A` cards) paired with clean off-white light mode (`#F7F9FB` / `#FFFFFF`). Razor-thin hairline borders (`#7B8794` / `#223650`), subtle grid alignment, and mono tabular typography.
* **Component Rhythm:** Compact KPI blocks, micro sparklines, and status chips (`Verified` check-circle, `Warning` triangle) embedded directly inline with financial metrics.
* **Why it fits NeuralCFO:** Gives CFOs the feeling of a precision instrument. Instantly communicates that this is a professional, institutional-grade calculation engine.

### Archetype B: The "What-If Sensitivity Simulator" (Causal & Pigment Canvas)
* **Visual Signature:** Dedicated interactive **Parameter Dock** where financial levers (Hiring 2 Devs, Client Payment Delay +30d, Price Increase +10%) live as tactile input cards with stepped steppers, toggle chips, and immediate delta pills (e.g., `-$15,400/mo outflow`).
* **Visualizing Uncertainty (Fan Charts):** The projection chart displays not just a single speculative line, but an **Expected Case** path anchored by a translucent 12% opacity probability corridor representing the **Best Case** (-7d payment) and **Worst Case** (+14d payment).
* **Breach Threshold Accents:** Horizontal benchmark bands for the **12-Week Cash Floor** and **$50,000 Hard Reserve**, with a pulsing point marker for the exact minimum-cash moment.

### Archetype C: The "Verifiable Evidence Drawer" (Palantir Foundry & Retool Style)
* **Visual Signature:** An off-canvas slide-out sheet (`width: 480px–560px`) triggered whenever a user clicks on any KPI, chart point, or claim chip (`[Computed]`, `[Cited]`, `[Inferred]`).
* **Content Hierarchy:**
  1. **Lineage Header:** Run ID hash, timestamp, and verifier score (`100% Verified · V1, V4, V5 Passed`).
  2. **Mathematical Formula Block:** LaTeX or clean syntax tree display:  
     $$\text{Closing Cash}_t = \text{Closing Cash}_{t-1} + \text{Inflows}_t - \text{Outflows}_t$$
  3. **Underlying Invoices / Payroll Table:** Filterable mini-table showing the exact raw rows contributing to this week's outflows.
  4. **Active Assumptions List:** Explicit badges showing payment term days, VAT rates, and employee burdens.

### Archetype D: The "Dual-Mode Copilot & Skeptic Panel" (Perplexity x Brex AI)
* **Visual Signature:** A 760px conversational stream integrated with a split workspace. The AI responds with structured report cards rather than walls of text.
* **The "Skeptic Section" Card:** In Moonshot Mode, every bold strategy card is accompanied by an equally weighted **Skeptic Stress-Test Card** rendered with warning styling:
  * *Example:* "If Apex delays payment by 45 days instead of 30, cash breaches the 12-week floor on Nov 17."
* **Citation Micro-Pill Interaction:** Hovering over any claim displays a tooltip preview; clicking opens the Evidence Drawer focused on the source row.

---

## 3. Curated Moodboard & Benchmark Library

### A. Pinterest Search Queries & Moodboard Collections
To explore or build dedicated Pinterest moodboards for this project, use these exact query strings:

| Query String | Expected Design Visuals | Relevant NeuralCFO Feature |
| :--- | :--- | :--- |
| `fintech cash flow dashboard ui dark mode` | Deep slate command centers, neon teal accents, runway badges | Main CFO Dashboard Shell & Theme |
| `saas scenario modeling what if slider ui` | Driver-based input docks, toggle steppers, scenario tabs | Scenario Levers & Comparison Matrix |
| `financial data lineage audit trail ui` | Node DAGs, source-row tables, verification stamp badges | Evidence Drawer & Verifier Checks |
| `b2b fpa forecasting fan chart ui` | Confidence intervals, multi-series dashed line charts | Forecast Chart (3-Case Visualizer) |
| `executive financial kpi card minimal typography` | Large tabular numbers, mono labels, delta badges | Runway & Cash Floor KPI Cards |

### B. Real-World Production Benchmarks

| Platform | Best-in-Class Feature to Borrow | NeuralCFO Application |
| :--- | :--- | :--- |
| **Causal.app** | Plain-English variable formulas and interactive slider cards | What-If Lever Registry (`hire`, `payment_delay`) |
| **Pigment** | Multi-scenario side-by-side comparison matrix with delta column | `ScenarioComparison.tsx` multi-case table |
| **Runway.com** | Intuitive visual runway timeline with cash floor breach warnings | 26-Week Canonical Cash Forecast SVG |
| **Ramp Intelligence** | AI insight callouts backed by verified source invoice badges | Claim tags (`[Computed]`, `[Cited]`) and Skeptic Box |
| **Linear** | Razor-sharp border contrast, keyboard shortcut accessibility, toast chips | Overall UI component borders, status chips, drawers |
| **Palantir Foundry** | End-to-end data lineage tracing from analytical metric to raw row | `EvidenceDrawer.tsx` lineage tab & Zetaris adapter |

---

## 4. Component-by-Component UI Innovations for NeuralCFO

### 4.1. The Runway & Reserve KPI Bar (The Hero Metrics)
* **Card 1: Projected Runway (Weeks):**
  - Large `32px` JetBrains Mono tabular numeral (e.g., `18 WEEKS`).
  - Status Chip (`✓ Safe` or `⚠ Cash Floor Breach in W9`).
  - Deterministic rule caption: *"Weeks until cash < $0 (from schedule, never burn extrapolation)"*.
* **Card 2: Minimum Cash Reserve Point:**
  - `$42,150.00` in Highlight Text (`#8A5300` light / `#FFB84D` dark).
  - Monospace date tag `2027-02-01 (Week 14)`.
  - Segmented mini-bar showing clearance above the `$50,000` reserve threshold.
* **Card 3: Inflow vs. Outflow Variance:**
  - Net cash burn/generation per week with trend icon.

### 4.2. The 26-Week Canonical Cash Forecast Chart
* **Multi-Series Choreography:**
  1. **Baseline Series:** Solid line (`#566474` light / `#9AA9BB` dark) representing immutable baseline reality.
  2. **Scenario Line:** Thicker Iris line (`#5B49C0` / `#A99DF5`) for the active simulation.
  3. **Case Fan Band:** Shaded translucent area between Best Case (+5% rev, -7d payment) and Worst Case (-10% rev, +14d payment).
  4. **Threshold Guardrails:** Dotted Red Line (`$50,000` Hard Reserve) and Dotted Amber Line (12-Week Cash Floor `$207,692.00`).
* **Scrubbing & Interaction:**
  - Hovering reveals a vertical cursor with a floating inspection card displaying exact closing cash, committed payroll, expected receivables, and active levers for that week.
  - Clicking any week locks the selection and prompts: *"Inspect Week Lineage in Evidence Drawer"*.

### 4.3. Interactive Scenario Lever Dock ("What-If Studio")
* Interactive lever tray:
  - **Hire Lever:** Quantity stepper (`[ - ] 2 [ + ]`), role dropdown (`Senior Full-Stack`), start date picker. Shows immediate calculated monthly burden (`+$18,000/mo`).
  - **Payment Delay Lever:** Client selector (`Apex Systems (38% rev)`), slider (`0` to `60` days, default `30` days).
  - **Deposit % Lever:** Slider from `0%` to `50%`.
* **Action Footer:**
  - `[ Run Scenario ]` (Primary Button)
  - `[ Reset to Baseline ]` (Ghost Button)
  - Live diff counter: *"2 modifications against baseline #0100"*

### 4.4. Scenario Multi-Case Comparison Matrix
* **5-Column comparative table:** `Metric` | `Baseline` | `Expected Case` | `Worst Case (+14d)` | `Best Case (-7d)`.
* **Row groups:**
  - **Cash Health:** Min Cash Point, Min Cash Date, Ending Cash (Week 26), Runway Weeks.
  - **Policy Breaches:** 12-Week Floor Breached? (Yes/No badge), $50k Reserve Breached? (Yes/No badge).
  - **Sensitivity:** Cash Variance vs Baseline ($\Delta$).
* Every row features tabular alignment and subtle color-coded delta pills (`-$82,400 (-18.2%)`).

### 4.5. The Evidence & Lineage Drawer
* **3-Tab Architectural Layout:**
  1. **Formula & Calculation:** Shows the exact deterministic math steps, opening cash anchor, and zero-float decimal validation.
  2. **Source Row Ingestion:** Paginated data table of the originating CSV records with raw column names, row index, and content hash.
  3. **Verification Checklist:**
     - `[✓] V1: All numbers traceable to engine output`
     - `[✓] V4: Applied declared levers to baseline without mutation`
     - `[✓] V5: Strict decimal-safe currency (USD) and date boundaries`

### 4.6. CSV Ingestion & Ambiguity Disambiguation Modal
* **3-Step Visual Stepper:**
  1. **Upload & Integrity Check:** Drag-and-drop zone with instant SHA-256 hash generation and row count.
  2. **Column Mapping & Disambiguation:** Visual interface displaying detected columns with ambiguity callouts.
  3. **Import Quality Report:** Accepted rows count, flagged duplicates (never silently deleted), and rejected rows with reason pills.

---

## 5. Design System Alignment & Token Rules (docs/BRANDING.md)

All UI concepts strictly preserve the mathematical contrast tokens defined in `docs/BRANDING.md`:

```css
/* Core Surfaces & Tokens */
--bg-light: #F7F9FB;          --bg-dark: #0A1624;
--surface-light: #FFFFFF;     --surface-dark: #12233A;
--text-light: #0B1F33;        --text-dark: #E8EEF5;        /* >15:1 ratio */
--primary-cfo: #0B6B74;       --primary-cfo-dark: #35C0CB; /* >6.2:1 ratio */
--accent-moonshot: #5B49C0;   --accent-moonshot-dark: #A99DF5; /* >6.6:1 ratio */
--highlight-amber: #8A5300;   --highlight-amber-dark: #FFB84D; /* >6.3:1 ratio */

/* Status Chips (Always Icon + Label + Background) */
--status-verified: #136F4B on #E3F4EC (Light) | #3DCB92 on #12372B (Dark)
--status-warning:  #8A5300 on #FFF1D6 (Light) | #F2B33D on #3D2F0F (Dark)
--status-failed:   #B42318 on #FDE8E6 (Light) | #FF8A80 on #4A1D1D (Dark)
```
