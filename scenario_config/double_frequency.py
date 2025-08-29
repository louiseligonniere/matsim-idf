import pandas as pd
import zipfile
import os

if not os.path.exists("C:\VSCodeProjects\matsim-idf\data_sources\gtfs_idf_double_frequency"):
    os.makedirs("C:\VSCodeProjects\matsim-idf\data_sources\gtfs_idf_double_frequency")

INPUT_ZIP = "data_sources\gtfs_idf_duplicate_trips\IDFM-gtfs.zip"
OUTPUT_ZIP = "data_sources\gtfs_idf_double_frequency\IDFM-gtfs.zip"
CHUNK_SIZE = 10240
NUM_CHUNKS = 1060
DEFAULT_OFFSET = 60 * 60 # default offset to use for routes that have one unique departure (60 minutes)


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


def duplicate_stoptimes_chunk(stoptimes_chunk, trips_df):
    # Merge to bring route_id into stoptimes
    stoptimes_chunk = stoptimes_chunk.merge(trips_df, on="trip_id", how="left")

    # Create containers for duplicated rows
    new_stoptimes = []

    # Loop on routes (in the given chunk)
    for route_id in stoptimes_chunk["route_id"].unique():
        offset = DEFAULT_OFFSET

        # Filter trips for the given route
        route_stoptimes = stoptimes_chunk[stoptimes_chunk["route_id"] == route_id].copy()

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
            newtrip_stoptimes[col] = format_timedelta_column(pd.to_timedelta(newtrip_stoptimes[col]) + pd.to_timedelta(offset))
        new_stoptimes.append(newtrip_stoptimes)

    # Concatenate original and duplicated data
    duplicated_stoptimes_chunk = pd.concat([stoptimes_chunk] + new_stoptimes, ignore_index=True)

    duplicated_stoptimes_chunk = duplicated_stoptimes_chunk.drop(columns=["route_id"])

    return duplicated_stoptimes_chunk


# Read trips.txt once outside loop to get route_id
with zipfile.ZipFile("data_sources\gtfs_idf\IDFM-gtfs.zip", "r") as archive:
    with archive.open("trips.txt") as trips_file:
        trips_df = pd.read_csv(trips_file, dtype=str)[["trip_id", "route_id"]]
print("Finished reading trips to get route IDs")

# Create container for stop times chunks
stoptimes_records = []

# Open zip file
with zipfile.ZipFile(INPUT_ZIP, "r") as archive:
    with archive.open("stop_times.txt") as file:
        stoptimes_csv = pd.read_csv(file, dtype = str, chunksize = CHUNK_SIZE)
        # Duplicate each chunk separately
        for counter_chunks, stoptimes_chunk in enumerate(stoptimes_csv):
            duplicated_stoptimes_chunk = duplicate_stoptimes_chunk(stoptimes_chunk, trips_df)

            if len(duplicated_stoptimes_chunk) > 0:
                stoptimes_records.append(duplicated_stoptimes_chunk)
            
            print(f"Processed {counter_chunks+1} chunks out of {NUM_CHUNKS}")

# Concatenate chunks into one file
all_stoptimes = pd.concat(stoptimes_records)

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
