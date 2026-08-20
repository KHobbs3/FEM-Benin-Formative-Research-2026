import re

import pandas as pd
import streamlit as st

# ── Pre-aggregated loaders (safe: no PII) ──────────────────────────────────
#
# Same drive.google.com pattern as niger_app's data_loader.py: each CSV
# lives in Drive (shared with the family_planning workspace domain, same
# access level as niger_app's files) and is referenced by its shareable
# file ID rather than a local path, so the app doesn't depend on a data/
# folder being present wherever it's deployed (e.g. Streamlit Community
# Cloud). Get a file's ID from its "Share" link:
# https://drive.google.com/file/d/<FILE_ID>/view

def _load(file_id, **kwargs):
    return pd.read_csv("https://drive.google.com/uc?export=download&id=" + file_id, **kwargs)


# ── Statements / drivers-barriers ──────────────────────────────────────────

def load_statement_labels():
    return _load("10jVtq1Xn1SY2eD60jHqyjo7fbaMjY3DZ")


def load_statements_heatmap():
    return _load("1vIEmR83mIl2er-GqHaZyOM6Iz3xazutk", index_col=0)


# ── Access page ─────────────────────────────────────────────────────────────

def load_access_stockouts():
    return _load("11cM8scy_qwXIW5mHwJvwWm5mSLdiei4x", index_col=0)


def load_access_stockout_responses():
    return _load("1WjeDCOpS62rhTUTdeC9EUxntI7mqmtBY", index_col=0)


def load_access_travel():
    return _load("13coFVaRMukaQhIwGyvqdAFOQO_DIwl-0", index_col=0)


def load_access_affordability():
    return _load("1PV4jHHk17BdeXTwfax8Ap1oyKl5zE1Cy", index_col=0)


def load_access_composite():
    return _load("1bPiVhCZv1JCh-P1piPPSaZal43WMlQss", index_col=0)


# ── Radio page ───────────────────────────────────────────────────────────────

def clean_column_name(col):
    col = re.sub(r'^\d+_\d+_', '', col)
    col = re.sub(r'_+\d+$', '', col)
    col = col.replace('_', ' ').strip().title()
    return col


def load_radio_by_station():
    df = _load("1OkbqLDi68k0cPYqdPorA_sn2IPfTHrLU")  # Benin_question_table_by_station_26_08_19.csv
                                                       # "1b6F3K6AaetMr86TnuYtX458ikOC7cUo2") - 26_08_18 version
    df.set_index(df.columns[0], inplace=True)
    return df


def load_radio_by_state():
    df = _load("1pxlnnsHf0CylXGh76y_52fUoP3HbOkwm")  # Benin_question_table_by_state_26_08_19.csv
                                                       # "1NttFCzxCcloaK5CFIaVXQiL_pYsV7VYe") - 26_08_18 version
    df.set_index(df.columns[0], inplace=True)
    return df


# ── Family planning page ──────────────────────────────────────────────────────

def load_fp_funnel():
    return _load("1EvaLIhWspeJIx72P5O0rksWX8lvaztMm", index_col=0)


def load_fp_timing():
    return _load("1SeG8LFTFL5wFXSALSQi0dDQUw4mwQ5JB", index_col=0)


def load_fp_methods():
    return _load("1Mc2a1hfVdJUYkUyFNP55m0Lj7AFDXQFB", index_col=0)


def load_fp_reason_use():
    return _load("1XciS8pzP5fogsQDiXZRl5hqPTPHq2mK_", index_col=0)


def load_fp_intent():
    return _load("1a8zdFhQ_9cWMRcOu8KSNEAM70fUHF0m5", index_col=0)


def load_fp_nonuse_reasons():
    return _load("1Lc6ZF6f-5HvgS4bU3txy0fAs-q03s1P4", index_col=0)


# ── Personality page ──────────────────────────────────────────────────────────

def load_personality_life_goals():
    return _load("1GgrO8VRfAhIqK9ny1gcO5VlfSV1CSqWN", index_col=0)


def load_personality_goals_achievable():
    return _load("1jST2cLtTUtxAz5-63ULGaJ4SXPXvjbCq", index_col=0)


def load_personality_role_models():
    return _load("1KXrKKqhZr8okAULwmDVegVcmrrhGrwcJ", index_col=0)


def load_personality_likeable_traits():
    return _load("1WTGuqdOUs0JhnLEnX3HbDSoEFkwc-RHi", index_col=0)


def load_personality_forming_beliefs():
    return _load("1aE2dtrGr9PxBEinBaFH-QB0D7uJ7kGjo", index_col=0)


def load_personality_decision_confident():
    return _load("1NdldUUYWCN3cRp0TeW0dV5Xb_V0fSb5G", index_col=0)


def load_personality_wellbeing():
    return _load("1I6nJfVUqZZkW6f3O2cC-XssPMySq0hwk", index_col=0)


# ── Respondent profile page ───────────────────────────────────────────────────

def load_respondents_profile():
    return _load("1jZRKIA1VNxi2VTJ29c5UG-RVfedtFrmq", index_col=0)


# ── Personas page ─────────────────────────────────────────────────────────────

def load_personas_centroids():
    return _load("1Y1Xk4r50AKKGHRzBh0YB7fZnbnKSva7C", index_col=0)


def load_personas_profile():
    return _load("1ReOtnqa0kbQ3g0HMyx0aS93W3xRcocYk", index_col=0)


def load_personas_centroids_by_gender():
    return _load("1SNQjIStYoM_kMPmQTAn-wdyI-IaJzNRA", index_col=0)


def load_personas_profile_by_gender():
    return _load("1qVwe9OsB_x4I_zPxFgreDUbdJMJZEjyV", index_col=0)


def load_personas_elbow():
    return _load("1ld9MIa9rUFEiftaAEBCbjiQ3sRN0e09E", index_col=0)


# ── Drivers & barriers ──────────────────────────────────────────────────────
# Unlike the pages above, this doesn't come from pipeline_output/'s ETL
# modules -- it's produced by table_analysis/03_driver_barrier_table_w_counts.ipynb
# into data/3_final/Benin_drivers-barriers_table_*.csv, then uploaded to
# Drive by hand (not wired into run_pipeline.py). Re-upload the latest dated
# file and paste its file ID here after re-running that notebook.
def load_drivers_barriers():
    return _load("1c8P4w_I320QgQ1lbqzqLXd-ZsFQN7kLD")  # Benin_drivers-barriers_table_26_08_18.csv


# ── Phone Pulse pages -- NOT COLLECTED FOR BENIN ───────────────────────────
# Niger's app has a whole second survey wave (phone pulse follow-up) with
# ~25 loaders here. Benin has no such data yet (see 05_settlements_radio_coverage.ipynb,
# which prepares radio-station labels *for* a future phone pulse survey, but
# no phone pulse responses exist yet). All Phone Pulse pages in app.py are
# stubbed rather than wired to loaders that would always return None.


# ── Shared parsing helpers (used by drivers/barriers) ──────────────────────

def parse_subgroup_prevalence(cell_str):
    result = {}
    if pd.isna(cell_str) or str(cell_str).strip() == "":
        return result
    for line in str(cell_str).split("\n"):
        line = line.strip()
        match = re.match(r"^(.+?):\s*([\d.]+)%", line)
        if match:
            result[match.group(1).strip()] = float(match.group(2))
    return result


def parse_statements(cell_str):
    if pd.isna(cell_str) or str(cell_str).strip() == "":
        return None, {}
    lines = [l.strip() for l in str(cell_str).split("\n") if l.strip()]
    statement = None
    percentages = {}
    for line in lines:
        match = re.match(r"^(.+?):\s*([\d.]+)%", line)
        if match:
            percentages[match.group(1).strip()] = float(match.group(2))
        elif statement is None and "%" not in line:
            statement = line
    return statement, percentages


PRIORITY_ORDER = {"Very high": 4, "High": 3, "Medium": 2, "Low": 1}


def get_priority_sort_key(p):
    return PRIORITY_ORDER.get(str(p).strip(), 0)


USER_CATEGORY_LABELS = {
    "user":        "Current user",
    "nonuser":     "Non-user",
    "future_user": "Future user",
    "past_user":   "Past user",
}

AGE_GROUPS  = ["16-20", "21-30", "31-45"]
# NOTE: the drivers/barriers table (table_analysis/03_driver_barrier_table_w_counts.ipynb)
# splits on the raw, unprocessed 'gender' column ("Femme Nyɔnu"/"Homme Sunnu"),
# not the cleaned "Femme"/"Homme" used in respondents_profile.csv etc. -- verified
# against the actual GENDER: columns in Benin_drivers-barriers_table_*.csv.
GENDERS     = ["Femme Nyɔnu", "Homme Sunnu"]
URBAN_RURAL = ["Rural", "Semi-urbain", "Urbain"]  # verified against the actual weighted data's urban_rural values
