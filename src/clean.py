import pandas as pd   # the data table library
import json           # reads JSON files from disk
import os             # creates folders, checks paths

# ── Constants ──────────────────────────────────────────────────────────────

RAW_DATA_DIR     = "data/raw"              # where the JSON files live
CLEANED_DATA_DIR = "data/cleaned"          # where the CSV will be saved
OUTPUT_FILE      = "data/cleaned/trials_clean.csv"  # final output path

# ── Layer 3: Functions ──────────────────────────────────────────────────────

def load_all_studies():
    """
    Reads every JSON file in data/raw/ into one flat list.
    Adds a _condition field to each study so we know which
    condition it came from after we merge everything together.
    """

    all_studies = []   # start with an empty list

    for filename in os.listdir(RAW_DATA_DIR):
        # os.listdir() gives us every filename in the folder as a string
        # we loop through each one

        if not filename.endswith(".json"):
            continue
            # 'continue' skips the rest of this loop iteration
            # and jumps straight to the next filename
            # this ignores any non-JSON files in the folder

        condition = filename.replace(".json", "")
        # strips the .json extension to get the condition name
        # e.g. "alzheimers_disease.json" -> "alzheimers_disease"

        filepath = os.path.join(RAW_DATA_DIR, filename)
        # os.path.join() builds a file path correctly for any OS
        # on Windows: "data/raw\\alzheimers_disease.json"
        # safer than manually writing "data/raw/" + filename

        with open(filepath, "r", encoding="utf-8") as f:
            raw = json.load(f)

        if isinstance(raw, list):
            studies = raw
        else:
            studies = raw.get("studies", [])

        for study in studies:
            study["_condition"] = condition
            # adds a new key to every trial dict
            # the underscore prefix means "we added this, it didn't come from the API"
            all_studies.append(study)
            # .append() adds one item (the study dict) to the list
            # this is correct here — one dict per slot, not a list of lists

    print(f"Loaded {len(all_studies)} total studies from {RAW_DATA_DIR}/")
    return all_studies


def extract_fields(study):
    """
    Takes one raw trial dict (deeply nested JSON)
    and returns a flat dict with only the fields we need.
    Each key here becomes one column in the final CSV.
    """

    # safely navigate the nested structure using .get() at every level
    # passing {} as default means the next .get() won't crash on a missing key

    proto       = study.get("protocolSection", {})
    id_mod      = proto.get("identificationModule", {})
    status_mod  = proto.get("statusModule", {})
    design_mod  = proto.get("designModule", {})
    sponsor_mod = proto.get("sponsorCollaboratorsModule", {})
    arms_mod    = proto.get("armsInterventionsModule", {})

    # ── Phase extraction ──
    phases = design_mod.get("phases", [])
    phase  = phases[0] if phases else None
    # phases is a list — take the first item if it exists
    # if the list is empty, use None instead of crashing with IndexError

    # ── Start year extraction ──
    start_date_struct = status_mod.get("startDateStruct", {})
    start_date        = start_date_struct.get("date")
    # start_date might be "2021-03-15" or "2021-03" or None
    # we'll parse the year from it in the cleaning step

    # ── Sponsor extraction ──
    lead_sponsor = sponsor_mod.get("leadSponsor", {})
    sponsor_name = lead_sponsor.get("name")
    sponsor_type = lead_sponsor.get("class")
    # class field contains: INDUSTRY / ACADEMIC / NIH / OTHER

    # ── Intervention type ──
    interventions     = arms_mod.get("interventions", [])
    intervention_type = interventions[0].get("type") if interventions else None
    # interventions is a list — take the type from the first one if it exists

    # ── Return a flat dict ──
    return {
        "nct_id"           : id_mod.get("nctId"),
        "title"            : id_mod.get("briefTitle"),
        "status"           : status_mod.get("overallStatus"),
        "phase"            : phase,
        "start_date"       : start_date,
        "sponsor_name"     : sponsor_name,
        "sponsor_type"     : sponsor_type,
        "intervention_type": intervention_type,
        "condition"        : study.get("_condition"),
        "has_results"      : study.get("hasResults", False),
    }


def clean_dataframe(df):
    """
    Takes a raw DataFrame of extracted fields
    and normalises, parses, and fills missing values.
    Returns the cleaned DataFrame.
    """

    # ── Normalise text columns to consistent capitalisation ──
    df["status"]           = df["status"].str.upper().str.strip()
    df["sponsor_type"]     = df["sponsor_type"].str.upper().str.strip()
    df["intervention_type"]= df["intervention_type"].str.upper().str.strip()

    # .str.upper()  — capitalise every character
    # .str.strip()  — remove leading/trailing whitespace
    # both are vectorised — applied to every row at once, no loop needed

    # ── Parse start year from date string ──
    df["start_year"] = (
        pd.to_datetime(df["start_date"], errors="coerce")
          .dt.year
    )
    # pd.to_datetime() converts strings like "2021-03-15" into datetime objects
    # errors="coerce" means: if a date string can't be parsed, use NaT (Not a Time)
    # .dt.year extracts just the year as an integer (e.g. 2021)

    # ── Normalise phase labels ──
    phase_map = {
        "PHASE1" : "Phase 1",
        "PHASE2" : "Phase 2",
        "PHASE3" : "Phase 3",
        "PHASE4" : "Phase 4",
        "NA"     : "N/A",
        "EARLY_PHASE1": "Phase 1",
    }
    df["phase"] = df["phase"].str.upper().map(phase_map).fillna("Unknown")
    # .map(dict) replaces each value using the dictionary as a lookup table
    # any value not found in the map becomes NaN
    # .fillna("Unknown") catches anything the map missed

    # ── Drop rows where critical fields are missing ──
    before = len(df)
    df = df.dropna(subset=["nct_id", "title"])
    after  = len(df)
    print(f"Dropped {before - after} rows missing nct_id or title")

    # ── Fill remaining missing values ──
    df["status"]            = df["status"].fillna("UNKNOWN")
    df["sponsor_type"]      = df["sponsor_type"].fillna("OTHER")
    df["intervention_type"] = df["intervention_type"].fillna("Unknown")
    df["sponsor_name"]      = df["sponsor_name"].fillna("Unknown")
    df["start_year"]        = df["start_year"].fillna(0).astype(int)
    # .astype(int) converts float years (e.g. 2021.0) to clean integers (2021)
    # must fillna first — you cannot convert NaN to int

    # ── Remove duplicate trials ──
    before = len(df)
    df = df.drop_duplicates(subset=["nct_id"])
    after  = len(df)
    print(f"Removed {before - after} duplicate nct_id rows")

    return df


def save_cleaned(df):
    """
    Creates the output folder if needed and saves the DataFrame as CSV.
    """

    os.makedirs(CLEANED_DATA_DIR, exist_ok=True)
    # creates data/cleaned/ if it doesn't already exist
    # exist_ok=True — don't crash if it already exists

    df.to_csv(OUTPUT_FILE, index=False)
    # saves the DataFrame to CSV
    # index=False — don't write the row numbers (0,1,2...) as a column

    print(f"Saved {len(df)} rows to {OUTPUT_FILE}")


# ── Layer 4: Main ───────────────────────────────────────────────────────────

def main():
    """
    Runs the full cleaning pipeline in order:
    load → extract → build dataframe → clean → save
    """

    # Step 1 — load all raw JSON into one list
    all_studies = load_all_studies()

    # Step 2 — extract fields from every study using list comprehension
    records = [extract_fields(s) for s in all_studies]
    # [f(x) for x in list] is a list comprehension
    # applies extract_fields() to every item in all_studies
    # returns a new list of flat dicts — one per trial
    # faster and cleaner than a for loop with .append()

    # Step 3 — build a DataFrame from the list of flat dicts
    df = pd.DataFrame(records)
    print(f"DataFrame shape before cleaning: {df.shape}")
    # df.shape returns (rows, columns) as a tuple

    # Step 4 — clean the DataFrame
    df = clean_dataframe(df)
    print(f"DataFrame shape after cleaning:  {df.shape}")

    # Step 5 — save
    save_cleaned(df)


if __name__ == "__main__":
    main()