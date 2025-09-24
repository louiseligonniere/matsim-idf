import pandas as pd
import zipfile
import os

os.makedirs("C:\VSCodeProjects\matsim-idf-yvelines0.05\data_sources\gtfs_idf_cap_traveltime_rertransilien", exist_ok=True)

INPUT_ZIP = "data_sources\gtfs_idf_double_frequency_rertransilien\IDFM-gtfs.zip"
OUTPUT_ZIP = "data_sources\gtfs_idf_cap_traveltime_rertransilien\IDFM-gtfs.zip"
CHUNK_SIZE = 10240
NUM_CHUNKS_STOPS = 1060
CAP = pd.Timedelta(minutes=2)

# SELECTED_LINES = [] # to keep all lines
SELECTED_LINES = ["A", "B", "C", "D", "E",
                  "H", "J", "K", "L", "N", "P", "R", "U", "V"]


def format_timedelta_column(series):
    """Convert timedelta or string series into HH:MM:SS string format"""
    # Ensure everything is timedelta
    series = pd.to_timedelta(series, errors="coerce")
    return series.apply(
        lambda x: f"{int(x.total_seconds() // 3600):02d}:"
                  f"{int((x.total_seconds() % 3600) // 60):02d}:"
                  f"{int(x.total_seconds() % 60):02d}"
        if pd.notnull(x) else ""
    )


def cap_travel_times(stoptimes_trip, cap=CAP):
    if stoptimes_trip["trip_id"].isin(selected_trips_id).iloc[0]:

        stoptimes_trip["arrival_time"] = pd.to_timedelta(stoptimes_trip["arrival_time"])
        stoptimes_trip["departure_time"] = pd.to_timedelta(stoptimes_trip["departure_time"])

        stoptimes_trip = stoptimes_trip.sort_values("arrival_time").copy()

        for i in range(len(stoptimes_trip) - 1):
            travel_time = stoptimes_trip.iloc[i+1]["arrival_time"] - stoptimes_trip.iloc[i]["departure_time"]

            if travel_time > CAP:
                # Compute how much we need to shift the following stops backward
                excess = travel_time - CAP

                # Apply shift to the next stop onward
                stoptimes_trip.loc[stoptimes_trip.index[i+1:], ["arrival_time", "departure_time"]] -= excess

        stoptimes_trip["arrival_time"] = format_timedelta_column(stoptimes_trip["arrival_time"])
        stoptimes_trip["departure_time"] = format_timedelta_column(stoptimes_trip["departure_time"])

    return stoptimes_trip


##################################
###### GET PREPARATORY INFO ######
##################################

# Read routes.txt to get route_id corresponding to selected lines
with zipfile.ZipFile(INPUT_ZIP, "r") as archive:
    with archive.open("routes.txt") as routes_file:
        routes_df = pd.read_csv(routes_file, dtype=str)[["route_id", "route_short_name"]]
        if SELECTED_LINES != []:
            selected_routes = routes_df[routes_df["route_short_name"].isin(SELECTED_LINES)]
        else:
            selected_routes = routes_df
        selected_routes_id = set(selected_routes["route_id"])

print("Finished reading routes to get selected lines")


# Read trips.txt once outside loop to get trip_id corresponding to selected lines
with zipfile.ZipFile(INPUT_ZIP, "r") as archive:
    with archive.open("trips.txt") as trips_file:
        trips_df = pd.read_csv(trips_file, dtype=str)[["trip_id", "route_id", "direction_id"]]
        if SELECTED_LINES != []:
            selected_trips = trips_df[trips_df["route_id"].isin(selected_routes_id)]
        else:
            selected_trips = trips_df
        selected_trips_id = set(selected_trips["trip_id"])

print("Finished reading trips to get selected lines")


#############################
###### CAP TRAVEL TIME ######
#############################

# Create container for stop times chunks
stoptimes_records = []

with zipfile.ZipFile(INPUT_ZIP, "r") as archive:
    with archive.open("stop_times.txt") as file:
        stoptimes_csv = pd.read_csv(file, dtype = str, chunksize=CHUNK_SIZE)

        # The cut between two chunks can happen inside lines from a same trip
        # To avoid it, we save lines of the last trip from each chunk and concatenate it at the beginning of the following chunk
        last_trip = pd.DataFrame()

        # Process each chunk separately
        for counter_chunks, stoptimes_chunk in enumerate(stoptimes_csv):
            COLUMNS = stoptimes_chunk.columns

            # Add previous last trip to current chunk
            stoptimes_chunk_to_fix = pd.concat([last_trip, stoptimes_chunk])

            # Save last trip from current chunk
            trips = stoptimes_chunk_to_fix["trip_id"].unique()
            last_id = trips[len(trips)-1]
            last_trip = stoptimes_chunk_to_fix[stoptimes_chunk_to_fix["trip_id"] == last_id]

            # Remove last trip from current chunk
            stoptimes_chunk_to_fix = stoptimes_chunk_to_fix[stoptimes_chunk_to_fix["trip_id"] != last_id]
            
            # Apply the processing function
            if len(stoptimes_chunk_to_fix)>0:
                stoptimes_chunk_fixed = stoptimes_chunk_to_fix.groupby("trip_id", group_keys=False)[COLUMNS].apply(cap_travel_times, include_groups=True)
                stoptimes_records.append(stoptimes_chunk_fixed)
            
            print(f"Processed {counter_chunks+1} chunks out of {NUM_CHUNKS_STOPS}")
        
        # Process last trip from last chunk
        last_trip_fixed = last_trip.groupby("trip_id", group_keys=False)[COLUMNS].apply(cap_travel_times, include_groups=True)
        stoptimes_records.append(last_trip_fixed)

# Concatenate chunks into one file
all_stoptimes = pd.concat(stoptimes_records)


################################
###### SAVE MODIFICATIONS ######
################################

# Write everything back into a new zip
with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
    # Replace modified files
    z.writestr("stop_times.txt", all_stoptimes.to_csv(index=False))

    # Copy all other files from original zip unchanged
    with zipfile.ZipFile(INPUT_ZIP, "r") as original_zip:
        for item in original_zip.infolist():
            if item.filename not in ["stop_times.txt"]:
                z.writestr(item, original_zip.read(item.filename))

print(f"Finished writing into {OUTPUT_ZIP}")

