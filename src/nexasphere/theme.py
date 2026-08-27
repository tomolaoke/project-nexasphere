"""Visual design system + landing page for NexaSphere.

Streamlit is a server-rendered Python framework, not a bespoke HTML/CSS/JS
stack (see docs/UI_UX_AUDIT.md section 8) -- so "premium SaaS redesign" here
means: a real typography + color system injected once via CSS, restrained
styling of Streamlit's own components (metrics, tabs, containers, buttons),
and a custom-HTML landing page shown before the dashboard. None of this
touches nexasphere.analytics / insights / nlg / user_data -- it is presentation
only, layered on top of the untouched deterministic pipeline.

Everything here is $0: one Google Fonts import (free, no key required) and
plain CSS. No new Python dependencies.
"""
from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --nx-bg: #0b0e14;
    --nx-surface: #12161f;
    --nx-surface-raised: #171c27;
    --nx-border: #232a38;
    --nx-text: #e8eaf0;
    --nx-muted: #93a0b4;
    --nx-accent: #5b8def;
    --nx-accent-soft: rgba(91, 141, 239, 0.12);
    --nx-critical: #e5484d;
    --nx-warning: #e0a72e;
    --nx-watch: #5b8def;
    --nx-info: #3aa66b;
    --nx-radius: 10px;
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Restrained metric cards */
[data-testid="stMetric"] {
    background: var(--nx-surface);
    border: 1px solid var(--nx-border);
    border-radius: var(--nx-radius);
    padding: 1rem 1.1rem;
}
[data-testid="stMetricLabel"] { color: var(--nx-muted); font-weight: 500; }
[data-testid="stMetricValue"] { font-weight: 700; }

/* Tabs: quieter, more deliberate */
button[data-baseweb="tab"] { font-weight: 600; }
div[data-baseweb="tab-highlight"] { background-color: var(--nx-accent) !important; }

/* Containers used for finding/insight cards */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: var(--nx-radius) !important;
    border-color: var(--nx-border) !important;
}

/* Buttons: single accent, no gradient */
.stButton > button[kind="primary"] {
    background-color: var(--nx-accent);
    border: none;
    font-weight: 600;
}

/* Landing page building blocks (rendered via st.markdown unsafe_allow_html) */
.nx-landing { max-width: 1040px; margin: 0 auto; padding: 0 0.5rem; }
.nx-nav {
    display: flex; justify-content: space-between; align-items: center;
    padding: 1rem 0; border-bottom: 1px solid var(--nx-border); margin-bottom: 2.5rem;
}
.nx-wordmark { font-weight: 800; font-size: 1.15rem; letter-spacing: -0.02em; color: var(--nx-text); }
.nx-nav-links { color: var(--nx-muted); font-size: 0.9rem; }
.nx-nav-links span { margin-right: 1.5rem; }

.nx-hero { text-align: left; padding: 1.5rem 0 2.5rem; }
.nx-hero h1 {
    font-size: 2.6rem; font-weight: 800; letter-spacing: -0.03em; line-height: 1.12;
    margin-bottom: 1rem; color: var(--nx-text);
}
.nx-hero p.nx-sub { font-size: 1.1rem; color: var(--nx-muted); max-width: 640px; line-height: 1.6; }

.nx-pill {
    display: inline-block; background: var(--nx-accent-soft); color: var(--nx-accent);
    border-radius: 999px; padding: 0.3rem 0.8rem; font-size: 0.8rem; font-weight: 600;
    margin-bottom: 1rem;
}

.nx-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1rem; margin: 1.5rem 0; }
.nx-card {
    background: var(--nx-surface); border: 1px solid var(--nx-border); border-radius: var(--nx-radius);
    padding: 1.25rem; text-align: left;
}
.nx-card h4 { margin: 0 0 0.4rem; font-size: 1rem; color: var(--nx-text); }
.nx-card p { margin: 0; font-size: 0.88rem; color: var(--nx-muted); line-height: 1.5; }

.nx-flow {
    display: flex; align-items: center; justify-content: center; flex-wrap: wrap;
    gap: 0.6rem; margin: 1.5rem 0; font-size: 0.9rem; font-weight: 600;
}
.nx-flow .nx-step {
    background: var(--nx-surface-raised); border: 1px solid var(--nx-border); border-radius: 999px;
    padding: 0.5rem 1.1rem; color: var(--nx-text);
}
.nx-flow .nx-arrow { color: var(--nx-muted); }

.nx-section-title { font-size: 1.5rem; font-weight: 700; margin: 2.5rem 0 0.5rem; color: var(--nx-text); }
.nx-section-sub { color: var(--nx-muted); font-size: 0.95rem; margin-bottom: 1rem; max-width: 680px; }

.nx-trust-line { display: flex; gap: 0.6rem; align-items: flex-start; margin-bottom: 0.8rem; }
.nx-trust-line .nx-check { color: var(--nx-info); font-weight: 700; }
.nx-trust-line span.nx-t { color: var(--nx-muted); font-size: 0.92rem; }

.nx-final-cta { text-align: center; padding: 3rem 0 2rem; border-top: 1px solid var(--nx-border); margin-top: 3rem; }
.nx-final-cta h2 { font-size: 1.8rem; font-weight: 800; color: var(--nx-text); margin-bottom: 0.5rem; }

.nx-footer { text-align: center; color: var(--nx-muted); font-size: 0.82rem; padding: 2rem 0 1rem; }
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


SEVERITY_COLOR = {"critical": "#e5484d", "warning": "#e0a72e", "watch": "#5b8def", "info": "#3aa66b"}


def render_landing() -> str | None:
    """Renders the marketing landing page. Returns 'demo', 'upload', or None
    (still on landing) depending on which CTA was clicked.
    """
    st.markdown('<div class="nx-landing">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="nx-nav">
            <div class="nx-wordmark">NexaSphere</div>
            <div class="nx-nav-links">
                <span>Product</span><span>How it works</span><span>AI &amp; Trust</span><span>Business Value</span>
            </div>
        </div>
        <div class="nx-hero">
            <div class="nx-pill">AI Business Intelligence · BuildFest 2026</div>
            <h1>Turn business data<br/>into decisions.</h1>
            <p class="nx-sub">
                Understand what happened, why it matters, and what to investigate next —
                using evidence-backed AI. Your analytics engine calculates the truth;
                NexaSphere's AI explains it in plain English, and never invents a number.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1, 1, 2])
    demo_clicked = c1.button("Explore NexaSphere Demo", type="primary", use_container_width=True)
    upload_clicked = c2.button("Analyze My Business", use_container_width=True)

    st.markdown('<div class="nx-section-title">See. Explain. Act. Trust.</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="nx-grid">
            <div class="nx-card"><h4>SEE</h4><p>Understand performance with KPIs and trends computed directly from your data.</p></div>
            <div class="nx-card"><h4>EXPLAIN</h4><p>Ask business questions in plain English and get answers grounded in real numbers.</p></div>
            <div class="nx-card"><h4>ACT</h4><p>Every finding comes with an evidence-backed recommendation, not a guess.</p></div>
            <div class="nx-card"><h4>TRUST</h4><p>AI explains verified metrics instead of inventing them — every number is traceable.</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="nx-section-title">How it works</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="nx-flow">
            <div class="nx-step">Upload Data</div><div class="nx-arrow">→</div>
            <div class="nx-step">NexaSphere Analyzes</div><div class="nx-arrow">→</div>
            <div class="nx-step">Ask Questions</div><div class="nx-arrow">→</div>
            <div class="nx-step">Discover Insights</div><div class="nx-arrow">→</div>
            <div class="nx-step">Take Action</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="nx-section-title">AI explains the numbers. It doesn\'t make them up.</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="nx-section-sub">Traditional dashboards tell you what happened. NexaSphere helps you understand '
        'why it matters and what to investigate next — without letting AI invent the numbers.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="nx-flow">
            <div class="nx-step">Business Data</div><div class="nx-arrow">→</div>
            <div class="nx-step">Deterministic Analytics</div><div class="nx-arrow">→</div>
            <div class="nx-step">Verified Evidence</div><div class="nx-arrow">→</div>
            <div class="nx-step">AI Explanation</div><div class="nx-arrow">→</div>
            <div class="nx-step">Recommendation</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="nx-section-title">What NexaSphere analyzes</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="nx-grid">
            <div class="nx-card"><h4>AI Business Q&amp;A</h4><p>Plain-English answers to profitability, returns, ROI and more.</p></div>
            <div class="nx-card"><h4>Revenue &amp; Profitability</h4><p>Spot when growth isn't translating into margin.</p></div>
            <div class="nx-card"><h4>Inventory Intelligence</h4><p>Stockouts and excess stock, by category and store.</p></div>
            <div class="nx-card"><h4>Delivery Performance</h4><p>Which partners are creating service risk.</p></div>
            <div class="nx-card"><h4>Customer Segmentation</h4><p>Which segments actually drive value.</p></div>
            <div class="nx-card"><h4>Evidence-backed Recommendations</h4><p>Every suggestion traces back to a real number.</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="nx-section-title">Bring your own business data</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="nx-section-sub">Upload your business dataset and let NexaSphere turn your raw data into '
        'understandable insights. NexaSphere automatically identifies what your data can reliably answer — '
        'it never fabricates an analysis your data doesn\'t support.</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="nx-section-title">Trust, by design</div>', unsafe_allow_html=True)
    for line in (
        "Deterministic calculations — every KPI is a real pandas computation, not a model guess.",
        "Evidence-backed AI — the AI only ever explains numbers it was given, never numbers it invented.",
        "Transparent recommendations — every suggestion cites the evidence behind it.",
        "Human decision-making stays in control — NexaSphere surfaces what to investigate, not autonomous actions.",
    ):
        st.markdown(
            f'<div class="nx-trust-line"><span class="nx-check">✓</span><span class="nx-t">{line}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="nx-final-cta">
            <h2>Your data already knows more about your business than you think.</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c4, c5, _ = st.columns([1, 1, 2])
    demo_clicked_2 = c4.button("Analyze My Business", key="final_cta_upload", type="primary", use_container_width=True)
    explore_clicked_2 = c5.button("Explore Demo", key="final_cta_demo", use_container_width=True)

    st.markdown(
        """
        <div class="nx-footer">
            NexaSphere · AI Business Intelligence Assistant · BuildFest 2026<br/>
            The data calculates. The AI explains. The evidence builds trust. The human decides.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if demo_clicked or explore_clicked_2:
        return "demo"
    if upload_clicked or demo_clicked_2:
        return "upload"
    return None
