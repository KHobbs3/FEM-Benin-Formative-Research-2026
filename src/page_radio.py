import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.data_loader import load_radio_by_state, load_radio_by_station
import re
import glob
from src.fem_colours import FEM_ORANGE, FEM_BROWN, FEM_TAUPE, FEM_STEEL, FEM_NAVY, FEM_SCALE

# NOTE: Niger's version of this file hardcoded a STATION_STATE / STATE_ORDER /
# STATION_NAMES lookup for its ~24 stations. That data doesn't exist for
# Benin's ~30 stations (see the TODO(Benin) comment on STATION_STATE in
# pipeline_output/pipeline/etl_radio.py -- station-level coverage areas
# aren't reliably known per-station yet). Station display names are instead
# cleaned up from the .gpkg filename directly below, with no state annotation.
# The by-state view doesn't need this at all -- etl_radio.py's
# build_radio_table_by_state() groups by the respondent's own recorded
# province, not by station coverage.


def _station_display(station_id):
    """Clean up a station's .gpkg filename stem into a display name, e.g.
    '2026-01-29_155911_radio bénin culture_GW_50' -> 'Radio Bénin Culture'."""
    name = re.sub(r'^\d{4}-\d{2}-\d{2}_\d+_', '', str(station_id))
    name = re.sub(r'_GW_\d+$', '', name)
    return name.strip().title()


def parse_radio_cell(cell_str):
    """
    Parse cell string and extract label-value pairs.

    Expects format:
        Label1
        25.3
        Label2
        15.2
        ...

    Returns:
        {label: value} dict where value is numeric
    """
    result = {}
    if pd.isna(cell_str) or str(cell_str).strip() == "":
        return result

    text = str(cell_str)
    # Match: label, newline, number (with optional decimal) - NO % suffix
    pattern = re.findall(r"([^\n%]+?)\s*\n\s*([\d.]+)", text)

    for name, val in pattern:
        name = name.strip()
        # Filter out preference labels
        if re.search(r"sais pas|prefer not|préfère ne pas", name, re.IGNORECASE):
            continue
        result[name] = float(val)

    return result


def get_station_columns(df: pd.DataFrame) -> list:
    """
    Extract base station names from column headers.

    From columns like ["Station_A", "Station_A_n", "Station_A_wn", "Station_A_state"],
    returns ["Station_A", "Station_B", ...]
    """
    stations = set()
    for col in df.columns:
        # Remove suffixes to get base name
        if col.endswith("_state"):
            stations.add(col[:-6])  # Remove "_state"
        elif col.endswith("_wn"):
            stations.add(col[:-3])
        elif col.endswith("_n"):
            stations.add(col[:-2])
        else:
            stations.add(col)

    return sorted(list(stations))


def shorten_question(q):
    first = q.split("\n")[0].strip()
    if len(first) > 100:
        first = first[:100] + "..."
    return first


def render_heatmap(df: pd.DataFrame, question: str, metric_type: str = "pct",
                   min_threshold: float = 5,
                   is_state_level: bool = False):
    """
    Render heatmap for selected metric type.

    Args:
        df: DataFrame with columns like "Station", "Station_n", "Station_wn"
        question: Row index (question)
        metric_type: "pct" (prevalence %), "n" (raw count), or "wn" (weighted count)
        min_threshold: Minimum value to display
        is_state_level: Whether this is state-level data
    """
    row = df.loc[question]

    # Get base column names (stations or states)
    columns = get_station_columns(df)

    # Select appropriate column suffix based on metric
    if metric_type == "pct":
        col_suffix = ""
        colorbar_title = "Prevalence %"
        zmax = 100
    elif metric_type == "n":
        col_suffix = "_n"
        colorbar_title = "Raw Count"
        zmax = None
    else:  # wn
        col_suffix = "_wn"
        colorbar_title = "Weighted Count"
        zmax = None

    # Parse data for this metric
    columns_by_data = {}
    for col in columns:
        col_name = f"{col}{col_suffix}"
        if col_name in row.index:
            columns_by_data[col] = parse_radio_cell(row[col_name])
        else:
            columns_by_data[col] = {}

    # Get all unique answer labels above threshold
    all_labels = set()
    for d in columns_by_data.values():
        all_labels.update(k for k, v in d.items() if float(v) >= min_threshold)

    all_labels = sorted(all_labels)

    if not all_labels:
        threshold_type = "%" if metric_type == "pct" else "count"
        st.info(f"No data meets the minimum threshold of {min_threshold} {threshold_type}. Try lowering it.")
        return

    # Y-axis: answer labels (NO transformation)
    display_names = all_labels

    # X-axis: column display names
    if is_state_level:
        # For state-level, just use state names
        column_display_names = columns
    else:
        # For station-level, use cleaned-up filenames
        column_display_names = [_station_display(s) for s in columns]

    # Build matrix
    matrix, text_matrix = [], []
    for label in all_labels:
        row_vals = [columns_by_data[col].get(label, None) for col in columns]
        matrix.append(row_vals)

        # Format text for display
        if metric_type == "pct":
            text_matrix.append([f"{v:.0f}%" if v is not None else "" for v in row_vals])
        else:
            text_matrix.append([f"{v:.0f}" if v is not None else "" for v in row_vals])

    # Set dynamic zmax if needed
    if zmax is None:
        flat_vals = [v for row_vals in matrix for v in row_vals if v is not None]
        zmax = max(flat_vals) if flat_vals else 100

    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=column_display_names,
        y=display_names,
        colorscale=FEM_SCALE,
        text=text_matrix,
        texttemplate="%{text}",
        showscale=True,
        hoverongaps=False,
        zmin=0,
        zmax=zmax,
        colorbar=dict(title=colorbar_title, thickness=12, len=0.8),
    ))

    r_margin = 10
    fig.update_layout(
        height=max(320, len(all_labels) * 30 + 100),
        margin=dict(l=10, r=r_margin, t=10, b=80),
        xaxis=dict(side="bottom", tickangle=-35, tickfont=dict(size=11)),
        yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11),
    )
    st.plotly_chart(fig, use_container_width=True)


def render(df=None):
    st.header("Radio")

    # Toggle between station and state level
    view_level = st.radio("View by:", ["Station", "State"], horizontal=True)

    if view_level == "Station":
        df = load_radio_by_station()
    else:
        df = load_radio_by_state()

    if df is None:
        st.info("No radio data file found. Run `python -m pipeline.run_pipeline --pages radio` (from pipeline_output/) to generate it.")
        return

    questions = df.index.tolist()
    short_labels = [shorten_question(q) for q in questions]
    label_to_full = dict(zip(short_labels, questions))

    # Create columns for controls
    col1, col2, col3, col4 = st.columns([3, 1.2, 1.2, 1.2])

    with col1:
        selected_label = st.selectbox("Select question", short_labels)

    with col2:
        metric_options = {
            "Prevalence %": "pct",
            "Raw Count (N)": "n",
            "Weighted Count": "wn"
        }
        metric_display = st.selectbox(
            "Metric",
            list(metric_options.keys()),
            help="Switch between percentage, raw count, or weighted count"
        )
        metric_type = metric_options[metric_display]

    with col3:
        # Dynamic threshold based on metric
        if metric_type == "pct":
            min_threshold = st.slider("Min %", min_value=0, max_value=100, value=5, step=1)
        else:
            min_threshold = st.slider("Min count", min_value=0, max_value=500, value=0, step=10)


    selected_q = label_to_full[selected_label]
    st.caption(selected_q)
    render_heatmap(
        df,
        selected_q,
        metric_type,
        min_threshold,
        is_state_level=(view_level == "State")
    )
