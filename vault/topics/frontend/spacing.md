
# Spacing and the 8px baseline

## Short explanation (layman terms)

When you lay out a screen, you need gaps between things: between a title and a paragraph, between buttons, between sections. Instead of picking random numbers like 7, 13, or 19 pixels, teams often stick to **multiples of 8** (8, 16, 24, 32…). That keeps layouts predictable: the same few sizes repeat everywhere, so the interface feels orderly. It also plays nicely with how screens and browsers round pixels, and with typical text sizes, so text and whitespace tend to line up without fighting each other.

## Theory (precise)

**Baseline grid:** Spacing is quantized to a **base unit** (commonly **8 CSS pixels**) so margins, padding, and gaps share a common arithmetic progression. A **4px** scale is often used as a finer subset (still aligned to the same system: 4 is half of 8).

**Device pixel ratio (DPR):** Physical screens use ratios such as 1×, 1.5×, 2×, 3×, and 4×. Values divisible by 8 map to **integer device pixels** at many of these ratios, which reduces awkward **subpixel** placement and blur from rounding. Odd bases (for example 5px) can produce fractional CSS pixels at some ratios (e.g. 7.5px at 1.5×), which is harder to render crisply.

**Typography alignment:** The browser default **font-size** is typically **16px** (2×8), and a common **line-height** of **1.5** yields **24px** (3×8). Spacing on the same 8px grid aligns vertical rhythm with body copy and headings when those are also set on the grid.

**Design tokens:** Named steps (`space-1`, `space-2`, … or framework utilities) encode the scale once; designers and engineers share the same numbers, which lowers ambiguity in handoff and review.

**Assumptions and limits:** The rule is a **convention** tuned to common defaults (16px root, typical DPRs). It does not replace content-specific optical adjustment; custom type scales or dense data UIs may need exceptions.

## Where it applies (examples)

- **System-wide UI libraries and design systems:** You want a **small, memorable set** of spacing steps used across components. **Why this concept:** One scale becomes the contract between design and code (tokens or utility classes).
- **Responsive layouts across devices:** You care about **consistent snapping** at different DPRs. **Why this concept:** 8px multiples align with integer mapping at many common ratios, reducing subpixel oddities.
- **Text-heavy pages:** You want **vertical rhythm** between blocks and lines. **Why this concept:** Default 16/24 typography often sits on the same 8px grid, so block spacing can match line rhythm.

## Common gotchas (examples)

- **Gotcha:** Treating “only 8” as a hard law for every inset. **What goes wrong:** Tight controls (icons, chips, dense tables) can look **too coarse** at 8px-only steps. **What to do instead:** Allow a **4px** half-step **inside** components while keeping **section-level** spacing on 8px (or document explicit exceptions).
- **Gotcha:** Confusing **rem** with “8px on screen.” **What goes wrong:** If root font-size is not 16px, `1rem` is not 16px, so “multiples of 8” in **px** and **rem** diverge unless you normalize. **What to do instead:** Define tokens in **rem** (or clamp) from a clear root, and verify computed px at your target defaults.
- **Gotcha:** Copying framework defaults without checking. **What goes wrong:** e.g. Tailwind’s default spacing uses a **4px** base (`p-1` = 4px); other systems use **8px** as step 1. **What to do instead:** Name and document your **token step 1** so “space-2” always means the same thing in Figma and CSS.

## Related concepts

- **Design tokens** — Named, versioned values (color, space, type) shared across tools and code; spacing scales are often expressed as token steps.
- **Vertical rhythm** — Aligning line boxes and block margins so repeated text blocks look even; 8px spacing pairs naturally with 16/24 type defaults.
- **Subpixel rendering** — How browsers map CSS pixels to device pixels; integer-friendly spacing reduces fuzzy edges at fractional positions.
- **Responsive type and `clamp()`** — Fluid typography changes effective sizes; spacing may need rem/clamp to stay coherent with type.
- **8pt grid (design tools)** — Same idea in many design apps, sometimes in **points** rather than CSS px; align export/review with how CSS will round.

## References

- [Why "Multiples of 8" Are the Standard for Spacing in CSS](https://www.hikari-dev.com/en/blog/2026/04/12/8px-spacing-rule) — Screen density, typography, tokens, and 4px as a finer base.
- [Material Design: Layout – Understanding layout](https://m3.material.io/foundations/layout/understanding-layout/overview) — Google’s layout foundations (spacing and grids in a design-system context).
- [Tailwind CSS: Spacing](https://tailwindcss.com/docs/padding) — Default spacing scale built on a 4px base (`spacing` theme).
