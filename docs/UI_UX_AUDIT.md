# UI/UX Audit (Stage 1)

Written before any redesign code is touched, per the redesign brief's own
"audit first" requirement. This documents the actual current state of the
repository — not an assumed one.

## 1. What exists today

`app.py` is a single-file Streamlit script with:

- A sidebar (`render_sidebar`): wordmark, AI-backend status badge, dataset
  date range, a one-line trust statement.
- A KPI row (`render_kpi_row`): 4 `st.metric` cards (Revenue, Gross Profit,
  Margin, Orders) + a conditional margin-pressure warning banner.
- Three `st.tabs`: **Findings**, **Ask a Question**, **Dashboards**. No
  landing page, no routing, no concept of "modes" — the app boots directly
  into the KPI row + tabs.
- Dashboards tab: 7 Plotly charts + 2 dataframes, laid out in `st.columns(2)`
  pairs stacked vertically.
- Streamlit's default dark theme, customized only via
  `.streamlit/config.toml` (`primaryColor`, background/text colors) — no
  custom CSS injection anywhere, no custom fonts, no custom iconography
  (emoji are used for severity: 🔴🟠🟢).

There is exactly one dataset: the 12 CSVs in `/data`, loaded once via
`ordino.data_loader` and cached with `functools.lru_cache`. There is no
upload path, no session-scoped alternate dataset, no concept of "my
business" vs. "demo".

## 2. Architecture that must be preserved (do not touch)

This is the part of the system that is already correct and is the actual
competition differentiator — the redesign must wrap it, not replace it:

- **`nlg.py`'s grounding guardrail** (`_numbers_are_grounded`,
  `_entities_are_grounded`, `_generate`) — completely dataset-agnostic. It
  operates on any `(generated_text, evidence_dict)` pair. This is the single
  most reusable piece of the whole system for the "Analyze My Business"
  feature: it needs zero changes to narrate evidence computed from a
  user-uploaded CSV instead of the Ordino CSVs.
- **`insights.Finding`** — a generic dataclass (id/title/category/severity/
  summary/evidence/recommendation/confidence). The *shape* is reusable; the
  six `finding_*` functions in `insights.py` are not — every one of them
  calls a specific `analytics.py` function that assumes the Ordino
  schema (e.g. `delivery_partner_performance()` assumes columns
  `delivery_partner_id`, `delivery_status`, `delivery_rating`,
  `promised_days`, `actual_days` exist). None of this generalizes to an
  arbitrary CSV without a mapping layer in between.
- **`qa.py`'s router pattern** (keyword → intent → deterministic function →
  `nlg.narrate_answer`) — the *pattern* is reusable; the nine intents
  themselves are hardcoded to Ordino's dimensions/columns.
- **The three-backend narration chain** (Ollama → Groq → template, just
  added) — already dataset-agnostic, no changes needed for user data.
- **The full test suite (88 tests)** and the ground-truth validation
  approach — must keep passing throughout.

## 3. The hard architectural fact for "Analyze My Business"

`analytics.py` and `insights.py` are tightly coupled to the Ordino
schema (specific CSV filenames, specific joins like `sales.merge(products,
on="product_id")`, specific column names like `revenue`, `gross_profit`,
`delayed_rate_pct`). They **cannot** be pointed at an arbitrary uploaded CSV
as-is. Supporting user data requires a genuinely new, separate module (a
"generic dataset adapter": profiler → column-mapper → a smaller set of
schema-agnostic deterministic analytics functions that only run when the
required canonical columns are present). This is new code, not a
refactor of `analytics.py` — and it's the single largest piece of work in
the brief. `analytics.py`/`insights.py` stay untouched and keep serving the
demo dataset exactly as they do now.

## 4. Current UI problems

- **Generic Streamlit look.** Default theme, default widgets, emoji icons,
  no custom typography or spacing system — reads as "hackathon prototype,"
  which is the exact complaint driving this redesign.
- **No landing/marketing surface.** The app *is* the dashboard; there's no
  narrative on-ramp (problem → solution → trust → CTA) before a user hits
  live KPIs.
- **No information architecture for multiple datasets.** Nothing
  distinguishes "you are looking at the curated demo" from "you are looking
  at your own data" — a prerequisite for the upload feature.
- **Hardcoded backend labels** in the AI captions — already fixed in this
  session (now reads `backend`/`model` dynamically instead of hardcoding
  "Ollama").
- **Dashboard tab is a flat, unranked list of 7 charts** with no
  "executive insight" framing — every chart has equal visual weight,
  whereas the brief (correctly) wants the hero story (revenue vs. profit)
  to lead.

## 5. What's already fine (verified live, not assumed)

- **Mobile responsiveness at the framework level.** Tested at a 375×812
  viewport: the sidebar auto-collapses on load, the KPI row stacks to a
  single column, tabs and evidence expanders remain usable. No horizontal
  scroll, no broken layout. Streamlit's own responsive grid handles this
  without custom CSS. The redesign should preserve this rather than fight
  Streamlit's layout engine with fixed-width hacks.
- **Caching discipline.** `st.cache_data` around findings generation and
  per-finding narration already prevents redundant recomputation/LLM calls
  on unrelated reruns — documented in `app.py`'s own comments as a fix for
  a real audit finding. Any new caches (dataset profiling, user-data
  findings) should follow the same pattern.

## 6. Accessibility notes

- Severity is communicated with both color *and* an icon/text label
  (`CRITICAL`/`WARNING`/etc. badge next to the emoji) — already not
  color-only, which is correct.
- Custom theme colors in `.streamlit/config.toml`
  (`primaryColor #3d7dd6` on `backgroundColor #0e1117`) have not been
  contrast-checked against WCAG AA; worth a pass when the design system is
  formalized.
- No explicit ARIA/semantic heading structure beyond Streamlit's own
  defaults (`st.subheader`, `st.markdown` headers) — acceptable, since
  Streamlit renders these as real `<h1>`-`<h3>` tags.

## 7. Performance notes

- `_ollama_available()` has a 10s TTL cache to avoid a network timeout on
  every rerun (existing, working fix). The equivalent will be needed for
  any per-session dataset-profiling result once uploads exist, so profiling
  isn't re-run on every widget interaction.
- Groq calls are synchronous per finding (6 sequential calls on first load
  of the Findings tab) — acceptable at this scale (few seconds total),
  cached afterward by `st.cache_data`.

## 8. Constraint the redesign brief should account for

Streamlit is a server-rendered Python framework, not a bespoke HTML/CSS/JS
stack. A pixel-perfect recreation of a Pinterest SaaS reference is not
achievable inside Streamlit's layout model (DOM order-based `st.columns`/
`st.container`, no free-form CSS grid without injecting raw HTML via
`st.markdown(..., unsafe_allow_html=True)` or `st.components.v1.html`).
What *is* achievable at $0 and without new frameworks:

- A custom theme (typography via injected `<link>`/`@font-face` or a
  Google Fonts import, color system, spacing) via CSS injected once at
  app start.
- A custom-HTML landing "page" (shown before the KPI dashboard, gated by a
  session-state flag) built with `st.markdown(unsafe_allow_html=True)` or
  `st.components.v1.html`, mimicking the reference's structure (nav, hero,
  value cards, "how it works" flow, trust section, CTA, footer) using our
  own copy/branding — not the reference's literal assets, wording, or logo.
- Restrained chart styling via Plotly's theme system (already in use).

This is the realistic ceiling; the audit flags it now so the next stage's
plan doesn't promise a fidelity Streamlit can't deliver.

## 9. Proposed information architecture

```
Landing (marketing, no data loaded)
  └─ CTA: "Explore Demo"  → Demo mode (current app.py content)
  └─ CTA: "Analyze My Business"      → Upload workflow → My Business mode

App shell (once past landing)
  Top bar: workspace switcher — "NexaSphere Retail (Demo)" | "My Business"
  Sidebar: Overview · Findings · Ask · Dashboards · Data · AI & Trust
  (Data + capability-matrix panel only meaningful in "My Business" mode)
```

Demo mode = today's `app.py` behavior, untouched, always available,
never overwritten by an upload. My Business mode = new upload → profile →
map → analyze pipeline, session-scoped, isolated from the demo dataset.

## 10. Recommended staged execution (matches brief's own Section 36)

Given the scope, this audit recommends splitting the remaining work into
independently shippable, independently testable stages rather than one
change:

1. Design system + app shell (theme, CSS injection helper, landing/app mode
   toggle) — no new analytics.
2. Landing page content (static, no data dependency).
3. Dashboard visual pass on existing demo data (restyle only, same numbers).
4. Generic dataset adapter: CSV upload → profiler → column-mapping UI
   (no analytics yet, just inspection).
5. Schema-agnostic deterministic analytics subset + capability matrix
   ("your data supports X of 9 categories").
6. Wire uploaded-data evidence into the *existing* `nlg`/grounding
   pipeline (no changes to `nlg.py` needed — it's already generic).
7. Tests for the new adapter/mapping/analytics code.
8. Documentation pass (the docs list in the brief).

Each stage should land, get tested, and get reported before the next
starts — per the brief's own release-discipline section.
