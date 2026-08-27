"""NexaSphere design system, landing page and dashboard chrome.

Implementation note: Streamlit's DOM-order layout constraint applies to its
*interactive widgets*. Content rendered through `st.markdown(...,
unsafe_allow_html=True)` lands in the main document, not a sandboxed iframe,
so bespoke CSS Grid layouts, layering, gradients, glass effects and inline SVG
are all available. Only genuinely interactive controls must be Streamlit
widgets, and those are restyled here via stable `data-testid` / `st-key-*`
hooks.

Theming is driven entirely by CSS custom properties, so light and dark modes
share one stylesheet and switch by swapping the values on `:root`. Streamlit's
own config.toml theme cannot change at runtime, so the injected CSS overrides
it for both modes -- that is what makes a working in-app toggle possible.

All illustration is inline SVG generated in this file: no binary assets, no
stock photography, no icon package, nothing downloaded. That keeps the deploy
$0 and avoids reproducing any copyrighted artwork from the visual references,
whose *design language* is what we recreate, not their assets.

Presentation only: nothing here imports or alters analytics, insights, nlg or
user_data.
"""
from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Palettes
# ---------------------------------------------------------------------------

PALETTES = {
    "light": {
        "canvas": "#F5F4FC", "surface": "#FFFFFF", "raised": "#FFFFFF",
        "border": "#E7E5F5", "ink": "#14142B", "muted": "#6E6D8A",
        "accent": "#5B4FE9", "accent2": "#7C6FF0", "accent_soft": "#EDEBFD",
        "navbar": "#14142B", "navbar_ink": "#FFFFFF",
        "grid": "#F0EEFA", "shadow": "rgba(20,20,43,.08)",
        "glow1": "#E4E0FB", "glow2": "#EAF4FF",
        "ok": "#2FA36B", "ok_bg": "#E8F6EE",
        "warn": "#E8A33D", "warn_bg": "#FDF3E3",
        "bad": "#E5484D", "bad_bg": "#FDECEC",
    },
    "dark": {
        "canvas": "#0E0D18", "surface": "#17162A", "raised": "#1E1C35",
        "border": "#2C2949", "ink": "#F2F1F9", "muted": "#9B99BC",
        "accent": "#8B7CF6", "accent2": "#A99EF3", "accent_soft": "#241F45",
        "navbar": "#0A0914", "navbar_ink": "#FFFFFF",
        "grid": "#232042", "shadow": "rgba(0,0,0,.45)",
        "glow1": "#241F45", "glow2": "#152036",
        "ok": "#4ED397", "ok_bg": "#12301F",
        "warn": "#F0B457", "warn_bg": "#33260F",
        "bad": "#FF6B6F", "bad_bg": "#3A1517",
    },
}


def current_mode() -> str:
    return st.session_state.get("nx_theme", "light")


def palette() -> dict:
    return PALETTES[current_mode()]


def severity_colors(severity: str) -> tuple[str, str]:
    p = palette()
    mapping = {
        "critical": (p["bad"], p["bad_bg"]),
        "warning": (p["warn"], p["warn_bg"]),
        "watch": (p["accent"], p["accent_soft"]),
        "info": (p["ok"], p["ok_bg"]),
    }
    return mapping.get(severity, (p["accent"], p["accent_soft"]))


def _html(markup: str) -> None:
    """Renders raw HTML, removing Python source indentation first.

    Streamlit runs this through a Markdown renderer, which treats any line
    indented by 4+ spaces as a code block -- so HTML written at normal function
    indentation would render as visible source. textwrap.dedent is not enough
    because these templates interpolate multi-line SVG already at column 0,
    which drops the common prefix to zero. Stripping every line is safe here:
    whitespace between HTML tags is insignificant and none of this markup
    contains <pre>-formatted content.
    """
    st.markdown("\n".join(l.strip() for l in markup.splitlines()).strip(),
                unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Stylesheet
# ---------------------------------------------------------------------------

_CSS_TEMPLATE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
  --nx-canvas:__canvas__; --nx-surface:__surface__; --nx-raised:__raised__;
  --nx-border:__border__; --nx-ink:__ink__; --nx-muted:__muted__;
  --nx-accent:__accent__; --nx-accent2:__accent2__; --nx-accent-soft:__accent_soft__;
  --nx-navbar:__navbar__; --nx-navbar-ink:__navbar_ink__;
  --nx-grid:__grid__; --nx-shadow:__shadow__;
  --nx-ok:__ok__; --nx-ok-bg:__ok_bg__;
  --nx-warn:__warn__; --nx-warn-bg:__warn_bg__;
  --nx-bad:__bad__; --nx-bad-bg:__bad_bg__;
}

html, body, [class*="css"], .stMarkdown, button, input, textarea, select {
  font-family:'Plus Jakarta Sans',-apple-system,BlinkMacSystemFont,sans-serif !important;
}

/* Streamlit's header is a 60px OPAQUE bar at z-index 999990. Left as-is it
   paints over the first 60px of the page -- which was covering our navbar and
   pill tabs. Make it transparent and click-through, restore pointer events on
   its actual controls, and pad the content below it.
   The running/connecting status indicator is deliberately KEPT: it is real
   feedback about whether the app is busy or has lost its connection, and
   hiding it makes the app feel frozen during a slow AI call. Only the Deploy
   button (irrelevant to end users) is removed. */
[data-testid="stHeader"] {
  background:transparent !important; pointer-events:none; height:0 !important;
}
[data-testid="stHeader"] > * { pointer-events:auto; }
[data-testid="stAppDeployButton"] { display:none !important; }
[data-testid="stStatusWidget"] { pointer-events:auto; }
[data-testid="stDecoration"], footer { display:none !important; }
.block-container { padding-top:3.4rem !important; }

.stApp {
  background:
    radial-gradient(1100px 520px at 78% -8%, __glow1__ 0%, transparent 62%),
    radial-gradient(760px 420px at 8% 4%, __glow2__ 0%, transparent 58%),
    var(--nx-canvas);
}
.block-container { padding-bottom:3rem !important; max-width:1200px; }
h1,h2,h3,h4,h5 { color:var(--nx-ink) !important; letter-spacing:-.025em; }
p, span, li, label, .stMarkdown { color:var(--nx-ink); }
hr { border-color:var(--nx-border); }

/* ---------- Streamlit widgets ---------- */
.stButton > button {
  border-radius:12px; font-weight:600; padding:.6rem 1.1rem;
  border:1px solid var(--nx-border); background:var(--nx-surface); color:var(--nx-ink);
  box-shadow:0 1px 2px var(--nx-shadow); transition:all .16s ease;
}
.stButton > button:hover { border-color:var(--nx-accent); transform:translateY(-1px);
  box-shadow:0 6px 18px color-mix(in srgb, var(--nx-accent) 24%, transparent); }
.stButton > button[kind="primary"] {
  background:linear-gradient(180deg,var(--nx-accent2),var(--nx-accent));
  color:#fff; border:none; box-shadow:0 6px 18px color-mix(in srgb, var(--nx-accent) 38%, transparent);
}
div[data-testid="stVerticalBlockBorderWrapper"] {
  background:var(--nx-surface); border:1px solid var(--nx-border) !important;
  border-radius:18px !important; box-shadow:0 1px 2px var(--nx-shadow);
}
[data-testid="stMetric"] { background:var(--nx-surface); border:1px solid var(--nx-border);
  border-radius:16px; padding:1.1rem 1.2rem; }
[data-testid="stMetricLabel"] { color:var(--nx-muted) !important; font-weight:600 !important; }
[data-testid="stMetricValue"] { color:var(--nx-ink) !important; font-weight:800 !important; }
section[data-testid="stSidebar"] { background:var(--nx-surface); border-right:1px solid var(--nx-border); }
[data-testid="stFileUploaderDropzone"] { background:var(--nx-surface);
  border:1.5px dashed var(--nx-accent); border-radius:16px; padding:1.5rem; }
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stTextArea textarea {
  border-radius:12px !important; border-color:var(--nx-border) !important;
  background:var(--nx-surface) !important; color:var(--nx-ink) !important;
}
.stTextInput input:focus { border-color:var(--nx-accent) !important;
  box-shadow:0 0 0 3px color-mix(in srgb, var(--nx-accent) 18%, transparent) !important; }
[data-testid="stExpander"] { background:var(--nx-surface); border:1px solid var(--nx-border);
  border-radius:14px; }
[data-testid="stExpander"] summary { color:var(--nx-ink) !important; font-weight:600; }
[data-testid="stDataFrame"] { border:1px solid var(--nx-border); border-radius:14px; }
code { background:var(--nx-accent-soft) !important; color:var(--nx-accent) !important; }

/* ---------- Pill navigation ----------
   Streamlit renders st.radio options as <label data-testid="stRadioOption">
   carrying data-selected, and scopes the widget with an st-key-<key> class.
   Those are the stable hooks; the emotion-cache class names are build hashes
   and must not be relied on. The radio dot lives three divs deep inside the
   label and is hidden so each option reads purely as a pill. */
.st-key-nx_active_page {
  display:flex; background:var(--nx-navbar); padding:.4rem; border-radius:999px;
  box-shadow:0 8px 26px var(--nx-shadow);
}
.st-key-nx_active_page [data-baseweb="radio"],
.st-key-nx_active_page > div, .st-key-nx_active_page > div > div {
  display:flex; flex-wrap:wrap; gap:.3rem; width:100%; align-items:center;
}
.st-key-nx_active_page [data-testid="stRadioOption"] {
  flex:1 1 auto; margin:0 !important; padding:.6rem 1.05rem; border-radius:999px;
  cursor:pointer; transition:all .18s ease; background:transparent;
  display:flex; align-items:center; justify-content:center;
}
/* the radio dot */
.st-key-nx_active_page [data-testid="stRadioOption"] > div > div > div:first-child {
  display:none !important;
}
.st-key-nx_active_page [data-testid="stRadioOption"] p {
  color:rgba(255,255,255,.72) !important; font-weight:600 !important;
  font-size:.88rem !important; margin:0 !important; white-space:nowrap;
}
.st-key-nx_active_page [data-testid="stRadioOption"]:hover p { color:#fff !important; }
.st-key-nx_active_page [data-testid="stRadioOption"][data-selected="true"] {
  background:linear-gradient(180deg,var(--nx-accent2),var(--nx-accent));
  box-shadow:0 4px 14px color-mix(in srgb, var(--nx-accent) 45%, transparent);
}
.st-key-nx_active_page [data-testid="stRadioOption"][data-selected="true"] p { color:#fff !important; }
@media (max-width:820px){
  .st-key-nx_active_page { border-radius:20px; }
  .st-key-nx_active_page [data-testid="stRadioOption"] { flex:1 1 44%; }
}

/* Icon-only circular controls (home, theme toggle) -- these are utilities, not
   primary actions, so they read as small round icon buttons rather than
   full-width labelled buttons competing with the navigation. */
.st-key-nx_home button, .st-key-nx_theme button {
  width:40px !important; height:40px !important; min-height:40px !important;
  border-radius:50% !important; padding:0 !important; font-size:1.05rem !important;
  display:flex !important; align-items:center; justify-content:center;
  line-height:1 !important;
}
.st-key-nx_home button p, .st-key-nx_theme button p { font-size:1.05rem !important; margin:0 !important; }
.st-key-nx_theme button:hover { transform:rotate(-18deg) scale(1.06); }

/* ---------- Motion ----------
   Entrance transitions only, kept short and non-looping: they orient the eye
   as content arrives without turning the dashboard into a distraction. All of
   it is disabled for users who ask for reduced motion. */
@keyframes nxUp { from{opacity:0;transform:translateY(12px);} to{opacity:1;transform:none;} }
@keyframes nxIn { from{opacity:0;} to{opacity:1;} }
@keyframes nxDraw { from{stroke-dashoffset:var(--len);} to{stroke-dashoffset:0;} }
.nx-kpi, .nx-card, .nx-stat, .nx-fstep { animation:nxUp .5s cubic-bezier(.22,.9,.3,1) both; }
.nx-statrow > :nth-child(2), .nx-grid > :nth-child(2), .nx-flow > :nth-child(2) { animation-delay:.06s; }
.nx-statrow > :nth-child(3), .nx-grid > :nth-child(3), .nx-flow > :nth-child(3) { animation-delay:.12s; }
.nx-statrow > :nth-child(4), .nx-grid > :nth-child(4), .nx-flow > :nth-child(4) { animation-delay:.18s; }
.nx-grid > :nth-child(5), .nx-flow > :nth-child(5) { animation-delay:.24s; }
.nx-grid > :nth-child(6), .nx-flow > :nth-child(6) { animation-delay:.30s; }
[data-testid="stPlotlyChart"], [data-testid="stVerticalBlockBorderWrapper"] { animation:nxIn .55s ease both; }
.nx-spark polyline { stroke-dasharray:var(--len,600); animation:nxDraw 1.1s ease-out both; }
.nx-hero svg g { animation:nxUp .7s cubic-bezier(.22,.9,.3,1) both; }
.nx-hero svg g:nth-of-type(2){animation-delay:.08s;} .nx-hero svg g:nth-of-type(3){animation-delay:.16s;}
.nx-hero svg g:nth-of-type(4){animation-delay:.24s;} .nx-hero svg g:nth-of-type(5){animation-delay:.32s;}
.nx-hero svg g:nth-of-type(6){animation-delay:.40s;}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation:none !important; transition:none !important; }
}

/* ---------- Landing ---------- */
.nx-nav { display:flex; align-items:center; justify-content:space-between; gap:1rem;
  background:color-mix(in srgb, var(--nx-surface) 74%, transparent); backdrop-filter:blur(14px);
  border:1px solid var(--nx-border); border-radius:18px; padding:.8rem 1.3rem;
  margin-bottom:2rem; box-shadow:0 2px 14px var(--nx-shadow); }
.nx-brand { display:flex; align-items:center; gap:.6rem; font-weight:800; font-size:1.05rem;
  color:var(--nx-ink); text-decoration:none; }
.nx-logo { width:30px; height:30px; border-radius:9px; flex:none;
  background:linear-gradient(135deg,var(--nx-accent2),var(--nx-accent)); color:#fff;
  display:grid; place-items:center; font-size:.84rem; font-weight:800;
  box-shadow:0 4px 12px color-mix(in srgb, var(--nx-accent) 40%, transparent); }
.nx-navlinks { display:flex; gap:.4rem; }
.nx-navlinks a { font-size:.86rem; color:var(--nx-muted); font-weight:600; text-decoration:none;
  padding:.45rem .85rem; border-radius:10px; border:1px solid transparent; transition:all .16s ease; }
.nx-navlinks a:hover { color:var(--nx-accent); background:var(--nx-accent-soft);
  border-color:var(--nx-border); }
.nx-navcta { background:var(--nx-navbar); color:var(--nx-navbar-ink); border-radius:999px;
  padding:.5rem 1rem; font-size:.8rem; font-weight:600; white-space:nowrap; }
@media (max-width:820px){ .nx-navlinks{display:none;} }

.nx-hero { display:grid; grid-template-columns:1.08fr .92fr; gap:2rem; align-items:center; }
@media (max-width:900px){ .nx-hero{grid-template-columns:1fr;} }
.nx-eyebrow { display:inline-flex; align-items:center; gap:.45rem; background:var(--nx-accent-soft);
  color:var(--nx-accent); border-radius:999px; padding:.34rem .85rem; font-size:.76rem;
  font-weight:700; margin-bottom:1rem; }
.nx-eyebrow .nx-dot { width:6px;height:6px;border-radius:50%;background:var(--nx-accent); }
.nx-hero h1 { font-size:3.1rem; line-height:1.06; font-weight:800; margin:0 0 1rem; }
@media (max-width:900px){ .nx-hero h1{font-size:2.25rem;} }
.nx-lede { font-size:1.03rem; line-height:1.62; color:var(--nx-muted) !important; max-width:30rem; margin:0; }

.nx-statrow { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:1rem; margin:2.2rem 0 .4rem; }
.nx-stat { background:var(--nx-surface); border:1px solid var(--nx-border); border-radius:16px; padding:1.05rem 1.15rem; }
.nx-k { font-size:.73rem; color:var(--nx-muted) !important; font-weight:600; text-transform:uppercase; letter-spacing:.05em; }
.nx-v { font-size:1.55rem; font-weight:800; color:var(--nx-ink); letter-spacing:-.03em; margin-top:.3rem; }
.nx-d { font-size:.78rem; font-weight:700; margin-top:.2rem; }
.nx-up{color:var(--nx-ok) !important;} .nx-down{color:var(--nx-bad) !important;}

.nx-sectionhead { margin:3.2rem 0 1.1rem; scroll-margin-top:1rem; }
.nx-tag { font-size:.75rem; font-weight:700; color:var(--nx-accent) !important; text-transform:uppercase; letter-spacing:.08em; }
.nx-sectionhead h2 { font-size:1.9rem; font-weight:800; margin:.35rem 0 .4rem; }
.nx-sectionhead p { color:var(--nx-muted) !important; font-size:.96rem; max-width:40rem; margin:0; line-height:1.6; }

.nx-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:1.05rem; }
.nx-card { background:var(--nx-surface); border:1px solid var(--nx-border); border-radius:18px;
  padding:1.45rem; box-shadow:0 1px 2px var(--nx-shadow); transition:all .18s ease; }
.nx-card:hover { transform:translateY(-3px); box-shadow:0 14px 32px var(--nx-shadow); border-color:var(--nx-accent); }
.nx-ico { width:42px;height:42px;border-radius:12px;display:grid;place-items:center;
  margin-bottom:.9rem;background:var(--nx-accent-soft); }
.nx-art { background:var(--nx-accent-soft); border-radius:14px; padding:.5rem;
  margin-bottom:.95rem; overflow:hidden; }
.nx-art svg { display:block; }
.nx-card h4 { font-size:1rem; font-weight:700; margin:0 0 .35rem; }
.nx-card p { font-size:.88rem; color:var(--nx-muted) !important; line-height:1.56; margin:0; }

.nx-flow { display:flex; gap:.5rem; flex-wrap:wrap; }
.nx-fstep { flex:1 1 148px; background:var(--nx-surface); border:1px solid var(--nx-border);
  border-radius:14px; padding:.95rem .85rem; text-align:center; }
.nx-n { width:24px;height:24px;border-radius:7px;background:var(--nx-accent-soft);
  color:var(--nx-accent) !important;font-size:.72rem;font-weight:800;display:grid;place-items:center;margin:0 auto .5rem; }
.nx-l { font-size:.82rem; font-weight:700; color:var(--nx-ink); }
.nx-s { font-size:.74rem; color:var(--nx-muted) !important; margin-top:.18rem; line-height:1.4; }

.nx-dark { background:#161428; border-radius:22px; padding:2.1rem; box-shadow:0 20px 48px var(--nx-shadow); }
.nx-dark h2 { color:#fff !important; font-size:1.8rem; font-weight:800; margin:0 0 .55rem; }
.nx-dark p { color:#A9A5C4 !important; font-size:.94rem; line-height:1.6; margin:0; }
.nx-pipe { display:flex; align-items:center; gap:.45rem; flex-wrap:wrap; margin-top:1.4rem; }
.nx-node { background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.14);
  border-radius:11px; padding:.55rem .85rem; font-size:.8rem; font-weight:600; color:#fff !important; }
.nx-node.nx-hl { background:linear-gradient(135deg,#7C6FF0,#5B4FE9); border-color:transparent; }
.nx-ar { color:#5A5680 !important; font-weight:700; }

.nx-trust { display:flex; gap:.7rem; align-items:flex-start; padding:.72rem 0; border-bottom:1px solid var(--nx-border); }
.nx-trust:last-child{border-bottom:none;}
.nx-ck { flex:none;width:20px;height:20px;border-radius:50%;background:var(--nx-ok-bg);
  color:var(--nx-ok) !important;display:grid;place-items:center;font-size:.7rem;font-weight:800;margin-top:.1rem; }
.nx-trust b{font-size:.89rem;color:var(--nx-ink);} .nx-trust span{font-size:.86rem;color:var(--nx-muted) !important;}

.nx-finalcta { background:linear-gradient(135deg,var(--nx-accent2),var(--nx-accent)); border-radius:22px;
  padding:2.8rem 2rem; text-align:center; box-shadow:0 20px 46px color-mix(in srgb, var(--nx-accent) 34%, transparent); }
.nx-finalcta h2 { color:#fff !important; font-size:1.95rem; font-weight:800; margin:0 0 .5rem; }
.nx-finalcta p { color:rgba(255,255,255,.88) !important; font-size:.98rem; margin:0; }
.nx-foot { text-align:center; color:var(--nx-muted) !important; font-size:.82rem; padding:2.2rem 0 .6rem; line-height:1.7; }

/* ---------- Dashboard ---------- */
.nx-apphead { display:flex; align-items:center; justify-content:space-between; gap:1rem;
  background:var(--nx-surface); border:1px solid var(--nx-border); border-radius:18px;
  padding:.75rem 1.15rem; box-shadow:0 2px 14px var(--nx-shadow); }
.nx-ws { display:flex; align-items:center; gap:.5rem; background:var(--nx-accent-soft);
  border-radius:999px; padding:.35rem .85rem; font-size:.78rem; font-weight:700; color:var(--nx-accent) !important; }

.nx-kpi { background:var(--nx-surface); border:1px solid var(--nx-border); border-radius:18px;
  padding:1.15rem 1.2rem; box-shadow:0 1px 2px var(--nx-shadow); height:100%;
  display:flex; flex-direction:column; justify-content:space-between; transition:all .18s ease; }
.nx-kpi:hover { border-color:var(--nx-accent); box-shadow:0 10px 26px var(--nx-shadow); }
.nx-kl { font-size:.77rem; color:var(--nx-muted) !important; font-weight:600;
  display:flex; align-items:center; justify-content:space-between; gap:.4rem; }
.nx-kv { font-size:1.8rem; font-weight:800; letter-spacing:-.03em; margin:.4rem 0 .3rem; color:var(--nx-ink); }
.nx-kd { font-size:.77rem; font-weight:700; display:inline-flex; align-items:center; gap:.25rem;
  padding:.15rem .5rem; border-radius:999px; }
.nx-kd.nx-up{background:var(--nx-ok-bg);} .nx-kd.nx-down{background:var(--nx-bad-bg);}
.nx-kn { font-size:.73rem; color:var(--nx-muted) !important; margin-top:.45rem; }
.nx-spark { margin-top:.7rem; }

.nx-fcard-head { display:flex; align-items:center; gap:.55rem; flex-wrap:wrap; margin-bottom:.5rem; }
.nx-ft { font-size:1.04rem; font-weight:800; color:var(--nx-ink); }
.nx-badge { font-size:.67rem; font-weight:800; letter-spacing:.05em; padding:.2rem .55rem; border-radius:999px; }
.nx-chip { font-size:.7rem; font-weight:600; color:var(--nx-muted) !important;
  background:var(--nx-accent-soft); border-radius:999px; padding:.2rem .55rem; }
.nx-alert { border-radius:14px; padding:.95rem 1.15rem; margin-top:1rem; border:1px solid; }
</style>
"""


def inject_css() -> None:
    css = _CSS_TEMPLATE
    for key, value in palette().items():
        css = css.replace(f"__{key}__", value)
    st.markdown(css, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# SVG helpers (all generated -- no external assets)
# ---------------------------------------------------------------------------

def sparkline(values: list[float], color: str | None = None, w: int = 150, h: int = 34) -> str:
    """Tiny inline trend line for KPI cards. Returns '' when there isn't enough
    data to draw an honest line, rather than faking a shape.
    """
    if not values or len(values) < 2:
        return ""
    color = color or palette()["accent"]
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    step = w / (len(values) - 1)
    pts = [(i * step, h - 4 - ((v - lo) / span) * (h - 8)) for i, v in enumerate(values)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"0,{h} " + line + f" {w},{h}"
    uid = abs(hash(tuple(values))) % 100000
    return (
        f'<svg class="nx-spark" width="100%" height="{h}" viewBox="0 0 {w} {h}" '
        f'preserveAspectRatio="none" aria-hidden="true">'
        f'<defs><linearGradient id="sp{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity=".28"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/></linearGradient></defs>'
        f'<polygon points="{area}" fill="url(#sp{uid})"/>'
        f'<polyline points="{line}" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )


def _hero_svg() -> str:
    p = palette()
    glass_hi = "#FFFFFF" if current_mode() == "light" else "#3A3560"
    glass_lo = "#DAD5FA" if current_mode() == "light" else "#221E42"
    stroke = "#FFFFFF" if current_mode() == "light" else "#4A4470"
    return f"""
<svg viewBox="0 0 520 420" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Illustration: translucent data panels above gradient columns on a glass platter">
  <defs>
    <linearGradient id="gGlass" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{glass_hi}" stop-opacity=".92"/>
      <stop offset="100%" stop-color="{glass_lo}" stop-opacity=".55"/></linearGradient>
    <linearGradient id="gPurple" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{p['accent2']}"/><stop offset="100%" stop-color="{p['accent']}"/></linearGradient>
    <linearGradient id="gTeal" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#7FE3DA"/><stop offset="100%" stop-color="#3FBFB3"/></linearGradient>
    <linearGradient id="gLilac" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#CFC8FB"/><stop offset="100%" stop-color="#A99EF3"/></linearGradient>
    <linearGradient id="gPlate" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{glass_hi}" stop-opacity=".95"/>
      <stop offset="100%" stop-color="{glass_lo}" stop-opacity=".6"/></linearGradient>
    <filter id="fSoft" x="-40%" y="-40%" width="180%" height="180%">
      <feDropShadow dx="0" dy="14" stdDeviation="18" flood-color="{p['accent']}" flood-opacity=".22"/></filter>
    <filter id="fLight" x="-40%" y="-40%" width="180%" height="180%">
      <feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="{p['accent']}" flood-opacity=".18"/></filter>
  </defs>
  <ellipse cx="260" cy="330" rx="176" ry="30" fill="{p['accent']}" opacity=".10"/>
  <g filter="url(#fSoft)">
    <rect x="176" y="196" width="46" height="126" rx="23" fill="url(#gLilac)"/>
    <rect x="234" y="150" width="46" height="172" rx="23" fill="url(#gPurple)"/>
    <rect x="292" y="216" width="46" height="106" rx="23" fill="url(#gTeal)"/>
    <rect x="350" y="176" width="46" height="146" rx="23" fill="url(#gLilac)"/>
  </g>
  <g filter="url(#fLight)">
    <ellipse cx="286" cy="322" rx="150" ry="30" fill="url(#gPlate)" stroke="{stroke}" stroke-opacity=".9"/>
    <ellipse cx="286" cy="316" rx="150" ry="30" fill="{glass_hi}" opacity=".34"/>
  </g>
  <g filter="url(#fLight)">
    <rect x="60" y="96" width="96" height="96" rx="26" fill="url(#gGlass)" stroke="{stroke}"/>
    <rect x="84" y="124" width="26" height="26" rx="8" fill="{p['accent']}" opacity=".85"/>
    <rect x="112" y="146" width="22" height="22" rx="7" fill="#3FBFB3" opacity=".85"/></g>
  <g filter="url(#fLight)">
    <rect x="330" y="42" width="86" height="86" rx="24" fill="url(#gGlass)" stroke="{stroke}"/>
    <path d="M350 96 L368 74 L384 88 L400 62" stroke="{p['accent']}" stroke-width="5" fill="none"
          stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="400" cy="62" r="6" fill="{p['accent']}"/></g>
  <g filter="url(#fLight)">
    <rect x="424" y="168" width="74" height="74" rx="22" fill="url(#gGlass)" stroke="{stroke}"/>
    <rect x="444" y="190" width="34" height="9" rx="4.5" fill="{p['accent2']}"/>
    <rect x="444" y="206" width="24" height="9" rx="4.5" fill="#3FBFB3"/>
    <rect x="444" y="222" width="30" height="9" rx="4.5" fill="#CFC8FB"/></g>
  <g filter="url(#fLight)">
    <rect x="150" y="24" width="66" height="66" rx="20" fill="url(#gGlass)" stroke="{stroke}"/>
    <circle cx="183" cy="57" r="17" fill="none" stroke="{p['accent']}" stroke-width="5"/>
    <path d="M183 40 A17 17 0 0 1 200 57 L183 57 Z" fill="#3FBFB3"/></g>
  <circle cx="472" cy="112" r="9" fill="{p['accent2']}" opacity=".55"/>
  <circle cx="40" cy="238" r="7" fill="#3FBFB3" opacity=".5"/>
</svg>
"""


def scene(name: str) -> str:
    """Illustrated card art.

    Monoline icons are what make a product look generated -- every card gets
    the same weight, the same abstraction, no personality. These are small
    drawn scenes instead: depth, multiple objects, warm/cool contrast, a
    subject doing something. Still pure SVG (free, scalable, themes with the
    palette, no binary assets and nothing copied from the references).
    """
    p = palette()
    a, a2 = p["accent"], p["accent2"]
    teal, amber, rose = "#3FBFB3", "#F0B457", "#F2789F"
    card = p["surface"] if current_mode() == "light" else p["raised"]
    line = p["border"]
    skin, skin2 = "#F2C9A0", "#C98B62"
    o = f'<svg viewBox="0 0 200 130" width="100%" height="118" xmlns="http://www.w3.org/2000/svg" role="img"'

    if name == "see":
        return (f'{o} aria-label="A person studying a dashboard through a magnifying glass">'
                f'<rect x="18" y="16" width="128" height="82" rx="10" fill="{card}" stroke="{line}" stroke-width="2"/>'
                f'<rect x="18" y="16" width="128" height="16" rx="10" fill="{a}" opacity=".16"/>'
                f'<circle cx="28" cy="24" r="3" fill="{rose}"/><circle cx="37" cy="24" r="3" fill="{amber}"/>'
                f'<circle cx="46" cy="24" r="3" fill="{teal}"/>'
                f'<rect x="30" y="66" width="14" height="22" rx="4" fill="{a2}"/>'
                f'<rect x="50" y="52" width="14" height="36" rx="4" fill="{a}"/>'
                f'<rect x="70" y="60" width="14" height="28" rx="4" fill="{teal}"/>'
                f'<rect x="90" y="44" width="14" height="44" rx="4" fill="{a2}"/>'
                f'<polyline points="34,60 57,46 77,54 97,38 120,44" fill="none" stroke="{amber}"'
                f' stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
                f'<circle cx="140" cy="82" r="26" fill="#fff" fill-opacity=".22" stroke="{a}" stroke-width="5"/>'
                f'<line x1="158" y1="100" x2="176" y2="118" stroke="{a}" stroke-width="7" stroke-linecap="round"/>'
                f'</svg>')

    if name == "explain":
        return (f'{o} aria-label="An assistant explaining a chart in a speech bubble">'
                f'<path d="M14 22h104a10 10 0 0 1 10 10v40a10 10 0 0 1-10 10H52l-18 16V82H14A10 10 0 0 1 4 72V32a10 10 0 0 1 10-10z"'
                f' transform="translate(8,0)" fill="{card}" stroke="{line}" stroke-width="2"/>'
                f'<rect x="34" y="40" width="62" height="7" rx="3.5" fill="{a}" opacity=".85"/>'
                f'<rect x="34" y="54" width="84" height="7" rx="3.5" fill="{line}"/>'
                f'<rect x="34" y="68" width="46" height="7" rx="3.5" fill="{line}"/>'
                f'<circle cx="160" cy="46" r="17" fill="{a}" opacity=".18"/>'
                f'<circle cx="160" cy="41" r="10" fill="{skin}"/>'
                f'<path d="M160 31a10 10 0 0 1 10 10h-20a10 10 0 0 1 10-10z" fill="{skin2}"/>'
                f'<path d="M144 68c2-10 8-15 16-15s14 5 16 15z" fill="{a2}"/>'
                f'<circle cx="156" cy="41" r="1.6" fill="#3A2A1E"/><circle cx="165" cy="41" r="1.6" fill="#3A2A1E"/>'
                f'<path d="M156 46q4 3 8 0" stroke="#3A2A1E" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
                f'</svg>')

    if name == "act":
        return (f'{o} aria-label="A checklist with a completed action and an upward result">'
                f'<rect x="20" y="14" width="94" height="100" rx="10" fill="{card}" stroke="{line}" stroke-width="2"/>'
                f'<rect x="52" y="8" width="30" height="12" rx="6" fill="{a}"/>'
                f'<circle cx="36" cy="42" r="8" fill="{teal}"/>'
                f'<path d="M32 42l3 3 6-6" stroke="#fff" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
                f'<rect x="50" y="38" width="52" height="7" rx="3.5" fill="{line}"/>'
                f'<circle cx="36" cy="66" r="8" fill="{teal}"/>'
                f'<path d="M32 66l3 3 6-6" stroke="#fff" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
                f'<rect x="50" y="62" width="40" height="7" rx="3.5" fill="{line}"/>'
                f'<circle cx="36" cy="90" r="8" fill="none" stroke="{a}" stroke-width="2.6"/>'
                f'<rect x="50" y="86" width="46" height="7" rx="3.5" fill="{line}"/>'
                f'<path d="M132 96 L150 62 L166 74 L182 34" fill="none" stroke="{a}" stroke-width="5"'
                f' stroke-linecap="round" stroke-linejoin="round"/>'
                f'<path d="M170 34h13v13" fill="none" stroke="{a}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
                f'<circle cx="150" cy="62" r="4.5" fill="{amber}"/><circle cx="166" cy="74" r="4.5" fill="{teal}"/>'
                f'</svg>')

    if name == "trust":
        return (f'{o} aria-label="A shield guarding a verified figure">'
                f'<path d="M100 12l40 15v33c0 27-17 45-40 58-23-13-40-31-40-58V27z" fill="{a}" opacity=".14"/>'
                f'<path d="M100 12l40 15v33c0 27-17 45-40 58-23-13-40-31-40-58V27z" fill="none" stroke="{a}" stroke-width="3"/>'
                f'<path d="M84 63l11 11 22-24" stroke="{teal}" stroke-width="7" fill="none"'
                f' stroke-linecap="round" stroke-linejoin="round"/>'
                f'<rect x="12" y="46" width="40" height="26" rx="6" fill="{card}" stroke="{line}" stroke-width="2"/>'
                f'<rect x="19" y="54" width="26" height="4" rx="2" fill="{a2}"/>'
                f'<rect x="19" y="62" width="16" height="4" rx="2" fill="{line}"/>'
                f'<rect x="148" y="46" width="40" height="26" rx="6" fill="{card}" stroke="{line}" stroke-width="2"/>'
                f'<rect x="155" y="54" width="26" height="4" rx="2" fill="{teal}"/>'
                f'<rect x="155" y="62" width="18" height="4" rx="2" fill="{line}"/>'
                f'<circle cx="46" cy="100" r="5" fill="{amber}"/><circle cx="156" cy="100" r="5" fill="{rose}"/>'
                f'</svg>')

    if name == "upload":
        return (f'{o} aria-label="Business files being carried into the workspace">'
                f'<rect x="60" y="30" width="86" height="72" rx="10" fill="{card}" stroke="{line}" stroke-width="2"/>'
                f'<path d="M60 40a10 10 0 0 1 10-10h22l8 10z" fill="{a}" opacity=".22"/>'
                f'<rect x="72" y="56" width="46" height="6" rx="3" fill="{line}"/>'
                f'<rect x="72" y="70" width="62" height="6" rx="3" fill="{line}"/>'
                f'<rect x="72" y="84" width="34" height="6" rx="3" fill="{line}"/>'
                f'<rect x="18" y="52" width="42" height="52" rx="8" fill="{a2}" opacity=".9"/>'
                f'<text x="39" y="84" font-size="15" font-weight="700" fill="#fff" text-anchor="middle"'
                f' font-family="Plus Jakarta Sans, sans-serif">CSV</text>'
                f'<rect x="146" y="60" width="40" height="44" rx="8" fill="{rose}" opacity=".85"/>'
                f'<text x="166" y="88" font-size="13" font-weight="700" fill="#fff" text-anchor="middle"'
                f' font-family="Plus Jakarta Sans, sans-serif">PDF</text>'
                f'<path d="M100 24v-14" stroke="{a}" stroke-width="4" stroke-linecap="round"/>'
                f'<path d="M92 16l8-8 8 8" fill="none" stroke="{a}" stroke-width="4"'
                f' stroke-linecap="round" stroke-linejoin="round"/>'
                f'</svg>')

    if name == "revenue":
        return (f'{o} aria-label="Rising revenue bars with a profit line lagging behind">'
                f'<rect x="16" y="18" width="168" height="94" rx="12" fill="{card}" stroke="{line}" stroke-width="2"/>'
                f'<rect x="34" y="74" width="18" height="26" rx="4" fill="{a2}" opacity=".55"/>'
                f'<rect x="60" y="62" width="18" height="38" rx="4" fill="{a2}" opacity=".7"/>'
                f'<rect x="86" y="50" width="18" height="50" rx="4" fill="{a}" opacity=".85"/>'
                f'<rect x="112" y="38" width="18" height="62" rx="4" fill="{a}"/>'
                f'<rect x="138" y="30" width="18" height="70" rx="4" fill="{a}"/>'
                f'<polyline points="43,78 69,72 95,68 121,64 147,62" fill="none" stroke="{amber}"'
                f' stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="5 4"/>'
                f'<circle cx="147" cy="62" r="5" fill="{amber}" stroke="{card}" stroke-width="2"/>'
                f'<text x="30" y="34" font-size="9" font-weight="700" fill="{p["muted"]}"'
                f' font-family="Plus Jakarta Sans, sans-serif">REVENUE</text></svg>')

    if name == "product":
        return (f'{o} aria-label="Stacked product boxes ranked by performance">'
                f'<rect x="24" y="60" width="44" height="44" rx="8" fill="{a2}" opacity=".8"/>'
                f'<path d="M24 74h44" stroke="{card}" stroke-width="3"/>'
                f'<rect x="78" y="40" width="44" height="64" rx="8" fill="{a}"/>'
                f'<path d="M78 58h44" stroke="{card}" stroke-width="3"/>'
                f'<rect x="132" y="70" width="44" height="34" rx="8" fill="{teal}" opacity=".85"/>'
                f'<path d="M132 82h44" stroke="{card}" stroke-width="3"/>'
                f'<path d="M100 24l4.5 9 10 1.5-7 7 1.5 10-9-4.5-9 4.5 1.5-10-7-7 10-1.5z" fill="{amber}"/>'
                f'</svg>')

    if name == "customer":
        return (f'{o} aria-label="Three customer profiles of differing value">'
                f'<circle cx="52" cy="52" r="15" fill="{skin}"/>'
                f'<path d="M52 39a13 13 0 0 1 13 13H39a13 13 0 0 1 13-13z" fill="{skin2}"/>'
                f'<path d="M32 100c2-14 10-21 20-21s18 7 20 21z" fill="{a2}"/>'
                f'<circle cx="100" cy="44" r="18" fill="{skin}"/>'
                f'<path d="M100 28a16 16 0 0 1 16 16H84a16 16 0 0 1 16-16z" fill="#4A3728"/>'
                f'<path d="M76 100c2-16 11-24 24-24s22 8 24 24z" fill="{a}"/>'
                f'<circle cx="148" cy="54" r="14" fill="{skin}"/>'
                f'<path d="M148 42a12 12 0 0 1 12 12h-24a12 12 0 0 1 12-12z" fill="{skin2}"/>'
                f'<path d="M130 100c2-13 9-19 18-19s16 6 18 19z" fill="{teal}"/>'
                f'<path d="M100 14l3.5 7 7.5 1-5.5 5.5 1.5 7.5-7-3.5-7 3.5 1.5-7.5-5.5-5.5 7.5-1z" fill="{amber}"/>'
                f'</svg>')

    if name == "inventory":
        return (f'{o} aria-label="Warehouse shelves with one bay empty and one overstocked">'
                f'<rect x="20" y="24" width="76" height="86" rx="8" fill="{card}" stroke="{line}" stroke-width="2"/>'
                f'<line x1="20" y1="52" x2="96" y2="52" stroke="{line}" stroke-width="2"/>'
                f'<line x1="20" y1="80" x2="96" y2="80" stroke="{line}" stroke-width="2"/>'
                f'<rect x="28" y="32" width="18" height="16" rx="3" fill="{a}"/>'
                f'<rect x="50" y="32" width="18" height="16" rx="3" fill="{a2}"/>'
                f'<rect x="28" y="60" width="18" height="16" rx="3" fill="{teal}"/>'
                f'<text x="66" y="73" font-size="15" font-weight="800" fill="{rose}"'
                f' font-family="Plus Jakarta Sans, sans-serif">!</text>'
                f'<rect x="104" y="24" width="76" height="86" rx="8" fill="{card}" stroke="{line}" stroke-width="2"/>'
                f'<line x1="104" y1="52" x2="180" y2="52" stroke="{line}" stroke-width="2"/>'
                f'<line x1="104" y1="80" x2="180" y2="80" stroke="{line}" stroke-width="2"/>'
                f'<rect x="110" y="30" width="16" height="18" rx="3" fill="{a}"/>'
                f'<rect x="130" y="30" width="16" height="18" rx="3" fill="{a2}"/>'
                f'<rect x="150" y="30" width="16" height="18" rx="3" fill="{a}"/>'
                f'<rect x="110" y="58" width="16" height="18" rx="3" fill="{a2}"/>'
                f'<rect x="130" y="58" width="16" height="18" rx="3" fill="{teal}"/>'
                f'<rect x="150" y="58" width="16" height="18" rx="3" fill="{a}"/>'
                f'<rect x="110" y="86" width="16" height="18" rx="3" fill="{a}"/>'
                f'<rect x="130" y="86" width="16" height="18" rx="3" fill="{a2}"/>'
                f'</svg>')

    if name == "delivery":
        return (f'{o} aria-label="A delivery van running behind a clock">'
                f'<rect x="20" y="46" width="72" height="42" rx="7" fill="{a}"/>'
                f'<path d="M92 58h22l16 16v14H92z" fill="{a2}"/>'
                f'<rect x="98" y="62" width="16" height="12" rx="3" fill="{card}" opacity=".8"/>'
                f'<circle cx="46" cy="94" r="11" fill="{p["ink"]}"/><circle cx="46" cy="94" r="4.5" fill="{card}"/>'
                f'<circle cx="116" cy="94" r="11" fill="{p["ink"]}"/><circle cx="116" cy="94" r="4.5" fill="{card}"/>'
                f'<line x1="6" y1="56" x2="18" y2="56" stroke="{a2}" stroke-width="3" stroke-linecap="round"/>'
                f'<line x1="2" y1="68" x2="18" y2="68" stroke="{a2}" stroke-width="3" stroke-linecap="round" opacity=".6"/>'
                f'<circle cx="160" cy="46" r="24" fill="{card}" stroke="{rose}" stroke-width="4"/>'
                f'<path d="M160 32v14l10 6" stroke="{rose}" stroke-width="4" fill="none"'
                f' stroke-linecap="round" stroke-linejoin="round"/></svg>')

    if name == "targets":
        return (f'{o} aria-label="A dartboard with an arrow near the centre and a spend gauge">'
                f'<circle cx="66" cy="64" r="42" fill="{card}" stroke="{line}" stroke-width="2"/>'
                f'<circle cx="66" cy="64" r="30" fill="{a}" opacity=".16"/>'
                f'<circle cx="66" cy="64" r="18" fill="{a}" opacity=".3"/>'
                f'<circle cx="66" cy="64" r="7" fill="{rose}"/>'
                f'<line x1="98" y1="30" x2="70" y2="60" stroke="{p["ink"]}" stroke-width="4" stroke-linecap="round"/>'
                f'<path d="M98 30l12-6-6 12z" fill="{amber}"/>'
                f'<path d="M126 96a34 34 0 0 1 68 0z" fill="{card}" stroke="{line}" stroke-width="2"/>'
                f'<path d="M126 96a34 34 0 0 1 20-31l14 31z" fill="{rose}" opacity=".8"/>'
                f'<path d="M146 65a34 34 0 0 1 34 0l-20 31z" fill="{amber}" opacity=".85"/>'
                f'<path d="M180 65a34 34 0 0 1 14 31h-34z" fill="{teal}" opacity=".85"/>'
                f'<line x1="160" y1="96" x2="178" y2="74" stroke="{p["ink"]}" stroke-width="4" stroke-linecap="round"/>'
                f'<circle cx="160" cy="96" r="5" fill="{p["ink"]}"/></svg>')

    # "data" -- generic analysis scene
    return (f'{o} aria-label="Charts and figures being analysed">'
            f'<rect x="16" y="20" width="168" height="90" rx="12" fill="{card}" stroke="{line}" stroke-width="2"/>'
            f'<rect x="30" y="72" width="18" height="26" rx="4" fill="{a2}"/>'
            f'<rect x="54" y="56" width="18" height="42" rx="4" fill="{a}"/>'
            f'<rect x="78" y="66" width="18" height="32" rx="4" fill="{teal}"/>'
            f'<circle cx="146" cy="58" r="26" fill="{a}" opacity=".16"/>'
            f'<path d="M146 32a26 26 0 0 1 26 26h-26z" fill="{a}"/>'
            f'<path d="M146 58h26a26 26 0 0 1-13 22z" fill="{teal}"/>'
            f'<rect x="30" y="34" width="52" height="6" rx="3" fill="{line}"/>'
            f'</svg>')


def _icon(path: str, color: str | None = None) -> str:
    color = color or palette()["accent"]
    return (f'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{path}</svg>')


_ICONS = {
    "see": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
    "explain": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "act": '<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>',
    "trust": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    "chart": '<path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/>',
    "layers": '<path d="m12 2 9 5-9 5-9-5 9-5z"/><path d="m3 17 9 5 9-5"/><path d="m3 12 9 5 9-5"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>',
    "box": '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>',
    "truck": '<path d="M14 18V6a2 2 0 0 0-2-2H3v13"/><path d="M14 9h4l3 3v6h-2"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "cash": '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/>',
    "orders": '<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/>',
    "percent": '<line x1="19" y1="5" x2="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/>',
}


# ---------------------------------------------------------------------------
# Landing page
# ---------------------------------------------------------------------------

def render_landing(kpi_preview: dict | None = None) -> str | None:
    """Returns 'demo', 'upload', or None."""
    _html(f"""
    <div class="nx-nav">
      <a class="nx-brand" href="#nx-top"><div class="nx-logo">N</div> NexaSphere</a>
      <div class="nx-navlinks">
        <a href="#nx-product">Product</a>
        <a href="#nx-how">How it works</a>
        <a href="#nx-trust">AI &amp; Trust</a>
        <a href="#nx-value">Business value</a>
      </div>
      <div class="nx-navcta">BuildFest 2026</div>
    </div>
    <div id="nx-top" class="nx-hero">
      <div>
        <div class="nx-eyebrow"><span class="nx-dot"></span> Evidence-backed business intelligence</div>
        <h1>Turn business data<br/>into decisions.</h1>
        <p class="nx-lede">Upload the files you already use. NexaSphere works out what your data can
        reliably answer, calculates the numbers itself, and explains what they mean in plain
        language &mdash; without letting AI invent a single figure.</p>
      </div>
      <div>{_hero_svg()}</div>
    </div>
    """)

    c1, c2, _ = st.columns([1.05, 1, 1.6])
    go_upload = c1.button("Analyze My Business", type="primary", use_container_width=True)
    go_demo = c2.button("Explore Demo", use_container_width=True)

    if kpi_preview:
        def d(v):
            if v is None:
                return ""
            cls = "nx-up" if v >= 0 else "nx-down"
            return f'<div class="nx-d {cls}">{"▲" if v >= 0 else "▼"} {abs(v):.1f}%</div>'
        _html(f"""
        <div class="nx-statrow">
          <div class="nx-stat"><div class="nx-k">Revenue analysed</div>
            <div class="nx-v">{kpi_preview['revenue']}</div>{d(kpi_preview.get('revenue_pct'))}</div>
          <div class="nx-stat"><div class="nx-k">Gross profit</div>
            <div class="nx-v">{kpi_preview['profit']}</div>{d(kpi_preview.get('profit_pct'))}</div>
          <div class="nx-stat"><div class="nx-k">Gross margin</div>
            <div class="nx-v">{kpi_preview['margin']}</div>
            <div class="nx-d nx-down">▼ {kpi_preview['margin_pp']} pp</div></div>
          <div class="nx-stat"><div class="nx-k">Orders</div>
            <div class="nx-v">{kpi_preview['orders']}</div>
            <div class="nx-kn">Live from the demo workspace</div></div>
        </div>
        <p style="color:var(--nx-muted);font-size:.79rem;margin:.5rem 0 0;">
          Real figures computed by the analytics engine from the demo dataset &mdash;
          not illustrative placeholders.</p>
        """)

    _html(f"""
    <div id="nx-product" class="nx-sectionhead">
      <div class="nx-tag">Why it's different</div>
      <h2>See. Explain. Act. Trust.</h2>
      <p>Traditional dashboards tell you what happened. NexaSphere helps you understand why it
         matters and what to investigate next.</p>
    </div>
    <div class="nx-grid">
      <div class="nx-card"><div class="nx-art">{scene('see')}</div><h4>See</h4>
        <p>KPIs and trends computed directly from your own data, never estimated.</p></div>
      <div class="nx-card"><div class="nx-art">{scene('explain')}</div><h4>Explain</h4>
        <p>Ask questions in plain language &mdash; formal, casual, or Pidgin.</p></div>
      <div class="nx-card"><div class="nx-art">{scene('act')}</div><h4>Act</h4>
        <p>Every finding carries an evidence trail and a recommended next step.</p></div>
      <div class="nx-card"><div class="nx-art">{scene('trust')}</div><h4>Trust</h4>
        <p>The AI explains verified numbers. It is never the source of them.</p></div>
    </div>

    <div id="nx-how" class="nx-sectionhead">
      <div class="nx-tag">How it works</div><h2>From raw files to a decision</h2>
    </div>
    <div class="nx-flow">
      <div class="nx-fstep"><div class="nx-n">01</div><div class="nx-l">Upload</div>
        <div class="nx-s">CSV, Excel, JSON, PDF, Word</div></div>
      <div class="nx-fstep"><div class="nx-n">02</div><div class="nx-l">Inspect</div>
        <div class="nx-s">Quality, columns, relationships</div></div>
      <div class="nx-fstep"><div class="nx-n">03</div><div class="nx-l">Confirm</div>
        <div class="nx-s">You approve every mapping</div></div>
      <div class="nx-fstep"><div class="nx-n">04</div><div class="nx-l">Analyse</div>
        <div class="nx-s">Verified calculations run</div></div>
      <div class="nx-fstep"><div class="nx-n">05</div><div class="nx-l">Ask</div>
        <div class="nx-s">Questions in your own words</div></div>
      <div class="nx-fstep"><div class="nx-n">06</div><div class="nx-l">Act</div>
        <div class="nx-s">Evidence-backed recommendations</div></div>
    </div>
    """)

    _html("<div style='height:3rem'></div>")
    _html("""
    <div id="nx-trust" class="nx-dark">
      <h2>AI explains the numbers. It doesn't make them up.</h2>
      <p>Most "chat with your data" tools let a language model read your spreadsheet and produce
         figures. NexaSphere doesn't. Calculations run first, in pandas. The AI receives only the
         verified result, and any sentence containing a number that isn't in that evidence is
         rejected before you ever see it.</p>
      <div class="nx-pipe">
        <div class="nx-node">Your data</div><div class="nx-ar">→</div>
        <div class="nx-node">Verified calculations</div><div class="nx-ar">→</div>
        <div class="nx-node">Business evidence</div><div class="nx-ar">→</div>
        <div class="nx-node nx-hl">AI explanation</div><div class="nx-ar">→</div>
        <div class="nx-node">Recommendation</div>
      </div>
    </div>
    """)

    _html(f"""
    <div id="nx-value" class="nx-sectionhead">
      <div class="nx-tag">Capabilities</div><h2>What NexaSphere can analyse</h2>
      <p>Availability depends on what your uploaded data actually contains &mdash; NexaSphere tells
         you which of these it supports, and which it can't.</p>
    </div>
    <div class="nx-grid">
      <div class="nx-card"><div class="nx-art">{scene('revenue')}</div><h4>Revenue &amp; profitability</h4>
        <p>Spot when growth stops translating into margin.</p></div>
      <div class="nx-card"><div class="nx-art">{scene('product')}</div><h4>Product performance</h4>
        <p>Which lines carry the business, and which drag on it.</p></div>
      <div class="nx-card"><div class="nx-art">{scene('customer')}</div><h4>Customer value</h4>
        <p>Which segments and accounts actually drive revenue.</p></div>
      <div class="nx-card"><div class="nx-art">{scene('inventory')}</div><h4>Inventory position</h4>
        <p>Where stock runs out, and where it sits idle.</p></div>
      <div class="nx-card"><div class="nx-art">{scene('delivery')}</div><h4>Delivery performance</h4>
        <p>Which partners are creating service risk.</p></div>
      <div class="nx-card"><div class="nx-art">{scene('targets')}</div><h4>Targets &amp; marketing ROI</h4>
        <p>Where attainment slips and which spend pays back.</p></div>
    </div>

    <div class="nx-sectionhead"><div class="nx-tag">Trust</div><h2>Your data. Your analysis.</h2></div>
    <div style="background:var(--nx-surface);border:1px solid var(--nx-border);border-radius:18px;padding:.5rem 1.35rem;">
      <div class="nx-trust"><div class="nx-ck">✓</div><div><b>Verified calculations.</b>
        <span>Every KPI is real pandas arithmetic, not a model's guess.</span></div></div>
      <div class="nx-trust"><div class="nx-ck">✓</div><div><b>Your files stay out of the prompt.</b>
        <span>The AI receives aggregated evidence, never your raw dataset.</span></div></div>
      <div class="nx-trust"><div class="nx-ck">✓</div><div><b>Session-scoped.</b>
        <span>Uploads are analysed in your session and are not permanently stored.</span></div></div>
      <div class="nx-trust"><div class="nx-ck">✓</div><div><b>Honest limits.</b>
        <span>If your data can't answer something, NexaSphere says so instead of inventing an answer.</span></div></div>
      <div class="nx-trust"><div class="nx-ck">✓</div><div><b>You decide.</b>
        <span>NexaSphere surfaces what to investigate. It never acts on your business by itself.</span></div></div>
    </div>
    """)

    _html("<div style='height:3rem'></div>")
    _html("""
    <div class="nx-finalcta">
      <h2>Your data already knows more than you think.</h2>
      <p>Bring the files you already have. Find out what they can tell you.</p>
    </div><div style='height:1rem'></div>
    """)
    c3, c4, _ = st.columns([1.05, 1, 1.6])
    up2 = c3.button("Analyze My Business", key="cta2_upload", type="primary", use_container_width=True)
    dm2 = c4.button("Explore Demo", key="cta2_demo", use_container_width=True)

    _html("""
    <div class="nx-foot"><b style="color:var(--nx-ink);">NexaSphere</b> &middot;
      AI Business Intelligence Assistant &middot; BuildFest 2026<br/>
      The data calculates. The AI explains. The evidence builds trust. The human decides.</div>
    """)

    if go_demo or dm2:
        return "demo"
    if go_upload or up2:
        return "upload"
    return None


# ---------------------------------------------------------------------------
# Dashboard chrome
# ---------------------------------------------------------------------------

NAV_PAGES = ["Overview", "Findings", "Ask NexaSphere", "Dashboards", "Analyze My Business"]


def app_shell(workspace: str) -> tuple[str, bool]:
    """Renders the app header (logo-home, workspace chip, theme toggle) and the
    pill navigation. Returns (active_page, go_home_clicked).
    """
    left, mid, right = st.columns([0.06, 0.88, 0.06])

    with left:
        with st.container(key="nx_home"):
            go_home = st.button("⌂", help="Back to landing page")
    with mid:
        _html(f"""
        <div style="display:flex;align-items:center;gap:.7rem;height:100%;padding-top:.15rem;">
          <div class="nx-logo">N</div>
          <div><div style="font-weight:800;font-size:1.02rem;color:var(--nx-ink);line-height:1.15;">NexaSphere</div>
          <div style="font-size:.74rem;color:var(--nx-muted);">Workspace &middot; {workspace}</div></div>
        </div>
        """)
    with right:
        with st.container(key="nx_theme"):
            dark = current_mode() == "dark"
            if st.button("☀" if dark else "☾",
                          help="Switch to light theme" if dark else "Switch to dark theme"):
                st.session_state["nx_theme"] = "light" if dark else "dark"
                st.rerun()

    _html("<div style='height:.9rem'></div>")
    page = st.radio("Navigate", NAV_PAGES, horizontal=True,
                     label_visibility="collapsed", key="nx_active_page")
    _html("<div style='height:1.4rem'></div>")
    return page, go_home


def page_title(title: str, subtitle: str) -> None:
    _html(f"""
    <h1 style="font-size:2rem;font-weight:800;margin:0 0 .25rem;">{title}</h1>
    <p style="color:var(--nx-muted);font-size:.95rem;margin:0 0 1.3rem;">{subtitle}</p>
    """)


def kpi_card(label: str, value: str, delta: str | None = None, positive: bool | None = None,
             note: str = "", icon: str | None = None, spark: list[float] | None = None) -> str:
    p = palette()
    icon_html = _icon(_ICONS[icon], p["muted"]) if icon and icon in _ICONS else ""
    delta_html = ""
    if delta:
        cls = "nx-up" if positive else "nx-down"
        delta_html = f'<div class="nx-kd {cls}">{"▲" if positive else "▼"} {delta}</div>'
    spark_html = sparkline(spark, p["ok"] if positive else p["bad"]) if spark else ""
    note_html = f'<div class="nx-kn">{note}</div>' if note else ""
    return (f'<div class="nx-kpi"><div><div class="nx-kl"><span>{label}</span>{icon_html}</div>'
            f'<div class="nx-kv">{value}</div>{delta_html}{note_html}</div>{spark_html}</div>')


def finding_header(title: str, severity: str, category: str, confidence: str | None = None) -> str:
    color, bg = severity_colors(severity)
    conf = f'<span class="nx-chip">confidence: {confidence.upper()}</span>' if confidence else ""
    return (f'<div class="nx-fcard-head"><span class="nx-ft">{title}</span>'
            f'<span class="nx-badge" style="background:{bg};color:{color};">{severity.upper()}</span>'
            f'<span class="nx-chip">{category}</span>{conf}</div>')


def alert(kind: str, title: str, body: str) -> str:
    p = palette()
    tone = {"warning": (p["warn"], p["warn_bg"]), "error": (p["bad"], p["bad_bg"]),
             "success": (p["ok"], p["ok_bg"]), "info": (p["accent"], p["accent_soft"])}[kind]
    color, bg = tone
    return (f'<div class="nx-alert" style="background:{bg};border-color:{color};border-left:4px solid {color};">'
            f'<b style="color:var(--nx-ink);font-size:.93rem;">{title}</b>'
            f'<div style="color:var(--nx-muted);font-size:.87rem;margin-top:.25rem;line-height:1.55;">{body}</div></div>')


def chart_colors() -> list[str]:
    p = palette()
    return [p["accent"], "#3FBFB3", p["accent2"], p["warn"], "#F2789F", p["ok"]]


def apply_chart_defaults() -> None:
    """Sets Plotly Express' default sequences to the NexaSphere palette.

    plotly_theme's `layout.colorway` alone is not enough: px assigns each
    trace an explicit colour at creation time from its own default sequence,
    which then wins over the layout colorway -- that is why charts stayed
    Plotly-blue. Setting px.defaults up front fixes every chart at once
    instead of threading color_discrete_sequence through each call site.
    """
    import plotly.express as px

    p = palette()
    px.defaults.color_discrete_sequence = chart_colors()
    px.defaults.color_continuous_scale = [
        [0.0, p["bad"]], [0.5, p["warn"]], [1.0, p["ok"]],
    ]


def plotly_theme(fig, height: int = 320):
    p = palette()
    fig.update_layout(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, sans-serif", size=12, color=p["muted"]),
        title=dict(font=dict(size=15, color=p["ink"]), x=0, xanchor="left"),
        margin=dict(l=8, r=8, t=46, b=8),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                     bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        colorway=[p["accent"], "#3FBFB3", p["accent2"], p["warn"], p["bad"], p["ok"]],
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor=p["border"], tickfont=dict(size=11))
    fig.update_yaxes(showgrid=True, gridcolor=p["grid"], zeroline=False, tickfont=dict(size=11))
    return fig
