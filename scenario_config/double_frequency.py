import pandas as pd
import zipfile
import os

os.makedirs("C:\VSCodeProjects\matsim-idf-yvelines0.05\data_sources\gtfs_idf_double_frequency_rertransilien", exist_ok=True)

INPUT_ZIP = "data_sources\gtfs_idf\IDFM-gtfs.zip"
OUTPUT_ZIP = "data_sources\gtfs_idf_double_frequency_rertransilien\IDFM-gtfs.zip"
CHUNK_SIZE = 10240
NUM_CHUNKS_TRIPS = 47
NUM_CHUNKS_STOPS = 1060
DEFAULT_OFFSET = 60 * 60 # default offset to use for routes that have one unique departure (60 minutes)

# SELECTED_LINES = [] # to keep all lines
SELECTED_LINES = ["A", "B", "C", "D", "E",
                  "H", "J", "K", "L", "N", "P", "R", "U", "V"]


def duplicate_trips_chunk(trips_chunk, selected_routes_id):
    # Create containers for duplicated rows
    new_trips = []

    # Duplicate each trip (for selected lines)
    for trip_id in trips_chunk["trip_id"]:
        if trips_chunk[trips_chunk["trip_id"] == trip_id]["route_id"].isin(selected_routes_id).item():
            # Duplicate row
            new_trip_row = trips_chunk[trips_chunk["trip_id"] == trip_id].copy()
            new_trip_row["trip_id"] = f"{trip_id}_copy"
            new_trips.append(new_trip_row)

    # Concatenate original and duplicated data
    duplicated_trips_chunk = pd.concat([trips_chunk] + new_trips, ignore_index=True)

    return duplicated_trips_chunk


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


def duplicate_stoptimes_chunk(stoptimes_chunk, selected_routes_id):
    # Create containers for duplicated rows
    new_stoptimes = []

    # Loop on routes (in the given chunk)
    for (route_id, direction_id), group in stoptimes_chunk.groupby(["route_id", "direction_id"]):
        if route_id in selected_routes_id: # duplicate only for selected lines
            offset = DEFAULT_OFFSET

            # Filter trips for the given route
            route_stoptimes = group.copy()

            # Create table of first departure times for each trip
            first_dep = route_stoptimes.groupby("trip_id")["departure_time"].min().reset_index()
            first_dep = first_dep.sort_values("departure_time").reset_index(drop=True)

            # Loop on trips for the given route
            for i in range(len(first_dep) - 1):
                trip_id = first_dep.loc[i, "trip_id"]

                # Calculate offset to shift every departure of this trip
                first_dep_time = pd.to_timedelta(first_dep.loc[i, "departure_time"])
                next_dep_time = pd.to_timedelta(first_dep.loc[i+1, "departure_time"])
                offset = (next_dep_time - first_dep_time) / 2 # offset = middle of given trip and following trip

                if offset == pd.to_timedelta(0): # if both departures at same time, we add a 10 min offset
                    offset = pd.to_timedelta(10 * 60, unit='s')

                # Copy stoptimes of this trip
                newtrip_stoptimes = route_stoptimes[route_stoptimes["trip_id"] == trip_id].copy()
                
                # New trip_id
                newtrip_stoptimes["trip_id"] = trip_id + "_copy"
                
                # Shift times
                for col in ["arrival_time", "departure_time"]:
                    newtrip_stoptimes[col] = format_timedelta_column(pd.to_timedelta(newtrip_stoptimes[col]) + offset)
                
                new_stoptimes.append(newtrip_stoptimes)

            # Add a departure for the last departure (with the same offset as the previous one / or default_offset if it is the only departure for the given route)
            last_trip_id = first_dep.iloc[-1]["trip_id"]
            newtrip_stoptimes = route_stoptimes[route_stoptimes["trip_id"] == last_trip_id].copy()
            newtrip_stoptimes["trip_id"] = last_trip_id + "_copy"
            for col in ["arrival_time", "departure_time"]:
                newtrip_stoptimes[col] = format_timedelta_column(pd.to_timedelta(newtrip_stoptimes[col]) + pd.to_timedelta(offset, unit='s'))
            new_stoptimes.append(newtrip_stoptimes)

    # Concatenate original and duplicated data
    duplicated_stoptimes_chunk = pd.concat([stoptimes_chunk] + new_stoptimes, ignore_index=True)

    return duplicated_stoptimes_chunk



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


# Read trips.txt once outside loop to get route_id
with zipfile.ZipFile(INPUT_ZIP, "r") as archive:
    with archive.open("trips.txt") as trips_file:
        trips_df = pd.read_csv(trips_file, dtype=str)[["trip_id", "route_id", "direction_id"]]

print("Finished reading trips to get correspondance between trips and route IDs")


#############################
###### DUPLICATE TRIPS ######
#############################

# Create container for trips chunks
trips_records = []

# Open zip file
with zipfile.ZipFile(INPUT_ZIP, "r") as archive:
    with archive.open("trips.txt") as file:
        trips_csv = pd.read_csv(file, dtype = str, chunksize = CHUNK_SIZE)

        # Duplicate each chunk separately
        for counter_chunks, trips_chunk in enumerate(trips_csv):
            duplicated_trips_chunk = duplicate_trips_chunk(trips_chunk, selected_routes_id)

            if len(duplicated_trips_chunk) > 0:
                trips_records.append(duplicated_trips_chunk)
            
            print(f"Processed {counter_chunks+1} chunks out of {NUM_CHUNKS_TRIPS}")

# Concatenate chunks into one file
all_trips = pd.concat(trips_records)


#############################
###### DUPLICATE STOPS ######
#############################

# Create container for stop times chunks
stoptimes_records = []

# Open zip file
with zipfile.ZipFile(INPUT_ZIP, "r") as archive:
    with archive.open("stop_times.txt") as file:
        stoptimes_csv = pd.read_csv(file, dtype = str, chunksize = CHUNK_SIZE)

        # The cut between two chunks can happen inside lines from a same route
        # To avoid it, we save lines of the last route from each chunk and concatenate it at the beginning of the following chunk
        last_route = pd.DataFrame()

        # Process each chunk separately
        for counter_chunks, stoptimes_chunk in enumerate(stoptimes_csv):            
            # Merge to bring route_id into stoptimes
            stoptimes_chunk = stoptimes_chunk.merge(trips_df, on="trip_id", how="left")

            # Add previous last route to current chunk
            stoptimes_chunk_to_fix = pd.concat([last_route, stoptimes_chunk])

            # Save last route from current chunk
            routes = stoptimes_chunk_to_fix["route_id"].unique()
            last_id = routes[len(routes)-1]
            last_route = stoptimes_chunk_to_fix[stoptimes_chunk_to_fix["route_id"] == last_id]

            # Remove last route from current chunk
            stoptimes_chunk_to_fix = stoptimes_chunk_to_fix[stoptimes_chunk_to_fix["route_id"] != last_id]
            
            # Apply the processing function
            if len(stoptimes_chunk_to_fix)>0:
                duplicated_stoptimes_chunk = duplicate_stoptimes_chunk(stoptimes_chunk_to_fix, selected_routes_id)
                stoptimes_records.append(duplicated_stoptimes_chunk.drop(columns=["route_id"]))
            
            print(f"Processed {counter_chunks+1} chunks out of {NUM_CHUNKS_STOPS}")
        
        # Process last route from last chunk
        last_route_fixed = duplicate_stoptimes_chunk(last_route, selected_routes_id)
        stoptimes_records.append(last_route_fixed.drop(columns=["route_id", "direction_id"]))

# Concatenate chunks into one file
all_stoptimes = pd.concat(stoptimes_records)


################################
###### SAVE MODIFICATIONS ######
################################

# Write everything back into a new zip
with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
    # Replace modified files
    z.writestr("trips.txt", all_trips.to_csv(index=False))
    z.writestr("stop_times.txt", all_stoptimes.to_csv(index=False))

    # Copy all other files from original zip unchanged
    with zipfile.ZipFile(INPUT_ZIP, "r") as original_zip:
        for item in original_zip.infolist():
            if item.filename not in ["trips.txt", "stop_times.txt"]:
                z.writestr(item, original_zip.read(item.filename))

print(f"Finished writing into {OUTPUT_ZIP}")


