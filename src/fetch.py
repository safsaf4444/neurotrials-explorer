import requests   #makes HTTPcalls to API
import json       #parses JSON responses from API
import time    # used for sleep between API calls to avoid rate limits - pause between requests
import os   # checks for file existance

#-- Constants ---

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"  # API endpoint

# 7 neuro conditions we want to study
NEURO_CONDITIONS = [
    "stroke",
    "Alzheimer's disease",
    "Parkinson's disease",
    "multiple sclerosis",
    "ALS",
    "epilepsy",
    "migraine"  
]

PAGE_SIZE = 100 # no of trials per page (max allowed = 1000)
SLEEP_TIME = 0.5  # seconds to wait between API calls to avoid rate limits
MAX_RETRIES = 3  # max retries for failed API calls
RAW_DATA_DIR = "data/raw"  # directory to save raw JSON responses

#-- Functions ---

def fetch_trials(condition, page_token=None):
    """
    Fetches one page of trials for a given condition
    Returns the raw response dict.
    """

    #--- Build query parameters
    params = {
        "query.cond" : condition,   # filter by condition
        "pageSize" : PAGE_SIZE,   # number of results per page
        "format" : "json"   # response format
    }

       # if we have a page token add it to get the next page
    # the 'if page_token' checks if the value is not None
    if page_token:
        params["pageToken"] = page_token   # add token to params dict

    # retry loop - tries up to max retries times
    for attempt in range(MAX_RETRIES):
        try:
            # make the API call with the specified parameters
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()  # raise an error for bad status codes
            return response.json()  # convert JSON text to Python dict and return it
        
        except requests.exceptions.RequestException as e:
            # 'except' catches any error that happened in the 'try' block
            # 'requests.exceptions.RequestException' is the parent class
            # of all requests errors (timeout, connection error, 404 etc)
            # 'as e' gives the error a nickname so we can print it

            print(f"Attempt {attempt + 1} failed: {e}") # print error message with attempt number

            if attempt < MAX_RETRIES - 1:  # if we have retries left
                wait_time = 2 ** attempt  # exponential backoff: wait longer after each failure
                # 2**0 = 1 sec, 2**1 = 2 secs, 2**2 = 4 secs
                # '**' is Python's power/exponent operator
                print(f"Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)  # pause execution for wait_time seconds
            else:
                # last attempt failed, return None to indicate failure
                raise # re-raise the last exception to be handled by the caller

def fetch_condition(condition):
    """
    Fetches ALL pages of trials for one condition.
    Returns a list of all trial dicts.
    """

    all_studies = []    # empty list - we'll add trials to this
    page_token = None   # start with no token (first page)
    page_number = 1     # just for our print messages

    print(f"Fetching: {condition}")
    # f-string again - {condition} gets replaced with the actual condition name

    while True:
        # 'while True' is an infinite loop - runs forever UNTIL we break out
        # we break out when there's no nextPageToken

        print(f"  Page {page_number}...", end="")
        # end="" means don't print a newline after this
        # so the next print goes on the same line

        data = fetch_trials(condition, page_token)
        # calls our function above, passing the condition and current token

        studies = data.get("studies", [])
        # '.get()' is a safer way to access a dict key
        # if "studies" key doesn't exist, returns [] instead of crashing
        # plain data["studies"] would crash if the key was missing

        all_studies.extend(studies)
        # '.extend()' adds all items from one list into another list
        # different from '.append()' which would add the list as one item

        print(f" {len(studies)} trials")
        # prints how many trials we got on this page

        page_token = data.get("nextPageToken")
        # get the next page token from the response
        # if there's no nextPageToken the response won't have this key
        # .get() returns None by default when key is missing

        if not page_token:
            break
        # 'if not page_token' means 'if page_token is None or empty'
        # 'break' exits the while loop immediately

        page_number += 1    # increment page counter (same as page_number = page_number + 1)
        time.sleep(SLEEP_TIME)  # pause between pages

    print(f"  Total: {len(all_studies)} trials for {condition}")
    return all_studies  # return the complete list

def save_condition(condition, studies):
    """
    Saves the list of trials to a JSON file in data/raw/ directory.
    """

    #turn the condition name into a safe filename
    # ex @Alzheimer's disease -> alzheimers_disease.json
    filename = condition.lower() # makes lowercase
    filename = filename.replace(" ", "_") # replaces spaces with underscores
    filename = filename.replace("'", "") # removes apostrophes
    # reassigns filename with moded version

    filepath = f"{RAW_DATA_DIR}/{filename}.json" # full path to save file

    with open(filepath, "w") as f:  # open file for writing
        json.dump(studies, f, indent=2)  # write the list of studies as JSON with indentation
            # saves the list of trials as a JSON file
    print(f"  Saved {len(studies)} trials to {filepath}") # print how many trials we saved and where

#-- Main execution ---

def main():
    """
    Main function to fetch and save trials for all conditions.
    """
    # create the raw data directory if it doesn't exist
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    # 'os.makedirs' creates a folder and any parent folders needed
    # 'exist_ok=True' means don't crash if the folder already exists

    # loop through every condition in our list
    for condition in NEURO_CONDITIONS:
        # 'for x in list' iterates through each item
        # each loop 'condition' becomes the next item in CONDITIONS

        studies = fetch_condition(condition)    # fetch all pages
        save_condition(condition, studies)      # save to disk
        print()     # print a blank line between conditions
        time.sleep(1)   # extra pause between conditions


# this block only runs if you execute this file directly
# it won't run if another file imports fetch.py
if __name__ == "__main__":
    main()