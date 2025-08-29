import pandas as pd
import zipfile
import os

if not os.path.exists("C:\VSCodeProjects\matsim-idf\data_sources\gtfs_idf_duplicate_stops"):
    os.makedirs("C:\VSCodeProjects\matsim-idf\data_sources\gtfs_idf_duplicate_stops")

INPUT_ZIP = "data_sources\gtfs_idf_duplicate_trips\IDFM-gtfs.zip"
OUTPUT_ZIP = "data_sources\gtfs_idf_duplicate_stops\IDFM-gtfs.zip"
OFFSET = 5 * 60  # 5 minutes in seconds
CHUNK_SIZE = 10240
NUM_CHUNKS = 1060


def time_to_seconds(t):
    h, m, s = map(int, t.split(":"))
    return h * 3600 + m * 60 + s


def seconds_to_time(s):
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{int(h):02}:{int(m):02}:{int(sec):02}"


def duplicate_stoptimes_chunk(stoptimes_chunk):
    # Create containers for duplicated rows
    new_stoptimes = []

    # Duplicate each trip
    for trip_id in stoptimes_chunk["trip_id"].unique():
        # Duplicate and shift stop times
        new_stoptimes_rows = stoptimes_chunk[stoptimes_chunk["trip_id"] == trip_id].copy()
        new_stoptimes_rows["trip_id"] = trip_id + "_copy"

        for col in ["arrival_time", "departure_time"]:
            new_stoptimes_rows[col] = new_stoptimes_rows[col].apply(
                lambda t: seconds_to_time(time_to_seconds(t) + OFFSET)
            )

        new_stoptimes.append(new_stoptimes_rows)

    # Concatenate original and duplicated data
    duplicated_stoptimes_chunk = pd.concat([stoptimes_chunk] + new_stoptimes, ignore_index=True)

    return duplicated_stoptimes_chunk


# Create container for stop times chunks
stoptimes_records = []

# Open zip file
with zipfile.ZipFile(INPUT_ZIP, "r") as archive:
    with archive.open("stop_times.txt") as file:
        stoptimes_csv = pd.read_csv(file, dtype = str, chunksize = CHUNK_SIZE)

        # Duplicate each chunk separately
        for counter_chunks, stoptimes_chunk in enumerate(stoptimes_csv):
            duplicated_stoptimes_chunk = duplicate_stoptimes_chunk(stoptimes_chunk)

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
