import streamlit as st        # turns this python script into a web dashboard
import pandas as pd            # handles our data table (the clean CSV)
from src.charts import (       # imports all 6 chart functions from our charts file
    chart_trials_by_year,      # line chart — trials registered per year
    chart_phase_breakdown,     # bar chart — phase 1/2/3/4 split
    chart_sponsor_type,        # donut chart — who funds these trials
    chart_intervention_type,   # bar chart — drug vs device vs other
    chart_recruitment_status,  # stacked bar — recruiting vs completed etc
    chart_condition_summary,   # bar chart — total trials per condition
)

# ────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# This must be the very first streamlit call in the file — before anything else
# layout="wide" uses the full browser width instead of a narrow centred column
# ────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="NeuroTrials Explorer",   # text shown in the browser tab
    page_icon="🧠",                      # emoji shown in the browser tab
    layout="wide",                       # full width layout
)

# ────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# @st.cache_data is a decorator — it wraps the function below it
# the first time load_data() is called, it reads the CSV from disk
# every time after that (e.g. when a filter changes) it returns the
# cached copy instantly without touching the disk again
# this makes the dashboard fast even with 27,000 rows
# ────────────────────────────────────────────────────────────────────────────

@st.cache_data
def load_data():
    return pd.read_csv("data/cleaned/trials_clean.csv")
    # pd.read_csv() reads a CSV file and returns it as a DataFrame
    # a DataFrame is like an Excel spreadsheet inside Python

df = load_data()   # df is the variable name — short for DataFrame, a common convention

# ────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# st.sidebar.X() places any widget into the left sidebar panel
# the sidebar is where all our filters live — keeps the main area clean
# ────────────────────────────────────────────────────────────────────────────

st.sidebar.title("🧠 NeuroTrials Explorer")
st.sidebar.markdown("Explore 27,000+ neuro clinical trials from ClinicalTrials.gov")
st.sidebar.divider()    # draws a horizontal dividing line — purely visual
st.sidebar.subheader("Filters")

# ── Filter 1: Condition ──────────────────────────────────────────────────────
# multiselect lets the user pick one or more options from a dropdown list
# df["condition"].dropna() removes any missing values before getting unique ones
# .unique() returns each condition name exactly once (no duplicates)
# .tolist() converts the result to a plain Python list
# sorted() sorts them alphabetically so they appear in order in the dropdown
# default=all_conditions means every condition is selected when the app loads

all_conditions = sorted(df["condition"].dropna().unique().tolist())
conditions = st.sidebar.multiselect(
    "Condition",               # label shown above the dropdown
    options=all_conditions,    # the list of options to choose from
    default=all_conditions,    # which ones are selected by default
)

# ── Filter 2: Year range ─────────────────────────────────────────────────────
# a range slider with two handles — the user drags them to set a start and end year
# df[df["start_year"] > 0] filters out rows where start_year is 0
# (0 is our sentinel value for trials whose date could not be parsed)
# int() converts numpy int64 to a plain Python int — st.slider requires this
# value=(2000, max_year) sets where the handles sit when the app first loads

min_year = int(df[df["start_year"] > 0]["start_year"].min())
max_year = int(df["start_year"].max())
years = st.sidebar.slider(
    "Start year range",
    min_value=min_year,          # leftmost position of the slider
    max_value=max_year,          # rightmost position of the slider
    value=(2000, max_year),      # default handle positions — a tuple (start, end)
)
# years is now a tuple e.g. (2000, 2026)
# years[0] is the left handle value, years[1] is the right handle value

# ── Filter 3: Recruitment status ─────────────────────────────────────────────
all_statuses = sorted(df["status"].dropna().unique().tolist())
statuses = st.sidebar.multiselect(
    "Recruitment status",
    options=all_statuses,
    default=all_statuses,
)

# ── Filter 4: Phase ──────────────────────────────────────────────────────────
all_phases = sorted(df["phase"].dropna().unique().tolist())
phases = st.sidebar.multiselect(
    "Phase",
    options=all_phases,
    default=all_phases,
)

# data source credit at the bottom of the sidebar
st.sidebar.divider()
st.sidebar.caption("Data source: ClinicalTrials.gov API v2")
st.sidebar.caption("Last fetched: April 2026")
# st.caption() renders small grey text — used for metadata and credits

# ────────────────────────────────────────────────────────────────────────────
# APPLY FILTERS
# boolean indexing — we pass a True/False condition inside square brackets
# pandas keeps only the rows where the condition is True
# & means AND — every condition must be satisfied for a row to be kept
# parentheses around each condition are REQUIRED — operator precedence rules
#
# .isin(list) — True for each row where the column value is in the list
# .between(a, b) — True for values between a and b inclusive
# | means OR — we use this to also keep rows where start_year is 0
#   (unparseable dates) so they still appear in the results table
# ────────────────────────────────────────────────────────────────────────────

filtered = df[
    (df["condition"].isin(conditions)) &
    (df["status"].isin(statuses)) &
    (df["phase"].isin(phases)) &
    (df["start_year"].between(years[0], years[1]) | (df["start_year"] == 0))
]
# filtered is now a smaller DataFrame containing only the rows
# that match every selected filter — this is what all the charts use

# ────────────────────────────────────────────────────────────────────────────
# MAIN PAGE HEADER
# st.title() renders the largest heading on the page
# st.markdown() renders text with markdown formatting (bold, italic, links etc)
# ────────────────────────────────────────────────────────────────────────────

st.title("NeuroTrials Explorer")
st.markdown(
    "Exploring clinical trial trends across **7 neurological conditions** "
    "using data from ClinicalTrials.gov. Filter by condition, phase, sponsor "
    "type, and year to explore the landscape."
)

# ────────────────────────────────────────────────────────────────────────────
# KPI METRIC CARDS
# st.columns(4) creates 4 equal-width columns side by side
# it returns 4 column objects — we unpack them into 4 variable names
# with col1: is a context manager — everything indented below
#   renders inside that column
# st.metric(label, value) renders a large KPI number card
# f"{number:,}" adds comma separators e.g. 26998 becomes "26,998"
# ────────────────────────────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total trials",
        value=f"{len(filtered):,}",    # len() counts the rows in the filtered DataFrame
    )
with col2:
    st.metric(
        label="Conditions selected",
        value=len(conditions),
    )
with col3:
    recruiting = len(filtered[filtered["status"] == "RECRUITING"])
    # filtered[filtered["status"] == "RECRUITING"] keeps only recruiting trials
    # len() counts how many rows that is
    st.metric(
        label="Currently recruiting",
        value=f"{recruiting:,}",
    )
with col4:
    completed = len(filtered[filtered["status"] == "COMPLETED"])
    st.metric(
        label="Completed",
        value=f"{completed:,}",
    )

st.divider()   # horizontal line separating the KPIs from the charts

# ────────────────────────────────────────────────────────────────────────────
# CHARTS
# st.plotly_chart(fig) renders a Plotly figure in the app
# use_container_width=True makes the chart fill its column's full width
# always include this — without it charts render at a fixed small default size
#
# we call each chart function from src/charts.py, passing the filtered DataFrame
# the function does all the grouping and aggregation, then returns a figure
# ────────────────────────────────────────────────────────────────────────────

# ── Row 1: trials over time + phase breakdown ─────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Trials registered per year")
    st.caption("How has neuro trial activity changed over time?")
    st.plotly_chart(chart_trials_by_year(filtered), use_container_width=True)

with col_b:
    st.subheader("Phase breakdown")
    st.caption("What proportion of trials are Phase 1 vs 2 vs 3?")
    st.plotly_chart(chart_phase_breakdown(filtered), use_container_width=True)

# ── Row 2: sponsor type + intervention type ───────────────────────────────────
col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Sponsor type")
    st.caption("Industry vs academic vs government funding")
    st.plotly_chart(chart_sponsor_type(filtered), use_container_width=True)

with col_d:
    st.subheader("Intervention type")
    st.caption("Drug vs device vs behavioural — what is being tested?")
    st.plotly_chart(chart_intervention_type(filtered), use_container_width=True)

# ── Row 3: recruitment status + condition summary ─────────────────────────────
col_e, col_f = st.columns(2)

with col_e:
    st.subheader("Recruitment status over time")
    st.caption("How has the recruiting / completed / terminated mix changed?")
    st.plotly_chart(chart_recruitment_status(filtered), use_container_width=True)

with col_f:
    st.subheader("Total trials by condition")
    st.caption("Which conditions have the most registered trials?")
    st.plotly_chart(chart_condition_summary(filtered), use_container_width=True)

st.divider()

# ────────────────────────────────────────────────────────────────────────────
# RESULTS TABLE
# shows the individual trial records matching the current filters
# st.subheader() renders an H2-size heading
# we select only the columns we want to display and rename them
#   .rename(columns={old_name: new_name}) renames specific columns
#   this does not modify the original filtered DataFrame
# st.dataframe() renders an interactive table — sortable and searchable
# hide_index=True hides the row number column on the left
# ────────────────────────────────────────────────────────────────────────────

st.subheader(f"Trial records — {len(filtered):,} results")
st.caption("Click any column header to sort. Use the search icon to filter within results.")

display_df = filtered[[
    "nct_id", "title", "condition", "status",
    "phase", "sponsor_name", "sponsor_type", "start_year",
]].rename(columns={
    "nct_id"       : "NCT ID",
    "title"        : "Title",
    "condition"    : "Condition",
    "status"       : "Status",
    "phase"        : "Phase",
    "sponsor_name" : "Sponsor",
    "sponsor_type" : "Sponsor type",
    "start_year"   : "Year",
})

st.dataframe(display_df, use_container_width=True, hide_index=True)

st.divider()

# ────────────────────────────────────────────────────────────────────────────
# DOWNLOAD BUTTON
# st.download_button() renders a button that triggers a file download
# data= is the file contents — filtered.to_csv() converts the DataFrame
#   to a CSV string in memory (not saved to disk) and passes it to the button
# file_name= is what the downloaded file will be called on the user's computer
# mime= tells the browser what kind of file this is ("text/csv" = CSV file)
# ────────────────────────────────────────────────────────────────────────────

st.download_button(
    label="Download filtered data as CSV",
    data=filtered.to_csv(index=False),     # index=False skips the row numbers
    file_name="neurotrials_filtered.csv",
    mime="text/csv",
)

st.divider()

# ────────────────────────────────────────────────────────────────────────────
# METHODS NOTE
# st.expander() creates a collapsible section
# content inside only shows when the user clicks to expand it
# good for methods, limitations, and credits — important but not primary
# st.markdown() inside renders full markdown formatting
# ────────────────────────────────────────────────────────────────────────────

with st.expander("About this data — limitations and methodology"):
    st.markdown("""
    **Data source:** ClinicalTrials.gov API v2, fetched April 2026.

    **Coverage:** 26,998 trials across 7 neurological conditions —
    stroke, Alzheimer's disease, Parkinson's disease, multiple sclerosis,
    ALS, migraine, and epilepsy.

    **How I built this:**
    The data was fetched using Python's `requests` library, paginating through
    the ClinicalTrials.gov API v2 endpoint with retry logic and exponential backoff.
    Cleaning was done with `pandas` — extracting nested JSON fields, normalising
    inconsistent values, and handling missing data. The dashboard was built with
    `Streamlit` and `Plotly Express`.

    **Known limitations:**
    - Not all clinical trials are registered on ClinicalTrials.gov.
    - Data quality varies by sponsor — older records are often incomplete.
    - A trial marked *Completed* does not mean results were published.
    - Sponsor name normalisation is imperfect — the same organisation may appear
      under slightly different names in different records.
    - Trials tagged under multiple conditions may appear in more than one
      condition's count.
    - Trials with unparseable start dates are shown with year = 0.

    **Built by:** Safa S. · Second-year Biomedical Sciences · Royal Holloway,
    University of London · [GitHub](https://github.com/safsaf4444)
    """)