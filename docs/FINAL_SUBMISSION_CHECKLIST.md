# Final Submission Checklist

**Deadline: 29 August 2026, 11:59. One submission. No edits, no resubmissions.**

## Case Study 4 — required capabilities

| Requirement | Status | Where |
|---|---|---|
| Load/connect to the provided dataset | ✅ | `data_loader.py` — 12 CSVs, cached |
| Display important KPIs | ✅ | Overview — revenue, profit, margin, orders, with change + sparklines |
| Allow users to ask questions | ✅ | Ask Ordino — streaming chat |
| Generate accurate natural-language answers | ✅ | `qa.py` → `nlg.py`, grounded |
| Present relevant visual insights | ✅ | Dashboards — 9 charts, multiple types |
| Identify at least three findings | ✅ | Six ranked findings |
| Provide practical recommendations | ✅ | Every finding carries one |
| Analyse KPIs from the dataset | ✅ | `analytics.py` |
| Identify trends, anomalies, risks, gaps | ✅ | z-score outliers, growth gap, target attainment |
| Compare across products/stores/regions/employees/campaigns/segments | ✅ | `breakdown_by`, campaign ROI, segment value, store performance |
| Explain possible reasons | ✅ | `possible_drivers` — stated as "consistent with", never as cause |
| All nine suggested questions | ✅ | Routed and tested — see SAMPLE_IO.md |

## General submission requirements

| Requirement | Status | Where |
|---|---|---|
| Clear explanation of the business problem | ✅ | `problem-statement.md`, README |
| Functional AI-powered prototype | ✅ | The app |
| Brief explanation of solution workflow | ✅ | README, `solution.md`, `architecture.md` |
| List of tools/platforms/AI models | ✅ | README tech-stack table |
| Sample inputs and outputs | ✅ | `SAMPLE_IO.md` |
| Evidence solution was tested | ✅ | `testing.md`, `evaluation.md`, 140 tests |
| Short presentation/demonstration | ⬜ | **Deck exists; video must be recorded** |
| Explanation of expected business impact | ✅ | `business-impact.md` |

## Pre-submission verification

### Product
- [ ] `streamlit run app.py` starts cleanly
- [ ] Landing page renders; both CTAs work
- [ ] Demo: revenue +63.2% / profit +53.8% / margin −1.45 pp
- [ ] All six findings render with evidence and recommendations
- [ ] Ask: hero question, a Pidgin phrasing, "What can I ask?", and an out-of-scope question
- [ ] Dashboards render with no overlapping labels
- [ ] Upload a CSV → profile → map → confirm → business workspace
- [ ] Capability matrix names missing columns for unsupported analyses
- [ ] Light and dark themes both legible
- [ ] Mobile layout checked

### Tests
- [ ] `python -m pytest tests/ -q` → all pass (140 at time of writing)

### Deployment
- [ ] Pushed to GitHub on `main`
- [ ] `git check-ignore -v .streamlit/secrets.toml` matches (secret not committed)
- [ ] Deployed on Streamlit Community Cloud; `GROQ_API_KEY` set in Secrets
- [ ] Sidebar shows "AI connected" on the live URL
- [ ] Live URL opens in a private window and on a phone

### Submission package
- [ ] Google Drive folder created, sharing = **Anyone with the link can view**
- [ ] `Presentation.pdf`
- [ ] `Demo Video.mp4` (≤ 5 min; script targets 3)
- [ ] `Links or README.pdf`
- [ ] Folder opens in an incognito window
- [ ] **Participant ID confirmed** — BF-0260 (verify against your registration email)
- [ ] **Registered email confirmed** — must match registration *exactly*
- [ ] Everything double-checked before submitting: there is no second attempt

## Submission README template

```
Project:        Ordino — AI Business Intelligence Assistant
Track:          AI for Business & Productivity
Case Study:     Case Study 4 — AI Business Intelligence Assistant
Participant:    Tomola Oke
Participant ID: BF-0260
Email:          <your registered email>

Live Demo:      https://ordino.streamlit.app
Repository:     https://github.com/<user>/ordino
Demo Video:     <Drive link>
Presentation:   <Drive link>

Technology:     Python · Streamlit · pandas · NumPy · Plotly ·
                pypdf · openpyxl · python-docx · pytest ·
                Ollama (local open-source LLM) / Groq free tier
Cost:           $0 — no paid API, database or hosting
```
