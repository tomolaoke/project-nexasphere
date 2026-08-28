"""NexaSphere AI Business Intelligence Assistant -- Streamlit prototype.

Every number on this page is produced by nexasphere.analytics /
nexasphere.insights (deterministic pandas computation). The optional local
LLM (Ollama) is only ever used to rephrase those numbers in plain English --
see nexasphere.nlg for the enforcement mechanism.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import os

# Streamlit Cloud has no local Ollama to reach, so the free-tier Groq API is
# the "online" AI backend. The key is read from Streamlit secrets (never
# committed to the repo) and exported as an env var before importing nlg,
# since nlg intentionally has no Streamlit/UI dependency of its own.
try:
    if st.secrets.get("GROQ_API_KEY"):
        os.environ.setdefault("GROQ_API_KEY", st.secrets["GROQ_API_KEY"])
except Exception:
    pass  # no secrets.toml (e.g. local run) -- fine, nlg falls back to Ollama/template

from nexasphere import analytics as an
from nexasphere import ingestion as ing
from nexasphere import insights as ins
from nexasphere import nlg
from nexasphere import qa
from nexasphere import theme
from nexasphere import user_data as ud

st.set_page_config(page_title="NexaSphere AI Business Intelligence Assistant", page_icon="\U0001F4CA", layout="wide")

SEVERITY_COLOR = {"critical": "#d64545", "warning": "#e0a72e", "watch": "#3d7dd6", "info": "#3aa66b"}
SEVERITY_ICON = {"critical": "\U0001F534", "warning": "\U0001F7E0", "watch": "\U0001F535", "info": "\U0001F7E2"}


@st.cache_data(show_spinner=False)
def _cached_findings(window_days: int):
    findings = ins.generate_findings(window_days)
    return [f.as_dict() for f in findings]


@st.cache_data(show_spinner=False, ttl=60)
def _cached_narrate_finding(finding_dict: dict):
    """Wraps nlg.narrate_finding so every Streamlit rerun doesn't re-trigger
    an LLM call for all six findings. Without this, typing in the unrelated
    Ask tab, or expanding any panel, silently re-ran narration for every
    finding on every keystroke -- a real demo-responsiveness problem when
    Ollama is actually running (each call can take seconds).
    """
    finding = ins.Finding(**{k: finding_dict[k] for k in
                              ("id", "title", "category", "severity", "summary", "evidence", "recommendation")})
    result = nlg.narrate_finding(finding)
    return result.text, result.source, result.backend, result.model, result.verified


@st.cache_data(show_spinner=False, ttl=60)
def _cached_narrate_generic(summary: str, evidence_json: str, recommendation: str):
    """Same caching rationale as _cached_narrate_finding, generalized to any
    (summary, evidence, recommendation) triple -- used for user-uploaded-data
    findings, which aren't nexasphere.insights.Finding instances.
    """
    class _NarratableEvidence:
        pass
    obj = _NarratableEvidence()
    obj.summary = summary
    obj.evidence = json.loads(evidence_json)
    obj.recommendation = recommendation
    result = nlg.narrate_finding(obj)
    return result.text, result.source, result.backend, result.model, result.verified


def _llm_status_badge():
    backend, model = nlg.ai_backend_status()
    if backend == "ollama":
        st.sidebar.success(f"AI connected (local Ollama · {model})")
    elif backend == "groq":
        st.sidebar.success(f"AI connected (free hosted Groq · {model})")
    else:
        st.sidebar.info(
            "No AI narration backend configured. Running on the deterministic "
            "template narrator -- every number below is still fully computed, "
            "just not rephrased by a model. Set a free GROQ_API_KEY in "
            "Streamlit secrets (or run Ollama locally) to enable AI narration, "
            "100% free either way."
        )


def business_name() -> str:
    return st.session_state.get("ud_biz_name", "").strip() or "My Business"


def is_business_workspace() -> bool:
    return st.session_state.get("nx_workspace") == "business"


def user_frame():
    """(canonical_frame, capabilities) for the active business workspace, or
    (None, None) if the user hasn't confirmed a mapping yet.
    """
    if not st.session_state.get("ud_confirmed") or "ud_raw_df" not in st.session_state:
        return None, None
    cdf = ud.build_canonical_frame(st.session_state["ud_raw_df"], st.session_state["ud_mapping"])
    return cdf, ud.capability_matrix(set(cdf.columns))


def render_sidebar():
    business = is_business_workspace()
    st.sidebar.title(business_name() if business else "NexaSphere")
    st.sidebar.caption(
        f"{st.session_state.get('ud_biz_industry', '').strip() or 'Your business'} · "
        "analyzed by NexaSphere" if business
        else "AI Business Intelligence Assistant · BuildFest 2026"
    )
    _llm_status_badge()
    st.sidebar.markdown("---")

    if business:
        cdf, _caps = user_frame()
        # The dataset window must describe THEIR data. Showing the demo
        # dataset's dates here would describe a different business entirely.
        # "Not analyzed yet" and "analyzed, but no date column" are genuinely
        # different states and must not share one message -- conflating them
        # made a pre-analysis workspace look like a mapping failure.
        if cdf is None:
            st.sidebar.markdown(
                "**Your data window**\n\nNot analyzed yet — upload your files and "
                "confirm the column mapping.")
        else:
            window = ud.dataset_window(cdf)
            if window:
                st.sidebar.markdown(
                    f"**Your data window**\n\n{window[0].date()} → {window[1].date()}")
            else:
                st.sidebar.markdown(
                    "**Your data window**\n\nNo date column mapped — trend and growth "
                    "analysis is unavailable until one is.")
            st.sidebar.markdown(f"**Records analyzed**\n\n{len(cdf):,}")
        if st.session_state.get("ud_filename"):
            st.sidebar.markdown(f"**Source file**\n\n{st.session_state['ud_filename']}")
        st.sidebar.markdown("---")
        if st.sidebar.button("← Back to NexaSphere demo", use_container_width=True):
            st.session_state["nx_workspace"] = "demo"
            # Staged rather than assigned, for the same reason as the confirm
            # handler: the nav radio owns this key. Safe here today only
            # because the sidebar renders first, which is too fragile to rely on.
            st.session_state["nx_pending_page"] = "Overview"
            st.rerun()
    else:
        start, end = an.dataset_date_range()
        st.sidebar.markdown(f"**Dataset window**\n\n{start.date()} → {end.date()}")
        st.sidebar.caption("NexaSphere Retail Ltd. — the BuildFest demo dataset.")

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "All KPIs are computed by a deterministic analytics engine. "
        "The AI layer only explains verified numbers -- it never invents them."
    )
    if business:
        st.sidebar.caption(
            "🔒 Your data is analyzed in this session only and is not stored."
        )


@st.cache_data(show_spinner=False)
def _landing_kpi_preview():
    """Real computed figures for the landing hero strip. Using actual analytics
    output (rather than invented marketing numbers) is the point: the landing
    page shows the product's real output.
    """
    comp = an.revenue_profit_growth_gap(30)
    latest, change = comp["latest_period"], comp["change"]
    return {
        "revenue": f"{latest['revenue']:,.0f}",
        "revenue_pct": change["revenue_pct"],
        "profit": f"{latest['gross_profit']:,.0f}",
        "profit_pct": change["gross_profit_pct"],
        "margin": f"{latest['margin_pct']:.2f}%",
        "margin_pp": f"{abs(change['margin_pp']):.2f}",
        "orders": f"{latest['orders']:,}",
    }


def render_kpi_row():
    comp = an.revenue_profit_growth_gap(30)
    latest = comp["latest_period"]
    change = comp["change"]

    # Real monthly series behind each sparkline -- the trend drawn is the
    # actual computed history, not a decorative squiggle.
    trend = an.monthly_revenue_trend()
    rev_series = trend["revenue"].tolist()
    profit_series = trend["gross_profit"].tolist()
    margin_series = trend["margin_pct"].tolist()
    order_series = trend["orders"].tolist()

    cards = [
        theme.kpi_card("Revenue", f"{latest['revenue']:,.0f}", f"{abs(change['revenue_pct']):.1f}%",
                        change["revenue_pct"] >= 0, "Last 30 days", "cash", rev_series),
        theme.kpi_card("Gross profit", f"{latest['gross_profit']:,.0f}", f"{abs(change['gross_profit_pct']):.1f}%",
                        change["gross_profit_pct"] >= 0, "Last 30 days", "chart", profit_series),
        theme.kpi_card("Gross margin", f"{latest['margin_pct']:.2f}%", f"{abs(change['margin_pp']):.2f} pp",
                        change["margin_pp"] >= 0, "vs. prior period", "percent", margin_series),
        theme.kpi_card("Orders", f"{latest['orders']:,}", f"{abs(change['orders_pct']):.1f}%",
                        change["orders_pct"] >= 0, "Last 30 days", "orders", order_series),
    ]
    for col, card in zip(st.columns(4), cards):
        col.markdown(card, unsafe_allow_html=True)

    if comp["margin_pressure"]:
        st.markdown(
            theme.alert(
                "warning", "Margin under pressure",
                f"Revenue grew {change['revenue_pct']:+.1f}% while gross profit grew only "
                f"{change['gross_profit_pct']:+.1f}% &mdash; margin moved {change['margin_pp']:+.2f} pp. "
                "Open <b>Findings</b> for the evidence trail.",
            ),
            unsafe_allow_html=True,
        )


def render_overview_highlights():
    """Top findings surfaced on Overview so the most important signals are
    visible without navigating away.
    """
    # Hero chart: the competition's core story (is growth reaching profit?)
    # belongs on the first screen, not buried a page away.
    trend = an.monthly_revenue_trend()
    left, right = st.columns([1.55, 1])
    with left:
        fig = px.area(trend, x="month", y=["revenue", "gross_profit"],
                       title="Revenue vs. Gross Profit", labels={"value": "", "month": ""})
        fig.update_traces(line=dict(width=2.5))
        st.plotly_chart(theme.plotly_theme(fig, 300), use_container_width=True)
    with right:
        cat = an.breakdown_by("category", top_n=6)
        fig2 = px.bar(cat, x="revenue", y="category", orientation="h",
                       title="Revenue by Category", labels={"revenue": "", "category": ""})
        fig2.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(theme.plotly_theme(fig2, 300), use_container_width=True)

    st.markdown("#### What needs your attention")
    findings = _cached_findings(30)[:3]
    for col, f in zip(st.columns(len(findings)), findings):
        color, bg = theme.severity_colors(f["severity"])
        with col:
            st.markdown(
                f'<div class="nx-card" style="border-left:4px solid {color};">'
                f'<span class="nx-badge" style="background:{bg};color:{color};">'
                f'{f["severity"].upper()}</span>'
                f'<h4 style="margin-top:.6rem;">{f["title"]}</h4>'
                f'<p>{f["summary"][:150]}…</p></div>',
                unsafe_allow_html=True,
            )
    st.caption("Full evidence and recommendations are on the **Findings** page.")


def render_findings_tab():
    st.caption(
        "Findings are generated by the insight engine from deterministic analytics "
        "output, ranked by severity. The narration is either produced by a local "
        "open-source LLM (if available) or a verified template -- both are "
        "grounded in the evidence shown below each card."
    )
    findings = _cached_findings(30)
    for f in findings:
        confidence = f.get("confidence", "medium")
        with st.container(border=True):
            st.markdown(
                theme.finding_header(f["title"], f["severity"], f["category"], confidence),
                unsafe_allow_html=True,
            )
            text, source, backend, model, _verified = _cached_narrate_finding(f)
            st.write(text)
            if source == "template":
                st.info("Verified analysis -- AI explanation unavailable or unverifiable right now; "
                        "the summary above is generated directly from the analytics engine, not a model.")
            else:
                label = "local Ollama" if backend == "ollama" else "free hosted Groq"
                st.caption(f"Narration source: AI ({label} · {model}), numerically verified")
            if f.get("possible_drivers"):
                st.markdown("**Possible drivers (not confirmed -- worth investigating):**")
                for d in f["possible_drivers"]:
                    st.markdown(f"- {d}")
            st.markdown(f"**Recommended focus:** {f['recommendation']}")
            with st.expander("Evidence (raw computed values)"):
                st.json(f["evidence"])


def render_ask_tab():
    st.caption(
        "Answers are calculated by the analytics engine first, then phrased by the AI layer. "
        "Ask formally or casually — including Nigerian English/Pidgin — or ask "
        "*\"What can I ask?\"* to see everything available."
    )

    def answer(question: str):
        result = qa.answer_question(question)
        caption = _source_caption(result.narration)
        caption += f"  ·  matched intent: `{result.intent}`"
        evidence = result.result if result.intent not in qa.DECLINED_INTENTS else None
        return result.narration.text, caption, evidence

    _render_chat("demo_chat", qa.SUGGESTED_QUESTIONS, answer,
                  "Ask about NexaSphere Retail's performance…")


def render_dashboard_tab():
    trend = an.monthly_revenue_trend()
    fig = px.line(trend, x="month", y=["revenue", "gross_profit"], markers=True,
                   labels={"value": "Amount", "month": "Month", "variable": "Metric"},
                   title="Monthly Revenue vs. Gross Profit")
    st.plotly_chart(theme.plotly_theme(fig), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        cat = an.breakdown_by("category")
        fig2 = px.bar(cat, x="category", y="revenue", color="margin_pct",
                       title="Revenue & Margin by Category")
        st.plotly_chart(theme.plotly_theme(fig2), use_container_width=True)
    with col2:
        region = an.breakdown_by("region")
        fig3 = px.pie(region, names="region", values="revenue", title="Revenue Share by Region")
        st.plotly_chart(theme.plotly_theme(fig3), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        returns = an.return_analysis()
        fig4 = px.bar(returns, x="category", y="return_rate_pct", title="Return Rate % by Category")
        st.plotly_chart(theme.plotly_theme(fig4), use_container_width=True)
    with col4:
        delivery = an.delivery_partner_performance()
        fig5 = px.bar(delivery, x="partner_name", y="delayed_rate_pct", title="Delayed Delivery Rate % by Partner")
        st.plotly_chart(theme.plotly_theme(fig5), use_container_width=True)

    col5, col6 = st.columns(2)
    with col5:
        emp = an.employee_store_performance()
        fig6 = px.bar(emp, x="store_name", y="revenue_per_employee", color="margin_pct",
                       title="Revenue per Employee by Store")
        st.plotly_chart(theme.plotly_theme(fig6), use_container_width=True)
        st.caption("Sales are recorded per store, not per individual employee -- this reflects "
                   "store-level team performance, not individual attribution.")
    with col6:
        seg = an.customer_segment_value()
        fig7 = px.bar(seg, x="customer_segment", y="revenue_per_customer", color="margin_pct",
                       title="Revenue per Customer by Segment")
        st.plotly_chart(theme.plotly_theme(fig7), use_container_width=True)

    st.markdown("#### Marketing Campaign ROI")
    st.dataframe(an.campaign_roi()[["campaign_name", "channel", "spend", "attributed_revenue", "roi"]], use_container_width=True)

    st.markdown("#### Target vs. Actual (latest month)")
    tva = an.target_vs_actual()
    st.dataframe(
        tva[["store_name", "region", "revenue_target", "actual_revenue", "revenue_attainment_pct",
             "on_time_gap_pp", "return_rate_gap_pp"]],
        use_container_width=True,
    )


def render_analyze_my_business_tab():
    st.caption(
        "Upload your own business dataset (CSV) and NexaSphere profiles it, detects "
        "what it can reliably analyze, and runs the same deterministic-analytics-first, "
        "AI-explains-the-evidence pipeline used for the demo dataset above -- on your data."
    )
    st.info(
        "🔒 **Privacy:** your uploaded file is analyzed only in this browser session and "
        "is never permanently stored, written to disk, or sent to any third-party service. "
        "The AI never sees your raw file -- only the verified numbers computed from it. "
        "Do not upload personally identifiable or confidential information unless you are "
        "authorized to do so."
    )

    uploaded = st.file_uploader(
        "Drop your business files here — select several at once, or a whole folder's contents",
        type=["csv", "tsv", "xlsx", "xls", "json", "pdf", "docx", "txt", "md",
               "png", "jpg", "jpeg", "webp", "mp4", "mov"],
        accept_multiple_files=True,
        key="ud_uploader",
    )
    st.caption(
        "**Analyzed:** CSV, TSV, XLSX, JSON — these produce your KPIs and findings.  \n"
        "**Read for context:** PDF, DOCX, TXT, MD — business notes and targets, never "
        "counted as measured figures.  \n"
        "**Not analyzed:** images and video — NexaSphere doesn't run OCR or video "
        "analysis, and won't guess at numbers it can't verify."
    )

    if uploaded:
        signature = tuple(sorted(f.name for f in uploaded))
        if st.session_state.get("ud_signature") != signature:
            with st.spinner("Reading your files..."):
                ingested = ing.ingest_files(uploaded)
            st.session_state["ud_ingested"] = ingested
            st.session_state["ud_signature"] = signature
            st.session_state["ud_confirmed"] = False
            # Drop the previous file's mapping selections. A Streamlit widget
            # with a key takes its value from session_state and IGNORES the
            # index argument, so a stale selection silently overrode the fresh
            # suggestion for the new file -- which is how a correctly detected
            # date column ended up reported as "not mapped".
            for k in [k for k in st.session_state if k.startswith("ud_map_")]:
                del st.session_state[k]

            primary = ing.choose_primary_frame(ingested)
            if primary is not None:
                df = primary.frame
                st.session_state["ud_raw_df"] = df
                st.session_state["ud_filename"] = primary.name
                profile = ud.profile_dataset(df)
                st.session_state["ud_mapping"] = ud.suggest_mapping(df, profile)
            else:
                st.session_state.pop("ud_raw_df", None)

    ingested = st.session_state.get("ud_ingested", [])
    if ingested:
        st.markdown(f"#### We found {len(ingested)} file(s)")
        st.dataframe(pd.DataFrame([f.summary_row() for f in ingested]), use_container_width=True)

        relationships = ing.detect_relationships(ingested)
        if relationships:
            st.markdown("**Possible relationships between your tables**")
            st.dataframe(pd.DataFrame(relationships), use_container_width=True)
            st.caption(
                "These tables share an identifier column, so they may be related. "
                "NexaSphere does not join them automatically — a coincidental shared "
                "column name would otherwise produce combined figures you never had."
            )

        context = ing.context_files(ingested)
        if context:
            with st.expander(f"Business context extracted from {len(context)} document(s)"):
                st.caption(
                    "This text is kept as background context only. It is never counted "
                    "as a measured business figure — a document saying \"our target is "
                    "10 million\" records a target, not revenue."
                )
                for f in context:
                    st.markdown(f"**{f.name}** — {f.detail}")
                    st.text(f.text[:1500] + ("…" if len(f.text) > 1500 else ""))

    if "ud_raw_df" not in st.session_state:
        if ingested:
            st.warning(
                "None of these files contain a table NexaSphere can compute on. "
                "Upload at least one CSV, TSV, XLSX or JSON file containing your "
                "business records to generate KPIs and findings."
            )
        else:
            st.markdown(
                "_No business data loaded yet. Upload your files above to analyze your own "
                "business, or explore the NexaSphere demo dataset using the tabs above._"
            )
        return

    if len(ing.data_files(ingested)) > 1:
        st.info(
            f"Analyzing **{st.session_state['ud_filename']}** — the largest table you "
            "uploaded. Other tables are listed above; NexaSphere analyses one table at a "
            "time rather than merging them on assumptions."
        )

    df = st.session_state["ud_raw_df"]
    profile = ud.profile_dataset(df)
    quality = ud.data_quality_score(profile)

    st.markdown(f"**{st.session_state['ud_filename']}** — {profile.n_rows:,} records across {profile.n_cols} columns.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Data quality score", f"{quality['score']}/100")
    c2.metric("Missing values (avg)", f"{quality['avg_missing_pct']:.1f}%")
    c3.metric("Duplicate rows", f"{quality['duplicate_pct']:.1f}%")
    for note in quality["notes"]:
        st.caption(f"• {note}")

    st.markdown("#### Confirm column mapping")
    st.caption(
        "NexaSphere guessed these mappings from your column names and types. Each dropdown "
        "only offers columns of the right kind -- dates for Date, numbers for Revenue, and "
        "so on. Correct anything that's wrong; nothing is analyzed until you confirm."
    )

    mapping = st.session_state["ud_mapping"]
    new_mapping = {}
    map_cols = st.columns(2)
    for i, concept in enumerate(ud.CANONICAL_FIELDS.keys()):
        # Only offer columns whose detected type suits this concept, so each
        # dropdown answers its own question instead of listing every column.
        options = ["(none)"] + ud.candidate_columns(concept, profile)
        current = mapping.get(concept)
        idx = options.index(current) if current in options else 0
        label = concept.replace("_", " ").capitalize()
        with map_cols[i % 2]:
            if len(options) == 1:
                st.selectbox(f"{label} — no suitable column found", options, index=0,
                              key=f"ud_map_{concept}", disabled=True,
                              help=ud.CONCEPT_HELP.get(concept))
                choice = "(none)"
            else:
                choice = st.selectbox(label, options, index=idx, key=f"ud_map_{concept}",
                                       help=ud.CONCEPT_HELP.get(concept))
        new_mapping[concept] = None if choice == "(none)" else choice
    st.session_state["ud_mapping"] = new_mapping

    if st.button("Confirm & Analyze", type="primary"):
        st.session_state["ud_confirmed"] = True
        # Everything from here on is that business's own workspace: switch the
        # whole app over so Overview / Findings / Ask / Dashboards all read
        # from their data instead of the demo dataset.
        st.session_state["nx_workspace"] = "business"
        # Requested navigation is staged, not assigned directly: the nav radio
        # owns the `nx_active_page` key and is instantiated earlier in the
        # run, so writing to it here raises StreamlitAPIException. main()
        # applies this before the widget is built.
        st.session_state["nx_pending_page"] = "Overview"
        st.rerun()

    if not st.session_state.get("ud_confirmed"):
        return

    cdf = ud.build_canonical_frame(df, st.session_state["ud_mapping"])
    caps = ud.capability_matrix(set(cdf.columns))

    st.markdown("---")
    st.markdown("#### What your data can answer")
    supported = [label for label, ok in caps.items() if ok]
    unsupported = [label for label, ok in caps.items() if not ok]
    st.markdown(f"Your dataset currently supports **{len(supported)} of {len(caps)}** analysis categories.")
    cap_a, cap_b = st.columns(2)
    with cap_a:
        st.markdown("**Detected:**")
        for label in supported:
            st.markdown(f"✓ {label}")
    with cap_b:
        st.markdown("**Not detected:**")
        for label in unsupported:
            st.markdown(f"○ {label}")

    if "revenue" not in cdf.columns:
        st.warning(
            "No revenue-like column is mapped -- most analyses need at least a revenue figure. "
            "Adjust the mapping above to unlock them."
        )
        return

    st.markdown("---")
    st.markdown("#### Overview")
    kpi = ud.kpi_summary(cdf)
    k1, k2, k3 = st.columns(3)
    k1.metric("Total revenue", f"{kpi.get('revenue', 0):,.2f}")
    if "profit" in kpi:
        k2.metric("Total profit", f"{kpi['profit']:,.2f}")
        k3.metric("Margin", f"{kpi.get('margin_pct', 0):.2f}%")
    else:
        k2.metric("Records", f"{kpi.get('records', 0):,}")

    findings = ud.generate_user_findings(cdf, caps)
    st.markdown("#### Findings")
    if findings:
        for f in findings:
            icon = SEVERITY_ICON.get(f.severity, "⚪")
            with st.container(border=True):
                st.markdown(f"### {icon} {f.title}  \n`{f.severity.upper()}` · {f.category}")
                text, source, backend, model, _verified = _cached_narrate_generic(
                    f.summary, json.dumps(f.evidence, default=str), f.recommendation
                )
                st.write(text)
                if source == "template":
                    st.info("Verified analysis -- AI explanation unavailable or unverifiable right now; "
                            "the summary above is generated directly from your data, not a model.")
                else:
                    label = "local Ollama" if backend == "ollama" else "free hosted Groq"
                    st.caption(f"Narration source: AI ({label} · {model}), numerically verified")
                st.markdown(f"**Recommended focus:** {f.recommendation}")
                with st.expander("Evidence (raw computed values)"):
                    st.json(f.evidence)
    else:
        st.info(
            "No findings yet -- your data may not support the pattern-detection checks "
            "(e.g. a date column is needed for growth-trend findings)."
        )

    st.markdown("#### Ask a question about your data")
    st.caption(
        "Ask in plain language — formal or casual, including Nigerian English/Pidgin. "
        "Not sure what's possible? Ask *\"What can I ask?\"* and NexaSphere will answer "
        "from the columns it actually detected in your files."
    )
    suggestions = [
        example
        for label, ok in caps.items() if ok
        for example in ud._CAPABILITY_QUESTIONS.get(label, [])
    ][:6]
    if suggestions:
        with st.expander("Suggested questions for your data"):
            for s in suggestions:
                st.markdown(f"- {s}")

    question = st.text_input(
        "Your question", key="ud_question", placeholder="e.g. Which product generates the most revenue?"
    )
    if st.button("Ask", key="ud_ask_btn") and question.strip():
        result = ud.answer_user_question(question, cdf, caps)
        if result.supported:
            narration = nlg.narrate_answer(question, result.result, result.template_answer)
            st.markdown(f"**Answer:** {narration.text}")
            if narration.source != "template":
                label = "local Ollama" if narration.backend == "ollama" else "free hosted Groq"
                st.caption(f"Narration source: AI ({label} · {narration.model}), numerically verified")
            with st.expander("Underlying computed result"):
                st.json(result.result)
        else:
            st.warning(result.template_answer)

    trend = ud.revenue_trend(cdf)
    dimension_charts = [d for d in ("product", "customer", "category", "region", "store", "campaign", "employee")
                         if d in cdf.columns]
    if not trend.empty or dimension_charts:
        st.markdown("#### Charts")
    if not trend.empty:
        y_cols = [c for c in ("revenue", "profit") if c in trend.columns]
        fig = px.line(trend, x="period", y=y_cols, markers=True, title="Revenue Over Time")
        st.plotly_chart(theme.plotly_theme(fig), use_container_width=True)
    for dim in dimension_charts:
        bdf = ud.breakdown_by(cdf, dim, top_n=10)
        if not bdf.empty:
            fig = px.bar(bdf, x=dim, y="revenue", title=f"Revenue by {dim.capitalize()}")
            st.plotly_chart(theme.plotly_theme(fig), use_container_width=True)


def render_business_setup() -> bool:
    """Required business details, collected before upload so the workspace can
    be titled and framed as theirs. Display-only: nothing here is persisted or
    sent anywhere, which is stated plainly rather than left ambiguous.

    Returns True once the required fields are filled.
    """
    if st.session_state.get("ud_setup_done"):
        return True

    theme.page_title(
        "Tell us about your business",
        "So your workspace is labelled with your name rather than a generic one.",
    )
    st.markdown(
        theme.alert(
            "info", "Display only",
            "These details are used to label this session's workspace. They are not "
            "saved, not sent anywhere, and disappear when you close the tab.",
        ),
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    with st.form("nx_business_setup"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Business name *", placeholder="e.g. Acme Retail Ltd.")
        industry = c2.text_input("Industry *", placeholder="e.g. Retail, Logistics, Hospitality")
        c3, c4 = st.columns(2)
        represents = c3.text_input("What does your data represent?",
                                    placeholder="e.g. Sales transactions")
        goal = c4.text_input("Primary goal", placeholder="e.g. Improve profitability")
        submitted = st.form_submit_button("Continue to upload", type="primary")

    if submitted:
        missing = [lbl for lbl, val in (("Business name", name), ("Industry", industry))
                    if not val.strip()]
        if missing:
            st.error(f"Please fill in: {', '.join(missing)}.")
            return False
        st.session_state.update({
            "ud_biz_name": name.strip(), "ud_biz_industry": industry.strip(),
            "ud_biz_dataset": represents.strip(), "ud_biz_goal": goal.strip(),
            "ud_setup_done": True,
        })
        st.rerun()
    return False


def _shorten(series, limit: int = 18):
    """Truncates long category labels. Full-length names on a categorical axis
    were colliding with each other and with the chart title.
    """
    return series.astype(str).str.slice(0, limit) + series.astype(str).str.len().gt(limit).map(
        {True: "…", False: ""})


def _user_chart_grid(cdf, caps):
    """Chart type is chosen by the shape of the question, not by habit.

    A trend over time reads as an area/line; share-of-a-whole as a donut;
    ranking as horizontal bars; a nested breakdown as a treemap; spread and
    outliers as a box plot; the distribution of a measure as a histogram;
    and a two-measure trade-off (revenue vs. margin) as a scatter, which no
    ranked bar chart can express. Rendering everything as bars flattens all
    those distinctions into one shape.
    """
    figs: list[tuple[str, object]] = []

    # ---- Time ----
    trend = ud.revenue_trend(cdf)
    if not trend.empty:
        y = [c for c in ("revenue", "profit") if c in trend.columns]
        f = px.area(trend, x="period", y=y, title="Revenue over time",
                     labels={"value": "", "period": "", "variable": ""})
        f.update_traces(line=dict(width=2.5))
        figs.append(("full", f))

        if "profit" in trend.columns and len(trend) > 1:
            m = trend.copy()
            m["margin_pct"] = (m["profit"] / m["revenue"].replace(0, pd.NA) * 100).round(2)
            f = px.line(m, x="period", y="margin_pct", markers=True, title="Margin % over time",
                         labels={"margin_pct": "", "period": ""})
            figs.append(("half", f))

        if len(trend) > 2:
            g = trend.copy()
            g["change_pct"] = (g["revenue"].pct_change() * 100).round(1)
            g = g.dropna(subset=["change_pct"])
            if not g.empty:
                f = px.bar(g, x="period", y="change_pct", title="Period-on-period revenue change %",
                            labels={"change_pct": "", "period": ""})
                figs.append(("half", f))

    # ---- Ranking ----
    for dim, title in (("product", "Top products by revenue"),
                        ("customer", "Top customers by revenue"),
                        ("employee", "Revenue by employee"),
                        ("campaign", "Revenue by campaign")):
        if dim in cdf.columns:
            d = ud.breakdown_by(cdf, dim, top_n=10)
            if not d.empty:
                d = d.copy()
                d["_label"] = _shorten(d[dim])
                f = px.bar(d, x="revenue", y="_label", orientation="h", title=title,
                            labels={"revenue": "", "_label": ""}, hover_name=dim)
                f.update_layout(yaxis=dict(autorange="reversed"))
                figs.append(("half", f))

    # ---- Share of whole ----
    for dim, title in (("category", "Revenue share by category"),
                        ("region", "Revenue share by region")):
        if dim in cdf.columns:
            d = ud.breakdown_by(cdf, dim, top_n=8)
            if not d.empty:
                f = px.pie(d, names=dim, values="revenue", title=title, hole=.55)
                f.update_traces(textposition="inside", textinfo="percent",
                                 insidetextorientation="horizontal")
                figs.append(("half", f))

    # ---- Nested composition ----
    if "category" in cdf.columns and "product" in cdf.columns:
        d = cdf.dropna(subset=["category", "product"]).groupby(
            ["category", "product"], dropna=False)["revenue"].sum().reset_index()
        if not d.empty and len(d) > 1:
            f = px.treemap(d, path=["category", "product"], values="revenue",
                            title="Revenue composition: category → product")
            figs.append(("half", f))

    # ---- Spread / outliers ----
    if "store" in cdf.columns:
        d = ud.breakdown_by(cdf, "store", top_n=12)
        if not d.empty:
            d = d.copy()
            d["_label"] = _shorten(d["store"], 14)
            f = px.bar(d, x="_label", y="revenue", title="Revenue by store",
                        labels={"revenue": "", "_label": ""}, hover_name="store")
            f.update_layout(xaxis=dict(tickangle=-35))
            figs.append(("half", f))

    if "product" in cdf.columns and cdf["product"].nunique() > 2:
        top = ud.breakdown_by(cdf, "product", top_n=6)["product"].tolist()
        d = cdf[cdf["product"].isin(top)].copy()
        if not d.empty:
            d["_label"] = _shorten(d["product"], 14)
            f = px.box(d, x="_label", y="revenue", title="Order-value spread by product",
                        labels={"revenue": "", "_label": ""}, points=False)
            f.update_layout(xaxis=dict(tickangle=-35))
            figs.append(("half", f))

    # ---- Distribution ----
    f = px.histogram(cdf, x="revenue", nbins=30, title="Distribution of transaction values",
                      labels={"revenue": "", "count": ""})
    figs.append(("half", f))

    # ---- Trade-off ----
    if "profit" in cdf.columns and "product" in cdf.columns:
        d = ud.breakdown_by(cdf, "product", top_n=40)
        if not d.empty and "margin_pct" in d.columns:
            f = px.scatter(d, x="revenue", y="margin_pct", size="revenue", color="margin_pct",
                            hover_name="product", title="Revenue vs. margin by product",
                            labels={"revenue": "Revenue", "margin_pct": "Margin %"})
            f.update_layout(coloraxis_showscale=False)
            figs.append(("half", f))

    if not figs:
        st.info("No chartable dimensions were detected in your mapping.")
        return

    pending = []
    for width, fig in figs:
        if width == "full":
            st.plotly_chart(theme.plotly_theme(fig, 330), use_container_width=True)
        else:
            pending.append(fig)
            if len(pending) == 2:
                for col, f in zip(st.columns(2), pending):
                    col.plotly_chart(theme.plotly_theme(f, 320), use_container_width=True)
                pending = []
    if pending:
        st.plotly_chart(theme.plotly_theme(pending[0], 320), use_container_width=True)


def render_user_overview(cdf, caps):
    kpi = ud.kpi_summary(cdf)
    cards = [theme.kpi_card("Total revenue", f"{kpi.get('revenue', 0):,.2f}",
                             note=st.session_state.get("ud_biz_dataset") or "From your data",
                             icon="cash")]
    if "profit" in kpi:
        cards.append(theme.kpi_card("Total profit", f"{kpi['profit']:,.2f}", icon="chart",
                                     note="Revenue less cost"))
        cards.append(theme.kpi_card("Margin", f"{kpi.get('margin_pct', 0):.2f}%", icon="percent",
                                     note="Profit as % of revenue"))
    cards.append(theme.kpi_card("Records", f"{kpi.get('records', 0):,}", icon="orders",
                                note="Rows analyzed"))
    for col, card in zip(st.columns(len(cards)), cards):
        col.markdown(card, unsafe_allow_html=True)

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
    _user_chart_grid(cdf, caps)

    findings = ud.generate_user_findings(cdf, caps)
    if findings:
        st.markdown("#### What needs your attention")
        for col, f in zip(st.columns(min(3, len(findings))), findings[:3]):
            color, bg = theme.severity_colors(f.severity)
            with col:
                st.markdown(
                    f'<div class="nx-card" style="border-left:4px solid {color};">'
                    f'<span class="nx-badge" style="background:{bg};color:{color};">'
                    f'{f.severity.upper()}</span><h4 style="margin-top:.6rem;">{f.title}</h4>'
                    f'<p>{f.summary[:150]}…</p></div>', unsafe_allow_html=True)


def render_user_findings(cdf, caps):
    findings = ud.generate_user_findings(cdf, caps)
    if not findings:
        st.info(
            "No findings yet. Findings need at least a revenue column, and trend-based "
            "findings also need a date column — check your column mapping."
        )
        return
    for f in findings:
        with st.container(border=True):
            st.markdown(theme.finding_header(f.title, f.severity, f.category, f.confidence),
                         unsafe_allow_html=True)
            text, source, backend, model, _v = _cached_narrate_generic(
                f.summary, json.dumps(f.evidence, default=str), f.recommendation)
            st.write(text)
            if source == "template":
                st.info("Verified analysis — AI explanation unavailable or unverifiable right "
                        "now; the summary above comes straight from your data, not a model.")
            else:
                label = "local Ollama" if backend == "ollama" else "free hosted Groq"
                st.caption(f"Narration source: AI ({label} · {model}), numerically verified")
            st.markdown(f"**Recommended focus:** {f.recommendation}")
            with st.expander("Evidence (raw computed values)"):
                st.json(f.evidence)


def _source_caption(narration) -> str:
    if narration.source == "template":
        return ("Verified analysis — computed directly from the data. "
                "AI rephrasing unavailable or unverifiable right now.")
    label = "local Ollama" if narration.backend == "ollama" else "free hosted Groq"
    return f"AI ({label} · {narration.model}) — numerically verified against the evidence"


def _render_chat(history_key: str, suggestions: list[str], answer_fn, placeholder: str):
    """Shared chat surface for both workspaces.

    Turns are replayed from session history so the conversation persists across
    Streamlit reruns; only the newest answer streams, because replaying the
    animation on every rerun would be noise rather than feedback.
    """
    history = st.session_state.setdefault(history_key, [])

    if suggestions and not history:
        st.caption("Try one of these, or type your own question:")
        cols = st.columns(2)
        for i, s in enumerate(suggestions[:4]):
            if cols[i % 2].button(s, key=f"{history_key}_sug_{i}", use_container_width=True):
                st.session_state[f"{history_key}_pending"] = s
                st.rerun()

    for turn in history:
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(turn["question"])
        with st.chat_message("assistant", avatar="📊"):
            st.markdown(turn["answer"])
            if turn.get("caption"):
                st.caption(turn["caption"])
            if turn.get("evidence"):
                with st.expander("Evidence — the computed values behind this answer"):
                    st.json(turn["evidence"])

    question = st.chat_input(placeholder) or st.session_state.pop(f"{history_key}_pending", None)
    if not question:
        return

    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="📊"):
        with st.spinner("Computing a verified answer…"):
            answer_text, caption, evidence = answer_fn(question)
        st.write_stream(nlg.stream_text(answer_text))
        if caption:
            st.caption(caption)
        if evidence:
            with st.expander("Evidence — the computed values behind this answer"):
                st.json(evidence)

    history.append({"question": question, "answer": answer_text,
                     "caption": caption, "evidence": evidence})
    st.rerun()


def render_user_ask(cdf, caps):
    st.caption(
        "Ask in plain language — formal or casual, including Nigerian English/Pidgin. "
        "Not sure what's possible? Ask *\"What can I ask?\"* and NexaSphere answers from "
        "the columns it detected in your files."
    )

    def answer(question: str):
        result = ud.answer_user_question(question, cdf, caps)
        if not result.supported:
            return result.template_answer, None, None
        narration = nlg.narrate_answer(question, result.result, result.template_answer)
        return narration.text, _source_caption(narration), (result.result or None)

    suggestions = [ex for label, ok in caps.items() if ok
                    for ex in ud._CAPABILITY_QUESTIONS.get(label, [])]
    _render_chat("ud_chat", suggestions, answer,
                  "Ask about your business data…")


def render_user_capabilities(cdf, caps):
    supported = [l for l, ok in caps.items() if ok]
    unsupported = [l for l, ok in caps.items() if not ok]
    st.markdown(f"Your data supports **{len(supported)} of {len(caps)}** analysis categories.")
    a, b = st.columns(2)
    with a:
        st.markdown("**Detected**")
        for label in supported:
            st.markdown(f"✓ {label}")
    with b:
        st.markdown("**Not detected**")
        for label in unsupported:
            needed = ud.missing_requirements(label, set(cdf.columns))
            extra = f" — needs {', '.join(needed)}" if needed else ""
            st.markdown(f"○ {label}{extra}")


def main():
    theme.inject_css()
    theme.apply_chart_defaults()

    if not st.session_state.get("nx_entered_app"):
        destination = theme.render_landing(_landing_kpi_preview())
        if destination is not None:
            st.session_state["nx_entered_app"] = True
            st.session_state["nx_jump_to_upload"] = destination == "upload"
            st.rerun()
        return

    # "Analyze My Business" from the landing page opens the business workspace
    # onboarding rather than dropping the user on the demo's Overview.
    if st.session_state.pop("nx_jump_to_upload", False):
        st.session_state["nx_workspace"] = "business"
        st.session_state["nx_pending_page"] = "Analyze My Business"

    # Apply any staged navigation BEFORE the nav radio is instantiated -- once
    # the widget owns its key, assigning to it raises StreamlitAPIException.
    pending = st.session_state.pop("nx_pending_page", None)
    if pending:
        st.session_state["nx_active_page"] = pending

    business = is_business_workspace()

    # A business workspace starts with required details, so every page after
    # it can be titled with their name instead of a generic placeholder.
    if business and not st.session_state.get("ud_setup_done"):
        theme.inject_css()
        if st.button("← Back to landing"):
            st.session_state["nx_workspace"] = "demo"
            st.session_state["nx_entered_app"] = False
            st.rerun()
        render_business_setup()
        return

    render_sidebar()

    # Navigation sits ABOVE the content it controls, so what you can do is
    # visible before what you're looking at.
    page, go_home = theme.app_shell(business_name() if business else "NexaSphere Demo")
    if go_home:
        st.session_state["nx_entered_app"] = False
        st.rerun()

    if not business:
        if page == "Overview":
            theme.page_title(
                "Business overview",
                "Every figure below is computed by the analytics engine and traceable to its evidence.",
            )
            render_kpi_row()
            st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
            render_overview_highlights()
        elif page == "Findings":
            theme.page_title("Findings",
                              "What needs management attention right now, ranked by severity.")
            render_findings_tab()
        elif page == "Ask NexaSphere":
            theme.page_title("Ask NexaSphere",
                              "Ask in plain language. Answers are calculated first, then explained.")
            render_ask_tab()
        elif page == "Dashboards":
            theme.page_title("Dashboards",
                              "Visual breakdowns across products, regions, partners, campaigns and people.")
            render_dashboard_tab()
        else:
            theme.page_title("Analyze My Business",
                              "Upload your own business files and run the same evidence-backed "
                              "pipeline on them.")
            render_analyze_my_business_tab()
        return

    # ---- Business workspace: every page reads from their uploaded data ----
    name = business_name()
    cdf, caps = user_frame()

    if page == "Analyze My Business" or cdf is None:
        if cdf is None and page != "Analyze My Business":
            st.markdown(
                theme.alert("info", "No data analyzed yet",
                             "Upload your files and confirm the column mapping below to unlock "
                             f"{page} for {name}."),
                unsafe_allow_html=True)
        theme.page_title(f"{name} · Data",
                          "Upload your business files, confirm what each column means, and analyze.")
        render_analyze_my_business_tab()
        return

    if page == "Overview":
        theme.page_title(f"{name} · Overview",
                          f"Computed from your uploaded data. "
                          f"{st.session_state.get('ud_biz_goal') or 'Every figure is traceable to its evidence.'}")
        render_user_overview(cdf, caps)
    elif page == "Findings":
        theme.page_title(f"{name} · Findings",
                          "What stands out in your data, with the evidence behind each one.")
        render_user_findings(cdf, caps)
    elif page == "Ask NexaSphere":
        theme.page_title(f"Ask about {name}",
                          "Answers are calculated from your data first, then explained.")
        render_user_ask(cdf, caps)
    elif page == "Dashboards":
        theme.page_title(f"{name} · Dashboards",
                          "Charts chosen to suit the columns detected in your data.")
        _user_chart_grid(cdf, caps)
        st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
        st.markdown("#### What your data can answer")
        render_user_capabilities(cdf, caps)


if __name__ == "__main__":
    main()
