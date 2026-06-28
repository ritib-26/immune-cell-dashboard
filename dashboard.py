"""
Streamlit dashboard for the Miraclib clinical trial immune cell analysis.

Run:
    streamlit run dashboard.py
"""

import sqlite3
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from src.analysis import (
    get_frequency_table,
    get_responder_comparison,
    run_statistics,
    get_baseline_subset,
    get_samples_per_project,
    get_response_counts,
    get_sex_counts,
    get_time_course, 
)

### page config ###
st.set_page_config(
    page_title="Miraclib Clinical Trial | Immune Cell Analysis",
    page_icon="💉",
    layout="wide",
)

### global styles ###
st.markdown("""
    <style>
        /* white background */
        .stApp { background-color: #ffffff; }
        
        /* sidebar */
        [data-testid="stSidebar"] { background-color: #f0f4f8; }
        
        /* metric cards */
        [data-testid="stMetric"] {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            color: #000000;
            text-align: center;
        }
        [data-testid="stMetricLabel"] {
            color: #000000 !important;
            justify-content: center;
        }
        [data-testid="stMetricValue"] {
            color: #000000 !important;
            justify-content: center;
        }

        /* all text to black */
        html, body, [class*="css"], p, span, div, label {
            color: #000000 !important;
        }

        /* section headers */
        h1 { color: #1a365d !important; }
        h2 { color: #2c5282 !important; }
        h3 { color: #2d3748 !important; }

        /* divider color */
        hr { border-color: #e2e8f0; }
        
        /* dropdown text color */
        [data-testid="stSelectbox"] div[data-baseweb="select"] {
            background-color: #ffffff;
        }
        [data-testid="stSelectbox"] div[data-baseweb="select"] * {
            color: #000000 !important;
            background-color: #ffffff !important;
        }
        
        [data-testid="stMetricLabel"] {
            color: #000000 !important;
            justify-content: center;
            display: flex;
        }
        [data-testid="stMetricValue"] {
            color: #000000 !important;
            justify-content: center;
            display: flex;
        }
        /* text input color */
        [data-testid="stTextInput"] input {
            background-color: #ffffff !important;
            color: #000000 !important;
        }
        /* placeholder text color */
        [data-testid="stTextInput"] input::placeholder {
            color: #999999 !important;
        }
        /* dataframe colors */
        [data-testid="stDataFrame"] iframe {
            background-color: #ffffff !important;
        }
        /* hide anchor links on headers */
        [data-testid="stMarkdownContainer"] a {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

### database connection ###
@st.cache_resource
def get_connection():
    return sqlite3.connect("cell_counts.db", check_same_thread=False)

conn = get_connection()

### load data once and cache ###
@st.cache_data
def load_data():
    freq_df      = get_frequency_table(conn)
    resp_df      = get_responder_comparison(conn)
    stats_df     = run_statistics(resp_df)
    baseline_df  = get_baseline_subset(conn)
    proj_df      = get_samples_per_project(baseline_df)
    response_df  = get_response_counts(baseline_df)
    sex_df       = get_sex_counts(baseline_df)
    timecourse_df = get_time_course(conn)
    return freq_df, resp_df, stats_df, baseline_df, proj_df, response_df, sex_df, timecourse_df

freq_df, resp_df, stats_df, baseline_df, proj_df, response_df, sex_df, timecourse_df = load_data()

### sidebar ###
st.sidebar.image("https://img.icons8.com/ios/100/1a365d/dna-helix.png", width=60)
st.sidebar.title("Miraclib Trial")
st.sidebar.markdown("**Immune Cell Population Analysis**")
st.sidebar.divider()
page = st.sidebar.radio(
    "Navigate",
    ["📊 Analysis", "📈 Additional Analysis", "🔬 Data Explorer"],
)
st.sidebar.divider()
st.sidebar.markdown("**Trial Summary**")
st.sidebar.markdown(f"- **Samples:** {freq_df['sample'].nunique():,}")
st.sidebar.markdown(f"- **Subjects:** {baseline_df['subject_id'].nunique():,}")
st.sidebar.markdown(f"- **Projects:** {baseline_df['project_id'].nunique()}")
st.sidebar.markdown(f"- **Treatment:** Miraclib")
st.sidebar.markdown(f"- **Indication:** Melanoma")

### PAGE 1 — ANALYSIS ###
if page == "📊 Analysis":
    st.title("Miraclib Clinical Trial")
    st.markdown("Exploring immune cell population dynamics in melanoma patients receiving miraclib treatment.")
    st.divider()

    # key findings
    sig_pops = stats_df[stats_df["significant"]]
    non_sig  = stats_df[~stats_df["significant"]]
    resp_yes = response_df.loc[response_df["response"] == "yes", "n_subjects"].values[0]
    resp_no  = response_df.loc[response_df["response"] == "no",  "n_subjects"].values[0]
    sex_m    = sex_df.loc[sex_df["sex"] == "M", "n_subjects"].values[0]
    sex_f    = sex_df.loc[sex_df["sex"] == "F", "n_subjects"].values[0]
    n_resp        = resp_df[resp_df["response"] == "yes"]["sample"].nunique()
    n_nonresp     = resp_df[resp_df["response"] == "no"]["sample"].nunique()
    n_resp_subj   = round(n_resp / 3)
    n_nonresp_subj = round(n_nonresp / 3)

    st.markdown(
        f"""
        <div style="
            background-color: #ebf8ff;
            border-left: 5px solid #2c5282;
            border-radius: 6px;
            padding: 20px 24px;
            margin-bottom: 24px;
        ">
            <h4 style="color: #1a365d; margin-top: 0;">🔍 Key Findings</h4>
            <ul style="color: #000000; margin: 0; padding-left: 20px;">
                <li>Analysis includes <b>{n_resp + n_nonresp}</b> total PBMC samples from <b>{n_resp_subj + n_nonresp_subj}</b> melanoma subjects treated with miraclib across 3 timepoints</li>
                <li><b>Baseline cohort is balanced</b> across responders/non-responders ({resp_yes} vs {resp_no}) and sex ({sex_m}M / {sex_f}F), supporting validity of the trial design</li>
                {"".join([
                    f"<li><b>{row['population']}</b> frequencies were significantly higher in responders "
                    f"(mean {row['mean_responders']}% vs {row['mean_non_responders']}%, p = {row['p_value']:.4f})</li>"
                    for _, row in sig_pops.iterrows()
                ])}
                <li><b>{', '.join(non_sig['population'].tolist())}</b> showed no significant difference between groups</li>
                <li>Statistical test: Mann-Whitney U, α = 0.05</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

    # baseline overview
    st.header("Baseline Patient Overview")
    st.markdown(
        f"Summary of **{len(baseline_df)} PBMC samples** from **{baseline_df['subject_id'].nunique()} melanoma subjects** "
        f"treated with miraclib at baseline (day 0), across **{baseline_df['project_id'].nunique()} projects**."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("<h3 style='text-align: center; color: #2d3748;'>Samples per <br> Project</h3>", unsafe_allow_html=True)
        fig = px.pie(
            proj_df,
            names="project_id",
            values="n_samples",
            color="project_id",
            color_discrete_sequence=["#2c5282", "#3182ce"],
        )
        fig.update_traces(textinfo="label+percent+value", textfont=dict(color="black"))
        fig.update_layout(showlegend=False, paper_bgcolor="white", font=dict(color="black"))
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.markdown("<h3 style='text-align: center; color: #2d3748;'>Responders vs <br> Non-Responders</h3>", unsafe_allow_html=True)
        fig = px.pie(
            response_df,
            names="response",
            values="n_subjects",
            color="response",
            color_discrete_map={"yes": "#38a169", "no": "#e53e3e"},
        )
        fig.update_traces(textinfo="label+percent+value", textfont=dict(color="black"))
        fig.update_layout(showlegend=False, paper_bgcolor="white", font=dict(color="black"))
        st.plotly_chart(fig, width="stretch")

    with col3:
        st.markdown("<h3 style='text-align: center; color: #2d3748;'>Sex<br>Distribution</h3>", unsafe_allow_html=True)
        fig = px.pie(
            sex_df,
            names="sex",
            values="n_subjects",
            color="sex",
            color_discrete_map={"M": "#2c5282", "F": "#b83280"},
        )
        fig.update_traces(textinfo="label+percent+value", textfont=dict(color="black"))
        fig.update_layout(showlegend=False, paper_bgcolor="white", font=dict(color="black"))
        st.plotly_chart(fig, width="stretch")

    st.divider()

    # treatment response 
    st.header("Treatment Response by Cell Population")
    st.markdown(
        f"Compare immune cell frequencies between **{n_resp_subj} responders** "
        f"and **{n_nonresp_subj} non-responders** ({n_resp + n_nonresp} total samples across all timepoints: day 0, 7, and 14). "
        f"Only PBMC samples from melanoma patients treated with miraclib are included."
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Select Population")
        populations = sorted(resp_df["population"].unique())
        selected_pop = st.selectbox("Cell population", populations, label_visibility="collapsed", key="analysis_pop")

        st.subheader("Statistical Results")
        display_stats = stats_df[["population", "p_value", "significant"]].copy()
        display_stats["p_value"] = display_stats["p_value"].apply(lambda x: f"{x:.4f}")
        display_stats["significant"] = display_stats["significant"].apply(lambda x: "✓" if x else "✗")
        display_stats.columns = ["Population", "P-Value", "Significant"]
        st.dataframe(display_stats, width="stretch", hide_index=True)

        sig_pops = stats_df[stats_df["significant"]]["population"].tolist()
        if sig_pops:
            st.success(f"**{', '.join(sig_pops)}** showed a significant difference between responders and non-responders (α = 0.05, Mann-Whitney U test).")
        else:
            st.info("No populations showed a significant difference at α = 0.05.")

    with col2:
        subset = resp_df[resp_df["population"] == selected_pop]
        p_val  = stats_df.loc[stats_df["population"] == selected_pop, "p_value"].values[0]
        sig    = "Significant ✓" if p_val < 0.05 else "Not Significant"

        fig = px.box(
            subset,
            x="response",
            y="percentage",
            color="response",
            points="all",
            labels={"response": "Response", "percentage": "Frequency (%)"},
            title=f"{selected_pop} — p = {p_val:.4f} ({sig})",
            color_discrete_map={"yes": "#38a169", "no": "#e53e3e"},
            category_orders={"response": ["yes", "no"]},
        )
        fig.update_layout(
            showlegend=False,
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(color="black", family="sans-serif"),
            xaxis=dict(
                ticktext=["Responder", "Non-Responder"],
                tickvals=["yes", "no"],
                tickfont=dict(color="black"),
                title_font=dict(color="black"),
            ),
            yaxis=dict(
                tickfont=dict(color="black"),
                title_font=dict(color="black"),
            ),
            title_font=dict(color="black"),
        )
        st.plotly_chart(fig, width="stretch")

### PAGE 2 — ADDITIONAL ANALYSIS ###
elif page == "📈 Additional Analysis":
    st.title("Cell Population Dynamics Over Time")
    st.markdown(
        "How do immune cell population frequencies change over the course of miraclib treatment? "
        "Comparing responders vs non-responders across day 0, 7, and 14. "
        "Melanoma · Miraclib · PBMC samples only. Error bars represent SEM."
    )
    st.divider()

    # aggregate mean per timepoint, population, response
    import pandas as pd
    summary = (
        timecourse_df
        .groupby(["timepoint", "population", "response"])["percentage"]
        .agg(mean="mean", sem="sem")
        .reset_index()
    )

    selected_pop = st.selectbox(
        "Select cell population",
        sorted(timecourse_df["population"].unique()),
        key="timecourse_pop",
    )

    subset = summary[summary["population"] == selected_pop]

    fig = px.line(
        subset,
        x="timepoint",
        y="mean",
        color="response",
        markers=True,
        error_y="sem",
        labels={
            "timepoint": "Days from Treatment Start",
            "mean": "Mean Frequency (%)",
            "response": "Response",
        },
        title=f"{selected_pop} frequency over time — Responders vs Non-Responders",
        color_discrete_map={"yes": "#38a169", "no": "#e53e3e"},
        category_orders={"response": ["yes", "no"]},
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black", family="sans-serif"),
        xaxis=dict(
            tickvals=[0, 7, 14],
            ticktext=["Day 0", "Day 7", "Day 14"],
            tickfont=dict(color="black"),
            title_font=dict(color="black"),
        ),
        yaxis=dict(
            tickfont=dict(color="black"),
            title_font=dict(color="black"),
        ),
        title_font=dict(color="black"),
        legend=dict(
            title="Response",
            font=dict(color="black"),
        ),
    )
    st.plotly_chart(fig, width="stretch")

    st.divider()

    # show all populations at once as small multiples
    st.subheader("All Populations Overview")
    fig2 = px.line(
        summary,
        x="timepoint",
        y="mean",
        color="response",
        facet_col="population",
        markers=True,
        error_y="sem",
        labels={
            "timepoint": "Day",
            "mean": "Mean Frequency (%)",
            "response": "Response",
        },
        color_discrete_map={"yes": "#38a169", "no": "#e53e3e"},
        category_orders={"response": ["yes", "no"]},
    )
    fig2.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black"),
    )
    fig2.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig2.update_xaxes(
        tickvals=[0, 7, 14],
        ticktext=["D0", "D7", "D14"],
        tickfont=dict(color="black"),
        title_font=dict(color="black"),
    )
    fig2.update_yaxes(
        tickfont=dict(color="black"),
        title_font=dict(color="black"),
    )
    st.plotly_chart(fig2, width="stretch")


### PAGE 3 — DATA EXPLORER ###
elif page == "🔬 Data Explorer":
    st.title("Data Explorer")
    st.markdown("Browse and filter the full cell population frequency table.")
    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        pop_filter = st.selectbox(
            "Filter by population",
            ["All"] + sorted(freq_df["population"].unique()),
        )
    with col2:
        sample_search = st.text_input("Search by sample ID", placeholder="e.g. sample00001")
    with col3:
        pct_range = st.slider("Frequency % range", 0.0, 100.0, (0.0, 100.0))

    # apply filters
    filtered = freq_df.copy()
    if pop_filter != "All":
        filtered = filtered[filtered["population"] == pop_filter]
    if sample_search:
        filtered = filtered[filtered["sample"].str.contains(sample_search, case=False)]
    filtered = filtered[
        (filtered["percentage"] >= pct_range[0]) &
        (filtered["percentage"] <= pct_range[1])
    ]

    st.markdown(f"Showing **{len(filtered):,}** rows")
    st.dataframe(filtered, width="stretch", height=600)