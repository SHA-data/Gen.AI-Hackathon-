# NeuralCFO + Moonshot Mode: Brand, Color, Type and Accessibility Guide
Version 1.0 · Oct 24, 2026 · Owner of this file: Aroon (web shell). Everyone else consumes it and never hard-codes colors. Put this file at `/docs/BRANDING.md` and the CSS block in section 9 at `/apps/web/styles/tokens.css`.

## 1. Contrast rules (the minimums this guide enforces)
All ratios below were calculated with the WCAG 2.x formula, not estimated.

| Use | Minimum ratio | Standard |
| :--- | :--- | :--- |
| Body text and small text (under 18 px, or under 14 px bold) | 4.5 : 1 | WCAG AA |
| Large text (18 px and up, or 14 px bold and up) | 3 : 1 | WCAG AA |
| UI parts: input borders, icons, focus rings, chart lines | 3 : 1 | WCAG AA (1.4.11) |
| Purely decorative dividers | no minimum | never carry meaning |

**House rule:** we apply 4.5 : 1 to all text, including large text. Every color pair in this file is at or above that. Nothing in this palette is close to 2 : 1.

Two more rules:
- Never use color alone. Every status and tag shows a text label and an icon.
- A new color is not allowed until its ratio is checked against both surfaces (page and card) in both themes.

---

## 2. Brand basics

| Item | Value |
| :--- | :--- |
| Product | NeuralCFO |
| Modes | CFO Mode, Moonshot Mode |
| Chat agent keys | `neuralcfo`, `moonshot` |
| Tagline | Bold ideas with the numbers to check them. |
| Retired name | "Moonshot Mentor" (do not use anywhere) |

**Voice:** plain, calm, honest. We explain numbers, we do not hype them.
- **Say:** "Cash falls below your reserve in week 9. This assumes the client pays 30 days late."
- **Do not say:** "Great news! This strategy will definitely work."
- Always show the assumption behind a figure.
- A failed or unverified result is never styled as a success, and never softened into "maybe fine".
- Never write as a real person, and never put a paraphrase in quotation marks.

**Wordmark** (text only, no logo file needed for the hackathon):  
`Neural` in body-text color, `CFO` in primary. In Moonshot pages append ` · Moonshot` in the Moonshot color. Keep clear space equal to the height of the letter "N" on all sides. Minimum size: 16 px tall.

**Mandatory disclaimer** (exact text, on every report and export):
> Decision support, not financial advice. Forecasts depend on the assumptions shown and are not guaranteed predictions.

**Disclaimer style:** muted text color, 13 px, never hidden, never collapsed.

---

## 3. Color palette
Light theme: page `#F7F9FB`, card surface `#FFFFFF`. Dark theme: page `#0A1624`, card surface `#12233A`.

### 3.1 Core colors
| Role | Light | Ratio on card / page | Dark | Ratio on card / page |
| :--- | :--- | :--- | :--- | :--- |
| Text | `#0B1F33` | 16.69 / 15.82 | `#E8EEF5` | 13.55 / 15.59 |
| Muted text | `#475569` | 7.58 / 7.18 | `#A9B8CB` | 7.84 / 9.02 |
| Primary (NeuralCFO) | `#0B6B74` | 6.23 / 5.91 | `#35C0CB` | 7.20 / 8.28 |
| Moonshot accent | `#5B49C0` | 6.65 / 6.30 | `#A99DF5` | 6.65 / 7.66 |
| Highlight text (minimum-cash callout) | `#8A5300` | 6.33 / 6.00 | `#FFB84D` | 9.20 / 10.59 |
| UI border (inputs, controls) | `#7B8794` | 3.66 / 3.47 | `#5B7391` | 3.24 / 3.73 |

*Notes:*
- The first version of this theme used `#F5A524` for the highlight. It measured 2.04 : 1 on white, so it is replaced. Amber now only appears as a fill or as the darker text color above.
- "UI border" is for borders that identify a control (input, button outline). The soft divider colors in 3.4 are decorative only.

### 3.2 Result statuses
Text color on the status chip background. Chip text is always paired with its label and icon.

| Status | Label | Icon | Light text on chip | Ratio | Dark text on chip | Ratio |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| verified | Verified | check circle | `#136F4B` on `#E3F4EC` | 5.41 | `#3DCB92` on `#12372B` | 6.32 |
| warning | Warning | triangle | `#8A5300` on `#FFF1D6` | 5.67 | `#F2B33D` on `#3D2F0F` | 7.00 |
| unverified | Unverified | dashed circle | `#566474` on `#EAEEF2` | 5.19 | `#9AA9BB` on `#22324A` | 5.40 |
| failed | Failed | x circle | `#B42318` on `#FDE8E6` | 5.59 | `#FF8A80` on `#4A1D1D` | 6.20 |

On plain card surfaces (no chip) these text colors measure 6.05 to 6.57 : 1 in light and 6.61 to 8.51 : 1 in dark.

### 3.3 Claim tags
| Tag | Label | Light text on chip | Ratio | Dark text on chip | Ratio |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| cited | Cited | `#1D4ED8` on `#E4ECFD` | 5.65 | `#7FA9FF` on `#16294D` | 6.19 |
| computed | Computed | `#0E6E85` on `#DDF1F6` | 5.01 | `#4CC9E0` on `#0F3340` | 6.85 |
| inferred | Inferred | `#6D3FD1` on `#EEE8FB` | 5.35 | `#B79CFF` on `#2B2250` | 6.37 |
| commentary | Commentary | `#566474` on `#EAEEF2` | 5.19 | `#9AA9BB` on `#22324A` | 5.40 |

Tags also differ by icon (quote mark, calculator, spark, speech bubble), so they stay distinguishable without color.

### 3.4 Buttons and decorative colors
| Element | Colors | Ratio |
| :--- | :--- | :--- |
| Primary button, light | white text on `#0B6B74` | 6.23 |
| Moonshot button, light | white text on `#5B49C0` | 6.65 |
| Primary button, dark | `#0A1624` text on `#35C0CB` | 8.28 |
| Moonshot button, dark | `#0A1624` text on `#A99DF5` | 7.66 |
| Soft divider (decorative only) | `#E2E8F0` light, `#223650` dark | not text |
| Focus ring | 2 px outline in primary, 2 px offset | at least 5.9 on page |

### 3.5 Chart lines
Line colors must reach 3 : 1 against the card surface. Lines also differ by dash pattern and direct labels, so color is never the only cue.

| Series | Light | Ratio | Dark | Ratio | Line style |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Baseline | `#566474` | 6.05 | `#9AA9BB` | 6.61 | solid |
| Hire | `#B26A00` | 4.24 | `#FFB84D` | 9.20 | dashed |
| Delay | `#C0392B` | 5.44 | `#FF8A80` | 6.93 | dotted |
| Combined | `#5B49C0` | 6.65 | `#A99DF5` | 6.65 | solid, thicker |

- Draw best and worst cases as a faint band (12% opacity of the series color) around the expected line.
- Mark the minimum-cash point with a filled circle and a text label ("Min cash, 1 Feb 2027"), using the highlight color.
- Chart axis labels and legends use the muted text color (7.58 : 1 or better).

---

## 4. Typography

| Role | Font | Fallback stack |
| :--- | :--- | :--- |
| UI and body | Inter | `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` |
| Headings | Inter (weight 600) | same |
| Numbers, IDs, code | JetBrains Mono | `ui-monospace, "SF Mono", Menlo, Consolas, monospace` |

Load fonts from Google Fonts with `display=swap`. The app must stay readable if they fail to load, so always keep the fallback stack.

**Rules for numbers (important for a finance product):**
- Money uses `font-variant-numeric: tabular-nums` so columns align.
- Always show the currency code or symbol and the sign. Negative values are written with a minus sign and the failed or warning label when they breach a limit. Never rely on red alone.
- Run IDs, row IDs and hashes use the monospace font.
- Dates use ISO format in tables (`2027-02-01`) and a readable form in sentences ("1 Feb 2027").

**Type scale** (base 16 px, minimum body size 16 px, minimum caption size 13 px):
| Style | Size / line height | Weight |
| :--- | :--- | :--- |
| Display (page title) | 32 / 40 | 700 |
| H1 | 28 / 36 | 600 |
| H2 | 22 / 30 | 600 |
| H3 | 18 / 26 | 600 |
| Body | 16 / 24 | 400 |
| Small | 14 / 20 | 400 |
| Caption and disclaimer | 13 / 18 | 400 |
| Key figure (KPI) | 32 / 36, mono, tabular | 600 |

Text rules: line length 60 to 80 characters, left aligned, never justified. Users must be able to zoom text to 200% without losing content.

---

## 5. Spacing, shape and layout

| Token | Value |
| :--- | :--- |
| Spacing scale | 4, 8, 12, 16, 24, 32, 48 px |
| Card radius | 12 px |
| Control radius (buttons, inputs) | 8 px |
| Chip radius | 999 px |
| Minimum tap target | 44 x 44 px |
| Card border | 1 px solid decorative divider, plus shadow 0 1px 2px rgba(11,31,51,0.08) in light only |
| Max content width | 1200 px; chat column 760 px |

---

## 6. Component rules

| Component | Rules |
| :--- | :--- |
| Status chip | Icon + label + status colors from 3.2. Appears next to every tool result and every report. |
| Claim tag chip | Icon + label from 3.3 on every report claim; click opens the evidence drawer. |
| Evidence drawer | Card surface, 1 px UI border, slides from the right, focus moves into it on open, Escape closes it. |
| Gated (failed) strategy | Listed in its own "Flagged" section, with the failed label, the gate name (G1 to G4) and the reason in text. Never muted, never hidden. |
| Approval card | Shows the proposed change, its risk level (low, medium, high) in text, and clear Approve and Reject buttons of equal size. |
| Assumption | Always shown as a visible label "Assumption" next to the value, using the Inferred tag style. |
| Errors | Message in plain words, a failed chip, and what the user can do next. No raw error codes alone. |
| Skeptic section | Same visual weight as the recommendation section. Never collapsed by default. |

---

## 7. Accessibility checklist (run before the demo)
- Every text and chip color pair matches a row in this file, or has been measured at 4.5 : 1 or higher.
- Every control, icon-only button and chart has a text label or accessible name.
- Keyboard only: you can upload, chat, open the evidence drawer, approve an action and export a report.
- Focus is always visible (2 px primary outline).
- Streaming chat text lives in an `aria-live="polite"` region.
- Status changes (verified, warning, failed) are announced by text, not only shown by color.
- Test both themes, at 200% zoom, and at 380 px width.
- Respect `prefers-reduced-motion`: no animations of numbers or charts when it is set.

---

## 8. Re-checking a color
Use this script when someone proposes a new color. It prints the WCAG ratio:

```python
def lum(h):
    h = h.lstrip('#')
    r, g, b = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

print(round(ratio('#0B6B74', '#FFFFFF'), 2))   # 6.23
```

---

## 9. Design tokens (`/apps/web/styles/tokens.css`)
See [`/apps/web/styles/tokens.css`](file:///c:/Users/n%20tech/Desktop/Neural%20CFO/apps/web/styles/tokens.css) for the canonical CSS definitions.

---

## 10. Rules for the three modules
- **Sharjeel (NeuralCFO):** use `--chart-*` for forecast lines and `--status-*` for run results. Show the minimum-cash point with `--highlight-fill` plus a text label.
- **Aleena (Moonshot):** use `--moonshot` as the page accent, `--tag-*` on every report claim, and the Flagged section style from section 6.
- **Aroon (Chat shell):** owns `tokens.css`, the status and tag chip components, the evidence drawer and the theme toggle. Other modules import these components and do not rebuild them.
- **Nobody writes a hex value inside a component. Use the variables. If a token is missing, open a "contract-change" issue so the palette stays checked.**
