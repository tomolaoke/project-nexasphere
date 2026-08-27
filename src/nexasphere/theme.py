"""NexaSphere design system, landing page and dashboard chrome.

Implementation note (this corrects an earlier assumption in
docs/UI_UX_AUDIT.md section 8): Streamlit's DOM-order layout constraint
applies to its *interactive widgets*. Content rendered through
`st.markdown(..., unsafe_allow_html=True)` lands in the main document, not a
sandboxed iframe, so bespoke CSS Grid layouts, layered/absolute positioning,
gradients, glass effects and inline SVG are all available. Only genuinely
interactive controls (buttons, inputs, uploader) must be Streamlit widgets,
and those are restyled here via their stable `data-testid` hooks.

All illustration is inline SVG generated in this file -- no binary image
assets, no stock photography, no third-party icon package, nothing
downloaded. That keeps the repo clean, the deploy $0, and avoids reproducing
any copyrighted artwork from the visual references, whose *design language*
(light lavender canvas, purple accent, soft rounded cards, glass depth) is
what we're recreating rather than their assets.

Presentation only: nothing here imports or alters analytics, insights, nlg or
user_data.
"""
from __future__ import annotations

import textwrap

import streamlit as st


def _html(markup: str) -> None:
    """Renders raw HTML, removing Python source indentation first.

    Necessary because Streamlit runs this through a Markdown renderer, and
    Markdown treats any line indented by 4+ spaces as a code block -- so an
    HTML block written at normal function indentation renders as visible
    source instead of markup. textwrap.dedent alone is not enough: these
    templates interpolate multi-line SVG that already sits at column 0, which
    drops the common prefix to zero and makes dedent a no-op. Stripping every
    line is safe here because whitespace between HTML tags is insignificant
    and none of this markup contains <pre>-formatted content.
    """
    flattened = "\n".join(line.strip() for line in markup.splitlines())
    st.markdown(flattened.strip(), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------

ACCENT = "#5B4FE9"
ACCENT_SOFT = "#EDEBFD"
INK = "#14142B"
MUTED = "#6E6D8A"
CANVAS = "#F5F4FC"
SURFACE = "#FFFFFF"
BORDER = "#E7E5F5"
DARK_PANEL = "#161428"

SEVERITY_COLOR = {
    "critical": "#E5484D",
    "warning": "#E8A33D",
    "watch": ACCENT,
    "info": "#2FA36B",
}
SEVERITY_BG = {
    "critical": "#FDECEC",
    "warning": "#FDF3E3",
    "watch": ACCENT_SOFT,
    "info": "#E8F6EE",
}

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stMarkdown, button, input, textarea, select {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.stApp {
    background:
        radial-gradient(1100px 520px at 78% -8%, #E4E0FB 0%, rgba(228,224,251,0) 62%),
        radial-gradient(760px 420px at 8% 4%, #EAF4FF 0%, rgba(234,244,255,0) 58%),
        #F5F4FC;
}

.block-container { padding-top: 1.6rem !important; padding-bottom: 3rem !important; max-width: 1180px; }
#MainMenu, footer { visibility: hidden; }
h1, h2, h3, h4 { color: #14142B; letter-spacing: -0.025em; }

/* ---------- Streamlit widget restyling ---------- */
.stButton > button {
    border-radius: 12px; font-weight: 600; padding: 0.62rem 1.15rem;
    border: 1px solid #E7E5F5; background: #FFFFFF; color: #14142B;
    box-shadow: 0 1px 2px rgba(20,20,43,0.05); transition: all .16s ease;
}
.stButton > button:hover { border-color: #C9C3F6; transform: translateY(-1px); box-shadow: 0 6px 18px rgba(91,79,233,.14); }
.stButton > button[kind="primary"] {
    background: linear-gradient(180deg, #6B5CF0 0%, #5B4FE9 100%);
    color: #fff; border: none; box-shadow: 0 6px 18px rgba(91,79,233,.32);
}
.stButton > button[kind="primary"]:hover { box-shadow: 0 10px 26px rgba(91,79,233,.42); }

[data-testid="stMetric"] {
    background: #FFFFFF; border: 1px solid #E7E5F5; border-radius: 16px;
    padding: 1.15rem 1.25rem; box-shadow: 0 1px 2px rgba(20,20,43,.04);
}
[data-testid="stMetricLabel"] { color: #6E6D8A !important; font-weight: 600 !important; font-size: .8rem !important; }
[data-testid="stMetricValue"] { font-weight: 800 !important; letter-spacing: -.03em; }

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF; border: 1px solid #E7E5F5 !important;
    border-radius: 18px !important; box-shadow: 0 1px 2px rgba(20,20,43,.04);
}

.stTabs [data-baseweb="tab-list"] { gap: .3rem; border-bottom: 1px solid #E7E5F5; }
.stTabs [data-baseweb="tab"] { font-weight: 600; color: #6E6D8A; padding: .6rem 1rem; }
.stTabs [aria-selected="true"] { color: #5B4FE9 !important; }
.stTabs [data-baseweb="tab-highlight"] { background: #5B4FE9 !important; height: 2px; }

section[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E7E5F5; }
[data-testid="stFileUploaderDropzone"] {
    background: #FFFFFF; border: 1.5px dashed #C9C3F6; border-radius: 16px; padding: 1.6rem;
}
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
    border-radius: 12px !important; border-color: #E7E5F5 !important;
}
.stTextInput input:focus { border-color: #5B4FE9 !important; box-shadow: 0 0 0 3px rgba(91,79,233,.12) !important; }

/* ---------- Layout primitives ---------- */
.nx-nav {
    display: flex; align-items: center; justify-content: space-between;
    background: rgba(255,255,255,.72); backdrop-filter: blur(14px);
    border: 1px solid #E7E5F5; border-radius: 18px;
    padding: .85rem 1.35rem; margin-bottom: 2.2rem;
    box-shadow: 0 2px 14px rgba(20,20,43,.05);
}
.nx-brand { display: flex; align-items: center; gap: .6rem; font-weight: 800; font-size: 1.06rem; color: #14142B; }
.nx-logo {
    width: 30px; height: 30px; border-radius: 9px;
    background: linear-gradient(135deg, #7C6FF0, #5B4FE9); color: #fff;
    display: grid; place-items: center; font-size: .84rem; font-weight: 800;
    box-shadow: 0 4px 12px rgba(91,79,233,.34);
}
.nx-navlinks { display: flex; gap: 1.7rem; font-size: .875rem; color: #6E6D8A; font-weight: 500; white-space: nowrap; }
.nx-navcta { background: #14142B; color: #fff; border-radius: 999px; padding: .5rem 1.05rem; font-size: .82rem; font-weight: 600; white-space: nowrap; }
/* Marketing nav links are decorative (the real navigation is the CTA buttons
   and the in-app tabs), so drop them rather than let them wrap and clip. */
@media (max-width: 720px) {
    .nx-navlinks { display: none; }
    .nx-nav { padding: .7rem 1rem; }
}

.nx-hero { display: grid; grid-template-columns: 1.08fr .92fr; gap: 2rem; align-items: center; margin-bottom: .6rem; }
@media (max-width: 900px) { .nx-hero { grid-template-columns: 1fr; } }
.nx-eyebrow {
    display: inline-flex; align-items: center; gap: .45rem; background: #EDEBFD; color: #5B4FE9;
    border-radius: 999px; padding: .34rem .85rem; font-size: .76rem; font-weight: 700; margin-bottom: 1.1rem;
}
.nx-eyebrow .nx-dot { width: 6px; height: 6px; border-radius: 50%; background: #5B4FE9; }
.nx-hero h1 { font-size: 3.15rem; line-height: 1.06; font-weight: 800; margin: 0 0 1.05rem; }
@media (max-width: 900px) { .nx-hero h1 { font-size: 2.3rem; } }
.nx-hero .nx-lede { font-size: 1.04rem; line-height: 1.62; color: #6E6D8A; max-width: 30rem; margin: 0; }

.nx-statrow { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px,1fr)); gap: 1rem; margin: 2.4rem 0 .5rem; }
.nx-stat { background: #fff; border: 1px solid #E7E5F5; border-radius: 16px; padding: 1.1rem 1.2rem; box-shadow: 0 1px 2px rgba(20,20,43,.04); }
.nx-stat .nx-k { font-size: .74rem; color: #6E6D8A; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; }
.nx-stat .nx-v { font-size: 1.6rem; font-weight: 800; color: #14142B; letter-spacing: -.03em; margin-top: .3rem; }
.nx-stat .nx-d { font-size: .78rem; font-weight: 700; margin-top: .2rem; }
.nx-up { color: #2FA36B; } .nx-down { color: #E5484D; }

.nx-sectionhead { margin: 3.4rem 0 1.2rem; }
.nx-sectionhead .nx-tag { font-size: .76rem; font-weight: 700; color: #5B4FE9; text-transform: uppercase; letter-spacing: .08em; }
.nx-sectionhead h2 { font-size: 1.95rem; font-weight: 800; margin: .4rem 0 .45rem; }
.nx-sectionhead p { color: #6E6D8A; font-size: .97rem; max-width: 40rem; margin: 0; line-height: 1.6; }

.nx-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(232px,1fr)); gap: 1.1rem; }
.nx-card { background:#fff; border:1px solid #E7E5F5; border-radius:18px; padding:1.5rem; box-shadow:0 1px 2px rgba(20,20,43,.04); transition: all .18s ease; }
.nx-card:hover { transform: translateY(-3px); box-shadow: 0 14px 32px rgba(20,20,43,.09); border-color:#D8D3F8; }
.nx-card .nx-ico { width:42px;height:42px;border-radius:12px;display:grid;place-items:center;margin-bottom:.95rem;background:#EDEBFD; }
.nx-card h4 { font-size:1.02rem; font-weight:700; margin:0 0 .4rem; }
.nx-card p { font-size:.885rem; color:#6E6D8A; line-height:1.58; margin:0; }

.nx-flow { display:flex; align-items:stretch; gap:.55rem; flex-wrap:wrap; }
.nx-fstep { flex:1 1 150px; background:#fff; border:1px solid #E7E5F5; border-radius:14px; padding:1rem .9rem; text-align:center; }
.nx-fstep .nx-n { width:24px;height:24px;border-radius:7px;background:#EDEBFD;color:#5B4FE9;font-size:.72rem;font-weight:800;display:grid;place-items:center;margin:0 auto .55rem; }
.nx-fstep .nx-l { font-size:.83rem; font-weight:700; color:#14142B; }
.nx-fstep .nx-s { font-size:.75rem; color:#6E6D8A; margin-top:.2rem; line-height:1.4; }

.nx-dark { background:#161428; border-radius:22px; padding:2.2rem; color:#fff; box-shadow:0 20px 48px rgba(20,20,43,.24); }
.nx-dark h2 { color:#fff; font-size:1.85rem; font-weight:800; margin:0 0 .6rem; }
.nx-dark p { color:#A9A5C4; font-size:.95rem; line-height:1.6; margin:0; }
.nx-pipe { display:flex; align-items:center; gap:.5rem; flex-wrap:wrap; margin-top:1.5rem; }
.nx-pipe .nx-node { background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.14); border-radius:11px; padding:.6rem .9rem; font-size:.82rem; font-weight:600; color:#fff; }
.nx-pipe .nx-node.nx-hl { background:linear-gradient(135deg,#7C6FF0,#5B4FE9); border-color:transparent; box-shadow:0 6px 18px rgba(91,79,233,.4); }
.nx-pipe .nx-ar { color:#5A5680; font-weight:700; }

.nx-trust { display:flex; gap:.7rem; align-items:flex-start; padding:.75rem 0; border-bottom:1px solid #EFEDF9; }
.nx-trust:last-child { border-bottom:none; }
.nx-trust .nx-ck { flex:none; width:20px;height:20px;border-radius:50%;background:#E8F6EE;color:#2FA36B;display:grid;place-items:center;font-size:.7rem;font-weight:800;margin-top:.1rem; }
.nx-trust b { font-size:.9rem; color:#14142B; } .nx-trust span { font-size:.87rem; color:#6E6D8A; }

.nx-finalcta { background:linear-gradient(135deg,#6B5CF0,#5B4FE9); border-radius:22px; padding:3rem 2rem; text-align:center; color:#fff; box-shadow:0 20px 46px rgba(91,79,233,.34); }
.nx-finalcta h2 { color:#fff; font-size:2rem; font-weight:800; margin:0 0 .55rem; }
.nx-finalcta p { color:rgba(255,255,255,.86); font-size:1rem; margin:0; }
.nx-foot { text-align:center; color:#8B89A6; font-size:.83rem; padding:2.4rem 0 .8rem; line-height:1.7; }

/* Dashboard chrome */
.nx-kpi { background:#fff; border:1px solid #E7E5F5; border-radius:18px; padding:1.25rem; box-shadow:0 1px 2px rgba(20,20,43,.04); height:100%; }
.nx-kpi .nx-kl { font-size:.78rem; color:#6E6D8A; font-weight:600; display:flex; align-items:center; gap:.4rem; }
.nx-kpi .nx-kv { font-size:1.85rem; font-weight:800; letter-spacing:-.03em; margin:.45rem 0 .3rem; color:#14142B; }
.nx-kpi .nx-kd { font-size:.79rem; font-weight:700; display:inline-flex; align-items:center; gap:.25rem; padding:.16rem .5rem; border-radius:999px; }
.nx-kpi .nx-kd.nx-up { background:#E8F6EE; } .nx-kpi .nx-kd.nx-down { background:#FDECEC; }
.nx-kpi .nx-kn { font-size:.75rem; color:#8B89A6; margin-top:.5rem; }

.nx-fcard { background:#fff; border:1px solid #E7E5F5; border-left:4px solid var(--sev); border-radius:16px; padding:1.3rem 1.4rem; margin-bottom:1rem; box-shadow:0 1px 2px rgba(20,20,43,.04); }
.nx-fhead { display:flex; align-items:center; gap:.6rem; flex-wrap:wrap; margin-bottom:.6rem; }
.nx-fhead .nx-ft { font-size:1.06rem; font-weight:800; color:#14142B; }
.nx-badge { font-size:.68rem; font-weight:800; letter-spacing:.05em; padding:.2rem .55rem; border-radius:999px; background:var(--sevbg); color:var(--sev); }
.nx-chip { font-size:.7rem; font-weight:600; color:#6E6D8A; background:#F3F2FA; border-radius:999px; padding:.2rem .55rem; }
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Inline SVG illustration (generated here; no external or licensed assets)
# ---------------------------------------------------------------------------

def _hero_svg() -> str:
    """Abstract 'data becoming structure' illustration: translucent glass
    panels floating above a glass platter holding gradient columns. Built from
    plain SVG gradients/filters so it scales, themes cleanly and costs nothing.
    """
    return """
<svg viewBox="0 0 520 420" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Illustration: translucent data panels above a set of gradient columns">
  <defs>
    <linearGradient id="gGlass" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity=".92"/>
      <stop offset="100%" stop-color="#DAD5FA" stop-opacity=".55"/>
    </linearGradient>
    <linearGradient id="gPurple" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#8B7CF6"/><stop offset="100%" stop-color="#5B4FE9"/>
    </linearGradient>
    <linearGradient id="gTeal" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#7FE3DA"/><stop offset="100%" stop-color="#3FBFB3"/>
    </linearGradient>
    <linearGradient id="gLilac" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#CFC8FB"/><stop offset="100%" stop-color="#A99EF3"/>
    </linearGradient>
    <linearGradient id="gPlate" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity=".95"/>
      <stop offset="100%" stop-color="#C9C2F7" stop-opacity=".6"/>
    </linearGradient>
    <filter id="fSoft" x="-40%" y="-40%" width="180%" height="180%">
      <feDropShadow dx="0" dy="14" stdDeviation="18" flood-color="#5B4FE9" flood-opacity=".2"/>
    </filter>
    <filter id="fLight" x="-40%" y="-40%" width="180%" height="180%">
      <feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#5B4FE9" flood-opacity=".16"/>
    </filter>
  </defs>

  <ellipse cx="260" cy="330" rx="176" ry="30" fill="#5B4FE9" opacity=".10"/>

  <!-- columns: the deterministic layer -->
  <g filter="url(#fSoft)">
    <rect x="176" y="196" width="46" height="126" rx="23" fill="url(#gLilac)"/>
    <rect x="234" y="150" width="46" height="172" rx="23" fill="url(#gPurple)"/>
    <rect x="292" y="216" width="46" height="106" rx="23" fill="url(#gTeal)"/>
    <rect x="350" y="176" width="46" height="146" rx="23" fill="url(#gLilac)"/>
  </g>

  <!-- glass platter -->
  <g filter="url(#fLight)">
    <ellipse cx="286" cy="322" rx="150" ry="30" fill="url(#gPlate)" stroke="#FFFFFF" stroke-opacity=".9"/>
    <ellipse cx="286" cy="316" rx="150" ry="30" fill="#FFFFFF" opacity=".34"/>
  </g>

  <!-- floating glass panels: the evidence/insight layer -->
  <g filter="url(#fLight)">
    <rect x="60" y="96" width="96" height="96" rx="26" fill="url(#gGlass)" stroke="#FFFFFF"/>
    <rect x="84" y="124" width="26" height="26" rx="8" fill="#5B4FE9" opacity=".85"/>
    <rect x="112" y="146" width="22" height="22" rx="7" fill="#3FBFB3" opacity=".85"/>
  </g>
  <g filter="url(#fLight)">
    <rect x="330" y="42" width="86" height="86" rx="24" fill="url(#gGlass)" stroke="#FFFFFF"/>
    <path d="M350 96 L368 74 L384 88 L400 62" stroke="#5B4FE9" stroke-width="5"
          fill="none" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="400" cy="62" r="6" fill="#5B4FE9"/>
  </g>
  <g filter="url(#fLight)">
    <rect x="424" y="168" width="74" height="74" rx="22" fill="url(#gGlass)" stroke="#FFFFFF"/>
    <rect x="444" y="190" width="34" height="9" rx="4.5" fill="#8B7CF6"/>
    <rect x="444" y="206" width="24" height="9" rx="4.5" fill="#3FBFB3"/>
    <rect x="444" y="222" width="30" height="9" rx="4.5" fill="#CFC8FB"/>
  </g>
  <g filter="url(#fLight)">
    <rect x="150" y="24" width="66" height="66" rx="20" fill="url(#gGlass)" stroke="#FFFFFF"/>
    <circle cx="183" cy="57" r="17" fill="none" stroke="#5B4FE9" stroke-width="5"/>
    <path d="M183 40 A17 17 0 0 1 200 57 L183 57 Z" fill="#3FBFB3"/>
  </g>

  <circle cx="472" cy="112" r="9" fill="#8B7CF6" opacity=".55"/>
  <circle cx="40" cy="238" r="7" fill="#3FBFB3" opacity=".5"/>
  <circle cx="252" cy="34" r="5" fill="#5B4FE9" opacity=".4"/>
</svg>
"""


def _icon(path: str, color: str = ACCENT) -> str:
    return (f'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{path}</svg>')


_ICONS = {
    "see": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
    "explain": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "act": '<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>',
    "trust": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    "chart": '<path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/>',
    "layers": '<path d="m12 2 9 5-9 5-9-5 9-5z"/><path d="m3 17 9 5 9-5"/><path d="m3 12 9 5 9-5"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/>',
    "box": '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>',
    "truck": '<path d="M14 18V6a2 2 0 0 0-2-2H3v13"/><path d="M14 9h4l3 3v6h-2"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
}


def render_landing(kpi_preview: dict | None = None) -> str | None:
    """Marketing landing page. Returns 'demo', 'upload', or None.

    `kpi_preview` should carry REAL figures from the demo workspace so the hero
    stat strip shows the product's actual computed output rather than invented
    marketing numbers.
    """
    _html(
        f"""
        <div class="nx-nav">
          <div class="nx-brand"><div class="nx-logo">N</div> NexaSphere</div>
          <div class="nx-navlinks">
            <span>Product</span><span>How it works</span><span>AI &amp; Trust</span><span>Business value</span>
          </div>
          <div class="nx-navcta">BuildFest 2026</div>
        </div>

        <div class="nx-hero">
          <div>
            <div class="nx-eyebrow"><span class="nx-dot"></span> Evidence-backed business intelligence</div>
            <h1>Turn business data<br/>into decisions.</h1>
            <p class="nx-lede">
              Upload the files you already use. NexaSphere works out what your data can
              reliably answer, calculates the numbers itself, and explains what they mean
              in plain language &mdash; without letting AI invent a single figure.
            </p>
          </div>
          <div>{_hero_svg()}</div>
        </div>
        """)

    c1, c2, _ = st.columns([1.05, 1, 1.6])
    go_upload = c1.button("Analyze My Business", type="primary", use_container_width=True)
    go_demo = c2.button("Explore Demo", use_container_width=True)

    if kpi_preview:
        def _delta(v: float | None) -> str:
            if v is None:
                return ""
            cls = "nx-up" if v >= 0 else "nx-down"
            return f'<div class="nx-d {cls}">{"▲" if v >= 0 else "▼"} {abs(v):.1f}%</div>'

        _html(
            f"""
            <div class="nx-statrow">
              <div class="nx-stat"><div class="nx-k">Revenue analysed</div>
                <div class="nx-v">{kpi_preview['revenue']}</div>{_delta(kpi_preview.get('revenue_pct'))}</div>
              <div class="nx-stat"><div class="nx-k">Gross profit</div>
                <div class="nx-v">{kpi_preview['profit']}</div>{_delta(kpi_preview.get('profit_pct'))}</div>
              <div class="nx-stat"><div class="nx-k">Gross margin</div>
                <div class="nx-v">{kpi_preview['margin']}</div>
                <div class="nx-d nx-down">▼ {kpi_preview['margin_pp']} pp</div></div>
              <div class="nx-stat"><div class="nx-k">Orders</div>
                <div class="nx-v">{kpi_preview['orders']}</div>
                <div class="nx-kn" style="font-size:.75rem;color:#8B89A6;">Live from the demo workspace</div></div>
            </div>
            <p style="color:#8B89A6;font-size:.8rem;margin:.55rem 0 0;">
              Real figures, computed by the analytics engine from the demo dataset &mdash;
              not illustrative placeholders.</p>
            """)

    _html(
        f"""
        <div class="nx-sectionhead">
          <div class="nx-tag">Why it's different</div>
          <h2>See. Explain. Act. Trust.</h2>
          <p>Traditional dashboards tell you what happened. NexaSphere helps you understand
             why it matters and what to investigate next.</p>
        </div>
        <div class="nx-grid">
          <div class="nx-card"><div class="nx-ico">{_icon(_ICONS['see'])}</div>
            <h4>See</h4><p>KPIs and trends computed directly from your own data, never estimated.</p></div>
          <div class="nx-card"><div class="nx-ico">{_icon(_ICONS['explain'])}</div>
            <h4>Explain</h4><p>Ask questions in plain language &mdash; formal, casual, or Pidgin.</p></div>
          <div class="nx-card"><div class="nx-ico">{_icon(_ICONS['act'])}</div>
            <h4>Act</h4><p>Every finding carries an evidence trail and a recommended next step.</p></div>
          <div class="nx-card"><div class="nx-ico">{_icon(_ICONS['trust'])}</div>
            <h4>Trust</h4><p>The AI explains verified numbers. It is never the source of them.</p></div>
        </div>

        <div class="nx-sectionhead">
          <div class="nx-tag">How it works</div>
          <h2>From raw files to a decision</h2>
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

    _html("<div style='height:3.4rem'></div>")
    _html(
        """
        <div class="nx-dark">
          <h2>AI explains the numbers. It doesn't make them up.</h2>
          <p>Most "chat with your data" tools let a language model read your spreadsheet and
             produce figures. NexaSphere doesn't. Calculations run first, in pandas. The AI
             receives only the verified result, and any sentence containing a number that
             isn't in that evidence is rejected before you ever see it.</p>
          <div class="nx-pipe">
            <div class="nx-node">Your data</div><div class="nx-ar">→</div>
            <div class="nx-node">Verified calculations</div><div class="nx-ar">→</div>
            <div class="nx-node">Business evidence</div><div class="nx-ar">→</div>
            <div class="nx-node nx-hl">AI explanation</div><div class="nx-ar">→</div>
            <div class="nx-node">Recommendation</div>
          </div>
        </div>
        """)

    _html(
        f"""
        <div class="nx-sectionhead">
          <div class="nx-tag">Capabilities</div>
          <h2>What NexaSphere can analyse</h2>
          <p>Availability depends on what your uploaded data actually contains &mdash;
             NexaSphere tells you which of these it can support, and which it can't.</p>
        </div>
        <div class="nx-grid">
          <div class="nx-card"><div class="nx-ico">{_icon(_ICONS['chart'])}</div>
            <h4>Revenue &amp; profitability</h4><p>Spot when growth stops translating into margin.</p></div>
          <div class="nx-card"><div class="nx-ico">{_icon(_ICONS['layers'])}</div>
            <h4>Product performance</h4><p>Which lines carry the business, and which drag on it.</p></div>
          <div class="nx-card"><div class="nx-ico">{_icon(_ICONS['users'])}</div>
            <h4>Customer value</h4><p>Which segments and accounts actually drive revenue.</p></div>
          <div class="nx-card"><div class="nx-ico">{_icon(_ICONS['box'])}</div>
            <h4>Inventory position</h4><p>Where stock runs out, and where it sits idle.</p></div>
          <div class="nx-card"><div class="nx-ico">{_icon(_ICONS['truck'])}</div>
            <h4>Delivery performance</h4><p>Which partners are creating service risk.</p></div>
          <div class="nx-card"><div class="nx-ico">{_icon(_ICONS['target'])}</div>
            <h4>Targets &amp; marketing ROI</h4><p>Where attainment slips and which spend pays back.</p></div>
        </div>

        <div class="nx-sectionhead">
          <div class="nx-tag">Trust</div>
          <h2>Your data. Your analysis.</h2>
        </div>
        <div style="background:#fff;border:1px solid #E7E5F5;border-radius:18px;padding:.6rem 1.4rem;">
          <div class="nx-trust"><div class="nx-ck">✓</div><div>
            <b>Verified calculations.</b> <span>Every KPI is real pandas arithmetic, not a model's guess.</span></div></div>
          <div class="nx-trust"><div class="nx-ck">✓</div><div>
            <b>Your files stay out of the prompt.</b> <span>The AI receives aggregated evidence, never your raw dataset.</span></div></div>
          <div class="nx-trust"><div class="nx-ck">✓</div><div>
            <b>Session-scoped.</b> <span>Uploads are analysed in your session and are not permanently stored.</span></div></div>
          <div class="nx-trust"><div class="nx-ck">✓</div><div>
            <b>Honest limits.</b> <span>If your data can't answer something, NexaSphere says so instead of inventing an answer.</span></div></div>
          <div class="nx-trust"><div class="nx-ck">✓</div><div>
            <b>You decide.</b> <span>NexaSphere surfaces what to investigate. It never acts on your business by itself.</span></div></div>
        </div>
        """)

    _html("<div style='height:3.4rem'></div>")
    _html(
        """
        <div class="nx-finalcta">
          <h2>Your data already knows more than you think.</h2>
          <p>Bring the files you already have. Find out what they can tell you.</p>
        </div>
        """)
    _html("<div style='height:1rem'></div>")
    c3, c4, _ = st.columns([1.05, 1, 1.6])
    go_upload_2 = c3.button("Analyze My Business", key="cta2_upload", type="primary", use_container_width=True)
    go_demo_2 = c4.button("Explore Demo", key="cta2_demo", use_container_width=True)

    _html(
        """
        <div class="nx-foot">
          <b style="color:#14142B;">NexaSphere</b> &middot; AI Business Intelligence Assistant &middot; BuildFest 2026<br/>
          The data calculates. The AI explains. The evidence builds trust. The human decides.
        </div>
        """)

    if go_demo or go_demo_2:
        return "demo"
    if go_upload or go_upload_2:
        return "upload"
    return None


# ---------------------------------------------------------------------------
# Dashboard chrome
# ---------------------------------------------------------------------------

def app_header(title: str, subtitle: str, workspace: str) -> None:
    _html(
        f"""
        <div class="nx-nav">
          <div class="nx-brand"><div class="nx-logo">N</div> NexaSphere</div>
          <div class="nx-navlinks"><span style="color:#5B4FE9;font-weight:700;">Workspace:</span>
            <span style="color:#14142B;font-weight:600;">{workspace}</span></div>
          <div class="nx-navcta">BuildFest 2026</div>
        </div>
        <h1 style="font-size:2.1rem;font-weight:800;margin:0 0 .3rem;">{title}</h1>
        <p style="color:#6E6D8A;font-size:.97rem;margin:0 0 1.5rem;">{subtitle}</p>
        """)


def kpi_card(label: str, value: str, delta: str | None = None,
             positive: bool | None = None, note: str = "") -> str:
    delta_html = ""
    if delta:
        cls = "nx-up" if positive else "nx-down"
        arrow = "▲" if positive else "▼"
        delta_html = f'<div class="nx-kd {cls}"><span>{arrow}</span>{delta}</div>'
    note_html = f'<div class="nx-kn">{note}</div>' if note else ""
    return (f'<div class="nx-kpi"><div class="nx-kl">{label}</div>'
            f'<div class="nx-kv">{value}</div>{delta_html}{note_html}</div>')


def finding_header(title: str, severity: str, category: str, confidence: str | None = None) -> str:
    color = SEVERITY_COLOR.get(severity, ACCENT)
    bg = SEVERITY_BG.get(severity, ACCENT_SOFT)
    conf = f'<span class="nx-chip">confidence: {confidence.upper()}</span>' if confidence else ""
    return (
        f'<div style="--sev:{color};--sevbg:{bg};">'
        f'<div class="nx-fhead"><span class="nx-ft">{title}</span>'
        f'<span class="nx-badge" style="--sev:{color};--sevbg:{bg};">{severity.upper()}</span>'
        f'<span class="nx-chip">{category}</span>{conf}</div></div>'
    )


def plotly_theme(fig, height: int = 320):
    """Applies the NexaSphere chart style to a Plotly figure."""
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, sans-serif", size=12, color=MUTED),
        title=dict(font=dict(size=15, color=INK, weight=700), x=0, xanchor="left"),
        margin=dict(l=8, r=8, t=46, b=8),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                     bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        colorway=[ACCENT, "#3FBFB3", "#A99EF3", "#E8A33D", "#E5484D", "#2FA36B"],
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor=BORDER, tickfont=dict(size=11))
    fig.update_yaxes(showgrid=True, gridcolor="#F0EEFA", zeroline=False, tickfont=dict(size=11))
    return fig
