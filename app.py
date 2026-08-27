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


def render_sidebar():
    st.sidebar.title("NexaSphere")
    st.sidebar.caption("AI Business Intelligence Assistant · BuildFest 2026")
    _llm_status_badge()
    st.sidebar.markdown("---")
    start, end = an.dataset_date_range()
    st.sidebar.markdown(f"**Dataset window**\n\n{start.date()} → {end.date()}")
    st.sidebar.markdown("---")
    st.sidebar.caption(
        "All KPIs are computed by a deterministic analytics engine. "
        "The AI layer only explains verified numbers -- it never invents them."
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

    cards = [
        theme.kpi_card("Revenue", f"{latest['revenue']:,.0f}",
                        f"{abs(change['revenue_pct']):.1f}%", change["revenue_pct"] >= 0, "Last 30 days"),
        theme.kpi_card("Gross profit", f"{latest['gross_profit']:,.0f}",
                        f"{abs(change['gross_profit_pct']):.1f}%", change["gross_profit_pct"] >= 0, "Last 30 days"),
        theme.kpi_card("Gross margin", f"{latest['margin_pct']:.2f}%",
                        f"{abs(change['margin_pp']):.2f} pp", change["margin_pp"] >= 0, "vs. prior period"),
        theme.kpi_card("Orders", f"{latest['orders']:,}",
                        f"{abs(change['orders_pct']):.1f}%", change["orders_pct"] >= 0, "Last 30 days"),
    ]
    for col, card in zip(st.columns(4), cards):
        col.markdown(card, unsafe_allow_html=True)

    if comp["margin_pressure"]:
        st.markdown(
            f"""
            <div style="background:#FDF3E3;border:1px solid #F3DFB4;border-left:4px solid #E8A33D;
                        border-radius:14px;padding:1rem 1.2rem;margin-top:1rem;">
              <b style="color:#14142B;font-size:.94rem;">Margin under pressure</b>
              <div style="color:#6E6D8A;font-size:.88rem;margin-top:.25rem;line-height:1.55;">
                Revenue grew {change['revenue_pct']:+.1f}% while gross profit grew only
                {change['gross_profit_pct']:+.1f}% &mdash; margin moved {change['margin_pp']:+.2f} pp.
                See <b>Findings</b> for the evidence trail.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_findings_tab():
    st.subheader("What needs management attention right now")
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
    st.subheader("Ask a business question")
    st.caption("Answers are computed by the analytics engine, then phrased by the AI narration layer.")

    with st.expander("Try a suggested question"):
        for q in qa.SUGGESTED_QUESTIONS:
            if st.button(q, key=f"suggest_{q}"):
                st.session_state["question_input"] = q

    question = st.text_input("Your question", key="question_input", placeholder="e.g. Which marketing campaigns generate the best ROI?")
    if st.button("Ask", type="primary") and question.strip():
        with st.spinner("Computing verified answer..."):
            result = qa.answer_question(question)
        st.markdown(f"**Answer:** {result.narration.text}")
        if result.narration.source == "template":
            st.info("Verified analysis -- AI explanation unavailable or unverifiable right now; "
                    "the answer above is generated directly from the analytics engine, not a model.")
        else:
            label = "local Ollama" if result.narration.backend == "ollama" else "free hosted Groq"
            st.caption(f"Narration source: AI ({label} · {result.narration.model}), numerically verified")
        st.caption(f"Matched intent: `{result.intent}`")
        with st.expander("Underlying computed result"):
            st.json(result.result)


def render_dashboard_tab():
    st.subheader("Business dashboards")

    trend = an.monthly_revenue_trend()
    fig = px.line(trend, x="month", y=["revenue", "gross_profit"], markers=True,
                   labels={"value": "Amount", "month": "Month", "variable": "Metric"},
                   title="Monthly Revenue vs. Gross Profit")
    st.plotly_chart(theme.plotly_theme(fig), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        cat = an.breakdown_by("category")
        fig2 = px.bar(cat, x="category", y="revenue", color="margin_pct",
                       title="Revenue & Margin by Category", color_continuous_scale="RdYlGn")
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
                       title="Revenue per Employee by Store", color_continuous_scale="RdYlGn")
        st.plotly_chart(theme.plotly_theme(fig6), use_container_width=True)
        st.caption("Sales are recorded per store, not per individual employee -- this reflects "
                   "store-level team performance, not individual attribution.")
    with col6:
        seg = an.customer_segment_value()
        fig7 = px.bar(seg, x="customer_segment", y="revenue_per_customer", color="margin_pct",
                       title="Revenue per Customer by Segment", color_continuous_scale="RdYlGn")
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
    st.subheader("Analyze My Business")
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

    with st.expander("Business context (optional -- not required for analysis)"):
        colA, colB = st.columns(2)
        colA.text_input("Business name", key="ud_biz_name")
        colA.text_input("Industry", key="ud_biz_industry")
        colB.text_input("What does this dataset represent?", key="ud_biz_dataset")
        colB.text_input("Primary business goal", key="ud_biz_goal")

    st.markdown("#### Confirm column mapping")
    st.caption(
        "NexaSphere guessed these mappings from your column names and types. Correct any "
        "that are wrong -- nothing is analyzed until you confirm below."
    )

    column_options = ["(none)"] + list(df.columns)
    mapping = st.session_state["ud_mapping"]
    new_mapping = {}
    map_cols = st.columns(2)
    for i, concept in enumerate(ud.CANONICAL_FIELDS.keys()):
        current = mapping.get(concept)
        idx = column_options.index(current) if current in column_options else 0
        with map_cols[i % 2]:
            choice = st.selectbox(
                concept.replace("_", " ").capitalize(), column_options, index=idx, key=f"ud_map_{concept}"
            )
        new_mapping[concept] = None if choice == "(none)" else choice
    st.session_state["ud_mapping"] = new_mapping

    if st.button("Confirm & Analyze", type="primary"):
        st.session_state["ud_confirmed"] = True

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


def main():
    theme.inject_css()

    if not st.session_state.get("nx_entered_app"):
        destination = theme.render_landing(_landing_kpi_preview())
        if destination is not None:
            st.session_state["nx_entered_app"] = True
            st.session_state["nx_jump_to_upload"] = destination == "upload"
            st.rerun()
        return

    render_sidebar()
    if st.sidebar.button("← Back to landing page"):
        st.session_state["nx_entered_app"] = False
        st.rerun()

    theme.app_header(
        "Business overview",
        "Every figure below is computed by the analytics engine and traceable to its evidence.",
        "NexaSphere Demo",
    )
    render_kpi_row()

    if st.session_state.pop("nx_jump_to_upload", False):
        st.info("👉 Head to the **📁 Analyze My Business** tab below to upload your own data.")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["🔎 Findings", "💬 Ask a Question", "📊 Dashboards", "📁 Analyze My Business"]
    )
    with tab1:
        render_findings_tab()
    with tab2:
        render_ask_tab()
    with tab3:
        render_dashboard_tab()
    with tab4:
        render_analyze_my_business_tab()


if __name__ == "__main__":
    main()
