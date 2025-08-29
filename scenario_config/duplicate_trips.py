import pandas as pd
import zipfile
import os

if not os.path.exists("C:\VSCodeProjects\matsim-idf\data_sources\gtfs_idf_duplicate_trips"):
    os.makedirs("C:\VSCodeProjects\matsim-idf\data_sources\gtfs_idf_duplicate_trips")

INPUT_ZIP = "data_sources\gtfs_idf\IDFM-gtfs.zip"
OUTPUT_ZIP = "data_sources\gtfs_idf_duplicate_trips\IDFM-gtfs.zip"
CHUNK_SIZE = 10240
NUM_CHUNKS = 47


def duplicate_trips_chunk(trips_chunk):
    # Create containers for duplicated rows
    new_trips = []

    # Duplicate each trip
    for trip_id in trips_chunk["trip_id"]:
        # Duplicate row
        new_trip_row = trips_chunk[trips_chunk["trip_id"] == trip_id].copy()
        new_trip_row["trip_id"] = f"{trip_id}_copy"
        new_trips.append(new_trip_row)

    # Concatenate original and duplicated data
    duplicated_trips_chunk = pd.concat([trips_chunk] + new_trips, ignore_index=True)

    return duplicated_trips_chunk


# Create container for trips chunks
trips_records = []

# Open zip file
with zipfile.ZipFile(INPUT_ZIP, "r") as archive:
    with archive.open("trips.txt") as file:
        trips_csv = pd.read_csv(file, dtype = str, chunksize = CHUNK_SIZE)

        # Duplicate each chunk separately
        for counter_chunks, trips_chunk in enumerate(trips_csv):
            duplicated_trips_chunk = duplicate_trips_chunk(trips_chunk)

            if len(duplicated_trips_chunk) > 0:
                trips_records.append(duplicated_trips_chunk)
            
            print(f"Processed {counter_chunks+1} chunks out of {NUM_CHUNKS}")

# Concatenate chunks into one file
all_trips = pd.concat(trips_records)

# Write everything back into a new zip
with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
    # Replace modified files
    z.writestr("trips.txt", all_trips.to_csv(index=False))

    # Copy all other files from original zip unchanged
    with zipfile.ZipFile(INPUT_ZIP, "r") as original_zip:
        for item in original_zip.infolist():
            if item.filename not in ["trips.txt"]:
                z.writestr(item, original_zip.read(item.filename))

print(f"Finished writing into {OUTPUT_ZIP}")
