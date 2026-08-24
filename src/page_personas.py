import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.fem_colours import FEM_ORANGE, FEM_BROWN, FEM_TAUPE, FEM_STEEL, FEM_NAVY, FEM_PALETTE
from src.data_loader import (
    load_personas_centroids,
    load_personas_profile,
    load_personas_centroids_by_gender,
    load_personas_profile_by_gender,
    load_personas_elbow,
    load_personas_centroids_by_region,
    load_personas_profile_by_region,
    load_personas_elbow_by_region,
    REGIONS,
)
from src.translations import tr

_MISSING = (
    "Pre-aggregated persona data not found. "
    "Run `python -m pipeline.run_pipeline --pages personas` (from pipeline_output/) to generate it."
)

PROFILE_VARS = ["gender", "age_group", "use", "occupation", "religion", "life_goals"]

# Raw 'gender' values are unprocessed bilingual text (etl_personas.py clusters
# on the raw survey column directly, doesn't run it through _clean_bilingual).
GENDER_DISPLAY = {
    "Femme Nyɔnu": "Femme",
    "Homme Sunnu": "Homme",
}
GENDER_COLORS = {
    "Femme Nyɔnu": FEM_ORANGE,
    "Homme Sunnu": FEM_NAVY,
}


# ── Chart helpers ─────────────────────────────────────────────────────────────

def _strip_hausa(text: str) -> str:
    """Return only the French part of bilingual 'French/Fon' labels (Benin's
    order -- first segment, not last)."""
    if not text or pd.isna(text):
        return str(text).strip()
    text = str(text)
    if "|" in text:
        parts = text.split("|")
        return "|".join(_strip_hausa(p) for p in parts)
    if "/" in text:
        split = text.split("/", 1)
        if len(split) == 2:
            french = split[0].strip()
            return french if french else text.strip()
    else:
        split = text.split(" / ", 1)
        if len(split) == 2:
            french = split[0].strip()
            return french if french else text.strip()
    return text.strip().replace("|", "; ")


def _hbar(series, title, top_n=10, key=None):
    series = series.head(top_n)
    if series is None or series.empty:
        return
    colors = (FEM_PALETTE * (len(series) // len(FEM_PALETTE) + 1))[:len(series)]
    fig = go.Figure(go.Bar(
        y=series.index.astype(str),
        x=series.values,
        orientation="h",
        marker_color=colors,
        text=[f"{v*100:.1f}%" for v in series.values],
        textposition="outside",
        cliponaxis=False,
    ))
    fig.update_layout(
        title=title,
        xaxis=dict(showgrid=False, showticklabels=False,
                   range=[0, series.max() * 1.35] if len(series) else [0, 1]),
        yaxis=dict(showgrid=False, autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=80, t=36, b=10),
        height=max(180, len(series) * 34 + 60),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


# ── Elbow plot ────────────────────────────────────────────────────────────────

def render_elbow_plot(df_elbow, split_col="gender", key="elbow_plot"):
    st.subheader("Choosing the number of clusters")
    label_map = GENDER_DISPLAY if split_col == "gender" else {}
    color_map = GENDER_COLORS if split_col == "gender" else {}
    split_noun = "female and male respondents" if split_col == "gender" else "each region"
    st.caption(
        "Each line shows the within-cluster cost (sum of dissimilarities) for "
        f"k = 1 – 6 clusters, computed separately for {split_noun}. "
        "The 'elbow' — where the curve flattens — indicates the optimal k."
    )

    groups = df_elbow[split_col].unique()
    fig = go.Figure()
    for i, g in enumerate(groups):
        sub = df_elbow[df_elbow[split_col] == g].sort_values("k")
        color = color_map.get(g, FEM_PALETTE[i % len(FEM_PALETTE)])
        label = tr(label_map.get(g, g))
        fig.add_trace(go.Scatter(
            x=sub["k"], y=sub["cost"],
            mode="lines+markers",
            name=label,
            line=dict(color=color, width=2),
            marker=dict(size=7),
        ))

    fig.update_layout(
        xaxis=dict(title="Number of clusters (k)", dtick=1, showgrid=False),
        yaxis=dict(title="Within-cluster cost", showgrid=True, gridcolor="#eeeeee"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(title=split_col.title(), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


# ── Section renderers ─────────────────────────────────────────────────────────

def render_centroid_table(df_centroids, split_label=None, split_col="gender"):
    st.subheader("Persona summary")
    st.caption(
        "Each row is a cluster centroid — the representative values for that persona. "
        "Count shows the number of respondents in each cluster."
    )

    display = df_centroids.copy()
    # Drop "persona" (just the row index) and the split column itself (constant
    # within this table, already shown by the tab it's under) -- but keep any
    # *other* clustering variable, e.g. "gender" is a real feature when split_col
    # is "region", not just bookkeeping.
    display.drop(columns=["persona", split_col], inplace=True, errors="ignore")
    for col in ("occupation", "religion", "life_goals"):
        if col in display.columns:
            display[col] = display[col].apply(lambda x: tr(_strip_hausa(x)))
    if "gender" in display.columns:
        display["gender"] = display["gender"].map(GENDER_DISPLAY).fillna(display["gender"])

    for col in ["age", "count", "weighted_count"]:
        if col in display.columns and display[col].dtype in [int, float]:
            display[col] = display[col].apply(
                lambda v: f"{int(v):,}" if pd.notna(v) else ""
            )

    display.columns = [col.replace("_", " ").title() for col in display.columns]
    st.dataframe(display, use_container_width=True)


def render_persona_profiles(df_profile, n_personas, split_label=None):
    key_suffix = split_label.replace(" ", "_").replace("/", "") if split_label else "overall"
    st.subheader("Persona deep-dive")
    st.caption("Select a persona to see the distribution of key variables within that cluster.")

    persona_id = st.selectbox(
        "Select persona",
        list(range(n_personas)),
        format_func=lambda x: f"Persona {x}",
        key=f"persona_select_{key_suffix}",
    )

    sub = df_profile[df_profile["persona"] == persona_id].copy()

    count_row = sub[sub["variable"] == "_count"]
    if not count_row.empty:
        n = count_row[count_row["value"] == "n"]["proportion"].values
        wn = count_row[count_row["value"] == "weighted_n"]["proportion"].values
        c1, c2 = st.columns(2)
        c1.metric("Respondents", f"{int(n[0]):,}" if len(n) else "N/A")
        c2.metric("Weighted N", f"{wn[0]:,.0f}" if len(wn) else "N/A")

    profile_vars = [v for v in sub["variable"].unique() if not v.startswith("_")]
    cols = st.columns(2)
    for i, var in enumerate(profile_vars):
        var_sub = sub[sub["variable"] == var].copy()
        if var_sub.empty:
            continue
        if var in ("occupation", "religion", "life_goals"):
            var_sub["value"] = var_sub["value"].apply(lambda x: tr(_strip_hausa(x)))
        if set(var_sub["value"].tolist()) == {"mean"}:
            val = var_sub["proportion"].iloc[0]
            cols[i % 2].metric(var.replace("_", " ").title(), f"{val:.1f}")
        else:
            s = var_sub.set_index("value")["proportion"].sort_values(ascending=False)
            with cols[i % 2]:
                _hbar(s, var.replace("_", " ").title(),
                      key=f"persona_{key_suffix}_{persona_id}_{var}")


def render_comparison(df_profile, n_personas, split_label=None):
    key_suffix = split_label.replace(" ", "_").replace("/", "") if split_label else "overall"
    st.subheader("Persona comparison")
    st.caption("Compare the distribution of one variable across all personas.")

    profile_vars = [v for v in df_profile["variable"].unique() if not v.startswith("_")]
    selected_var = st.selectbox(
        "Select variable", profile_vars,
        format_func=lambda v: v.replace("_", " ").title(),
        key=f"persona_compare_var_{key_suffix}",
    )

    sub = df_profile[df_profile["variable"] == selected_var].copy()
    if selected_var in ("occupation", "religion", "life_goals"):
        sub["value"] = sub["value"].apply(lambda x: tr(_strip_hausa(x)))

    if set(sub["value"].tolist()) == {"mean"}:
        st.info("Comparison chart not available for numeric variables.")
        return

    traces = []
    for i, pid in enumerate(range(n_personas)):
        pdata = sub[sub["persona"] == pid].set_index("value")["proportion"]
        traces.append(go.Bar(
            name=f"Persona {pid}",
            x=pdata.index.astype(str),
            y=pdata.values,
            marker_color=FEM_PALETTE[i % len(FEM_PALETTE)],
            text=[f"{v*100:.0f}%" for v in pdata.values],
            textposition="outside",
        ))

    if not traces:
        return

    fig = go.Figure(traces)
    fig.update_layout(
        barmode="group",
        yaxis=dict(tickformat=".0%", showgrid=False, title="% of persona"),
        xaxis=dict(showgrid=False, tickangle=-30),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=80, l=10, r=10),
        height=360,
        legend_title="Persona",
    )
    st.plotly_chart(fig, use_container_width=True, key=f"persona_compare_{key_suffix}")


def _render_split_tab(df_centroids_g, df_profile_g, split_label, split_col="gender"):
    n_personas = df_centroids_g["persona"].nunique()
    render_centroid_table(df_centroids_g, split_label=split_label, split_col=split_col)
    st.divider()
    if df_profile_g is not None and not df_profile_g.empty:
        tab1, tab2 = st.tabs(["Deep-dive", "Comparison"])
        with tab1:
            render_persona_profiles(df_profile_g, n_personas, split_label=split_label)
        with tab2:
            render_comparison(df_profile_g, n_personas, split_label=split_label)
    else:
        st.warning(f"Persona profile data not found for this {split_col}.")


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    st.header("Personas")
    st.caption(
        "We develop cluster-based respondent profiles (i.e. archetypes) based on the "
        "profiles of formative research participants. This approach is used in "
        "user-centred design and marketing to create representative \"customer personas\" "
        "that help teams empathise with their target audience and make informed design decisions."
    )
    st.markdown("""
### Methodology
Personas were derived using **k-modes clustering**, a variant of k-means adapted for
categorical data. Unlike k-means, k-modes uses modes (most frequent values) rather than
means as cluster centres, and measures dissimilarity by the number of mismatching
categories between observations — making it well-suited to survey responses.

**Clustering is run separately within each group of a split** (gender, or region) so
that within-group variation drives the clusters rather than the split variable itself.

**Clustering variables:** age, occupation, religion, and life goals (plus gender itself,
when splitting by region — gender isn't dropped there since it varies within a region).

**Configuration:** 3 clusters per group, initialised using the Cao method (which selects
starting centroids based on category frequency distributions to reduce sensitivity to
random starting points), with 5 independent runs to improve stability. Results are fully
reproducible (fixed random seed).

**Output:** Each persona represents the modal respondent within a cluster — the
combination of attribute values that best characterises that group. Cluster size (N and
weighted N) is shown for each persona. Individual-level data is not stored or displayed.
    """)
    st.markdown("")

    # ── Split selector: Gender or Region ────────────────────────────────────────
    split_choice = st.radio("Split personas by", ["Gender", "Region"], horizontal=True)
    split_col = "gender" if split_choice == "Gender" else "region"

    if split_col == "gender":
        df_centroids_s = load_personas_centroids_by_gender()
        df_profile_s   = load_personas_profile_by_gender()
        df_elbow       = load_personas_elbow()
        label_map      = GENDER_DISPLAY
        missing_msg    = _MISSING
    else:
        df_centroids_s = load_personas_centroids_by_region()
        df_profile_s   = load_personas_profile_by_region()
        df_elbow       = load_personas_elbow_by_region()
        label_map      = {}
        missing_msg = (
            "Pre-aggregated region-split persona data not found. "
            "Run `python -m pipeline.run_pipeline --pages personas` (from pipeline_output/) "
            "to generate it, then upload personas_centroids_by_region.csv / "
            "personas_profile_by_region.csv / personas_elbow_by_region.csv to Drive and "
            "wire the file IDs into src/data_loader.py."
        )

    if df_centroids_s is None or df_centroids_s.empty:
        st.warning(missing_msg)
        return

    # ── Elbow plot ────────────────────────────────────────────────────────────
    if df_elbow is not None and not df_elbow.empty:
        with st.expander("Elbow plot — choosing number of clusters", expanded=False):
            render_elbow_plot(df_elbow, split_col=split_col, key=f"elbow_plot_{split_col}")

    # ── Split tabs ────────────────────────────────────────────────────────────
    groups_in_data = df_centroids_s[split_col].unique().tolist()
    if split_col == "region":
        # Prefer the canonical North-East/North-West/South-South/Mid-South order
        groups_in_data = [g for g in REGIONS if g in groups_in_data] + \
                         [g for g in groups_in_data if g not in REGIONS]
    tab_labels = [tr(label_map.get(g, g)) for g in groups_in_data]
    tabs = st.tabs(tab_labels)

    for tab, group_label in zip(tabs, groups_in_data):
        with tab:
            c_sub = df_centroids_s[df_centroids_s[split_col] == group_label].copy()
            p_sub = (
                df_profile_s[df_profile_s[split_col] == group_label].copy()
                if df_profile_s is not None else None
            )
            _render_split_tab(c_sub, p_sub, group_label, split_col=split_col)
