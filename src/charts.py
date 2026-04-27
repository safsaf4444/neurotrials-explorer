import plotly.express as px   # high-level chart library
import pandas as pd            # needed for any data prep inside chart functions

# ── How this file works ─────────────────────────────────────────────────────
#
# Each function in this file:
#   1. takes a filtered DataFrame as its only argument
#   2. does any grouping/aggregation needed to prepare the data
#   3. returns a Plotly figure object
#
# Functions never display anything themselves — they just return the figure.
# Streamlit will call fig with st.plotly_chart() in app.py.
# This makes every chart independently testable.

# ── Chart 1 — Trial count by year ───────────────────────────────────────────

def chart_trials_by_year(df):
    """
    Line chart showing how many trials were registered each year,
    with one line per neuro condition.
    """

    # step 1 — filter out rows where start_year is 0 (unparseable dates)
    df = df[df["start_year"] > 1990]
    # boolean indexing — keeps only rows where start_year is greater than 1990
    # this removes the sentinel 0 values and any implausibly old records

    # step 2 — group and count
    yearly = (
        df.groupby(["start_year", "condition"])
          .size()
          .reset_index(name="count")
    )
    # .groupby(["start_year", "condition"]) — groups rows by every unique
    #   combination of (year, condition)
    # .size() — counts how many rows are in each group
    # .reset_index(name="count") — flattens the result back to a DataFrame
    #   and names the count column "count"

    fig = px.line(
        yearly,
        x="start_year",
        y="count",
        color="condition",
        markers=True,
        title="Neuro clinical trials registered per year",
        labels={
            "start_year": "Year",
            "count": "Number of trials",
            "condition": "Condition",
        },
    )
    # px.line() — creates a line chart
    # x= — horizontal axis column
    # y= — vertical axis column
    # color= — creates one line per unique value in this column
    # markers=True — shows a dot at each data point on the line
    # labels={} — maps column names to display labels shown on axes and tooltips

    fig.update_layout(legend_title_text="Condition")
    # .update_layout() modifies chart appearance after creation
    # legend_title_text sets the title above the colour legend

    return fig


# ── Chart 2 — Phase breakdown ────────────────────────────────────────────────

def chart_phase_breakdown(df):
    """
    Grouped bar chart showing trial counts broken down by phase,
    one group of bars per condition.
    """

    phase_df = (
        df.groupby(["condition", "phase"])
          .size()
          .reset_index(name="count")
    )

    # define the order phases should appear in — most meaningful order
    phase_order = ["Phase 1", "Phase 2", "Phase 3", "Phase 4", "N/A", "Unknown"]

    fig = px.bar(
        phase_df,
        x="condition",
        y="count",
        color="phase",
        barmode="group",
        title="Trial phase breakdown by condition",
        labels={
            "condition": "Condition",
            "count": "Number of trials",
            "phase": "Phase",
        },
        category_orders={"phase": phase_order},
    )
    # px.bar() — creates a bar chart
    # barmode="group" — bars sit side by side, one per phase per condition
    # barmode="stack" would stack them on top of each other instead
    # category_orders= — controls the order colours and legend entries appear

    return fig


# ── Chart 3 — Sponsor type donut ─────────────────────────────────────────────

def chart_sponsor_type(df):
    """
    Donut chart showing the proportion of trials by sponsor type
    (Industry vs Academic vs Government vs Other).
    """

    sponsor_df = (
        df["sponsor_type"]
          .value_counts()
          .reset_index()
    )
    sponsor_df.columns = ["sponsor_type", "count"]
    # .value_counts() counts each unique sponsor_type value
    # .reset_index() turns the result back into a flat DataFrame
    # .columns = [...] renames the columns because value_counts().reset_index()
    #   gives awkward auto-generated column names

    fig = px.pie(
        sponsor_df,
        names="sponsor_type",
        values="count",
        hole=0.45,
        title="Trials by sponsor type",
        labels={"sponsor_type": "Sponsor type", "count": "Trials"},
    )
    # px.pie() — creates a pie or donut chart
    # names= — the column containing the slice labels
    # values= — the column containing the slice sizes
    # hole=0.45 — cuts a hole in the centre to make it a donut
    #   0 = full pie, 0.45 = donut, 1 = invisible

    fig.update_traces(textposition="inside", textinfo="percent+label")
    # .update_traces() modifies the data series appearance
    # textposition="inside" — puts labels inside the slices
    # textinfo="percent+label" — shows both % and the label name

    return fig


# ── Chart 4 — Intervention type ──────────────────────────────────────────────

def chart_intervention_type(df):
    """
    Horizontal bar chart showing the most common intervention types
    across all trials in the current filter selection.
    """

    intervention_df = (
        df["intervention_type"]
          .value_counts()
          .head(10)
          .reset_index()
    )
    intervention_df.columns = ["intervention_type", "count"]
    # .head(10) — takes only the top 10 most common types
    #   preventing the chart from becoming unreadable with rare types

    fig = px.bar(
        intervention_df,
        x="count",
        y="intervention_type",
        orientation="h",
        title="Top intervention types",
        labels={
            "intervention_type": "Intervention type",
            "count": "Number of trials",
        },
        color="count",
        color_continuous_scale="Blues",
    )
    # orientation="h" — makes the bars horizontal
    #   x and y swap roles: x is the value, y is the category
    # color="count" — colours each bar by its value
    # color_continuous_scale="Blues" — uses a blue gradient colour scale

    fig.update_layout(showlegend=False, yaxis={"categoryorder": "total ascending"})
    # showlegend=False — hides the colour scale legend (redundant here)
    # categoryorder="total ascending" — sorts bars from smallest to largest

    return fig


# ── Chart 5 — Recruitment status over time ───────────────────────────────────

def chart_recruitment_status(df):
    """
    Stacked bar chart showing how the mix of trial statuses
    has changed year by year.
    """

    df = df[df["start_year"] > 1990]

    status_df = (
        df.groupby(["start_year", "status"])
          .size()
          .reset_index(name="count")
    )

    # keep only the most meaningful statuses to avoid clutter
    key_statuses = ["COMPLETED", "RECRUITING", "ACTIVE_NOT_RECRUITING",
                    "TERMINATED", "WITHDRAWN", "UNKNOWN"]
    status_df = status_df[status_df["status"].isin(key_statuses)]
    # boolean indexing with .isin() — keeps only rows where status
    # is one of the values in the key_statuses list

    fig = px.bar(
        status_df,
        x="start_year",
        y="count",
        color="status",
        barmode="stack",
        title="Trial recruitment status by start year",
        labels={
            "start_year": "Year",
            "count": "Number of trials",
            "status": "Status",
        },
    )
    # barmode="stack" — bars are stacked on top of each other
    # each colour represents a different status
    # shows both volume and composition changing over time

    return fig


# ── Chart 6 — Condition comparison ───────────────────────────────────────────

def chart_condition_summary(df):
    """
    Horizontal bar chart giving a quick overview of total trial
    counts per condition — useful as a top-level summary card.
    """

    condition_df = (
        df.groupby("condition")
          .size()
          .reset_index(name="count")
          .sort_values("count", ascending=True)
    )
    # .sort_values("count", ascending=True) — sorts from fewest to most
    # ascending=True puts the shortest bar at the bottom
    # which reads naturally on a horizontal bar chart

    fig = px.bar(
        condition_df,
        x="count",
        y="condition",
        orientation="h",
        title="Total trials by condition",
        labels={"condition": "Condition", "count": "Number of trials"},
        color="condition",
    )

    fig.update_layout(showlegend=False)

    return fig