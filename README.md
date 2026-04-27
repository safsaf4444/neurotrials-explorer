Neurotrials Explorer

A Streamlit dashboard for exploring neuro-related clinical trial trends 
using data from ClinicalTrials.gov.

https://neurotrials-explorer-qg2apd6zdy97bggcchbx6o.streamlit.app/

Fetches and visualises 26,998 registered clinical trials across 7 
neurological conditions — stroke, Alzheimer's disease, Parkinson's disease, 
multiple sclerosis, ALS, migraine, and epilepsy.

Filters: condition · phase · recruitment status · year range

Charts: trials per year · phase breakdown · sponsor type · 
intervention type · recruitment status over time · condition summary

Tech stack:
Python · requests · pandas · Streamlit · Plotly Express
Data source: ClinicalTrials.gov API v2

{
How to run locally

git clone https://github.com/safsaf4444/neurotrials-explorer
cd neurotrials-explorer
conda create -n neurotrials python=3.11
conda activate neurotrials
pip install -r requirements.txt
python src/fetch.py
python src/clean.py
streamlit run app.py
}

What I learned

- How to paginate through a REST API using cursor-based tokens
- How to handle nested JSON and flatten it into a clean pandas DataFrame
- How to build reactive Streamlit dashboards with filtered data
- How to structure a data project using ETL separation of concerns
- Real data quality issues — missing phases, inconsistent sponsor names, 
  unpublished completed trials

## Limitations

- Not all trials are registered on ClinicalTrials.gov
- Completed status does not mean results were published
- Sponsor name normalisation is imperfect
- Trials tagged under multiple conditions appear in multiple counts

## Built by

Safa S. · Second-year Biomedical Sciences · Royal Holloway, 
University of London
