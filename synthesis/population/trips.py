from tqdm import tqdm
import itertools
import numpy as np
import pandas as pd

"""
This stage attaches trips to the synthetic population using synth.pop.matched. 
Each trip is duplicated as many times as the number of persons in the synthetic population to which it was matched.
Departure times are diversified using a random offset in [-30min, +30min] (with constraint to keep all departure times after midnight).
The same offset is added to each trip in a person's activity chain.
Returns: df_trips = matched person_id + trips variables.
"""

def configure(context):
    context.stage("synthesis.population.matched")
    context.config("random_seed")

    hts = context.config("hts")
    context.stage("data.hts.selected", alias = "hts")

def execute(context):
    # Load data
    df_trips = context.stage("hts")[2]

    # Duplicate with synthetic persons
    df_matching = context.stage("synthesis.population.matched")
    df_trips = df_trips.rename(columns = { "person_id": "hts_id" })
    df_trips = pd.merge(df_matching, df_trips, on = "hts_id")
    df_trips = df_trips.sort_values(by = ["person_id", "trip_id"])

    # Define trip index
    df_count = df_trips.groupby("person_id").size().reset_index(name = "count")
    df_trips["trip_index"] = np.hstack([np.arange(count) for count in df_count["count"].values])
    df_trips = df_trips.sort_values(by = ["person_id", "trip_index"])

    # Diversify departure times
    random = np.random.RandomState(context.config("random_seed"))
    counts = df_trips[["person_id"]].groupby("person_id").size().reset_index(name = "count")["count"].values

    interval = df_trips[["person_id", "departure_time"]].groupby("person_id").min().reset_index()["departure_time"].values # First departure time of each person
    interval = np.minimum(1800.0, interval) # The interval for the offset must be +/- 30 min (=1800 s) OR less if first departure time is less than 30 min after midnight
    # Eg: if first departure time is just 5min after midnight, we restrict the deviation we add to max 5min

    offset = random.random_sample(size = (len(counts), )) * interval * 2.0 - interval # Random offset in [-interval, +interval] for each person
    offset = np.repeat(offset, counts) # Duplicate the offset so that it is added to each trip of the activity chain for each person

    df_trips["departure_time"] += offset
    df_trips["arrival_time"] += offset
    df_trips["departure_time"] = np.round(df_trips["departure_time"])
    df_trips["arrival_time"] = np.round(df_trips["arrival_time"])

    assert (df_trips["departure_time"] >= 0.0).all()
    assert (df_trips["arrival_time"] >= 0.0).all()

    return df_trips[[
        "person_id", "trip_index",
        "departure_time", "arrival_time",
        "preceding_purpose", "following_purpose",
        "is_first_trip", "is_last_trip",
        "trip_duration", "activity_duration",
        "mode"
    ]]
