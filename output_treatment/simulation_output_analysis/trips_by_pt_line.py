import os
import pandas as pd
import xml.etree.ElementTree as ET
import zipfile

"""
This module is used to analyze the pt_transit events outputed by MATSim :
- First, it converts the event file (OUTPUT_PATH/extracted_files/output_events.xml), 
from xml to csv. It creates one csv file : converted_pttransit_events.csv (events of type pt_transit). 
It is saved in OUTPUT_PATH/extracted_files
- Then, it produces a table of number of passengers per selected PT line
Stat tables are saved into OUTPUT_PATH.
"""

SELECTED_LINES = ["A", "B", "C", "D", "E",
                  "H", "J", "K", "L", "N", "P", "R", "U", "V"]

GTFS_ZIP = "data_sources\gtfs_idf\IDFM-gtfs.zip"

OUTPUT_PATH = "output_treatment/results"

#### EVENTS ANALYSIS ####

def xml_to_csv_events():
    """
    Reads xml events file (output_events.xml) and searchs for pt_transit events. 
    Returns df_events. 
    """
    print("Reading pt_transit events...")

    # Parse the XML file
    tree = ET.parse(r'C:\VSCodeProjects\matsim-idf-yvelines0.05\output_treatment\results\extracted_files\output_events.xml')
    root = tree.getroot()
        
    # Empty df for events
    df_events = pd.DataFrame(columns=['time', 'type', 'person', 'facility', 'link', 'x', 'y', 'actType', 'legMode', 'computationalRoutingMode', 
                                        'distance', 'mode', 'vehicle', 'networkMode', 'relativePosition', 'line', 'route', 'accessStop', 'egressStop', 
                                        'vehicleDepartureTime', 'travelDistance'])

    progress = 0

    for event in root.iter("event"):
        if event.get("type") == "pt_transit":
            attrib = event.attrib.copy()
            
            # Append in the events df
            df_events.loc[len(df_events)] = attrib

            # Progress status
            if progress%2000 == 0:
                print(f"Reading pt_transit events... Progress: {progress}/...")
            progress+=1

    # Add a unique events id
    df_events["event_id"] = range(len(df_events))

    print("Reading pt_transit events: done!")

    return df_events


#### CREATE CSV ####

os.makedirs("%s/extracted_files" % OUTPUT_PATH, exist_ok=True)

# Pt transit events
df_events = xml_to_csv_events()
df_events.to_csv("%s/extracted_files/converted_pttransit_events.csv" % OUTPUT_PATH)

print(f"Converted file for pt_transit events saved into {OUTPUT_PATH}/extracted_files/converted_pttransit_events.csv")

#### TABLE OF NB OF PASSENGERS PER SELECTED LINE ####

# Read routes.txt to get route_id corresponding to selected lines
with zipfile.ZipFile(GTFS_ZIP, "r") as archive:
    with archive.open("routes.txt") as routes_file:
        routes_df = pd.read_csv(routes_file, dtype=str)[["route_id", "route_short_name"]]
        selected_routes = routes_df[routes_df["route_short_name"].isin(SELECTED_LINES)]
        selected_routes = selected_routes.rename(columns={"route_id": "line"})
        selected_routes_id = set(selected_routes["line"])

df_events = pd.read_csv("%s\extracted_files\converted_pttransit_events.csv" % OUTPUT_PATH)

selected_events = df_events[df_events["line"].isin(selected_routes_id)]

selected_events = selected_events.merge(selected_routes, on="line", how="left")

trips_by_line = selected_events["route_short_name"].value_counts().reset_index()
trips_by_line.columns = ["line", "count"]

total = trips_by_line.drop(columns="line").sum()
total["line"] = "total"

trips_by_line = pd.concat([trips_by_line.sort_values(by="line"), pd.DataFrame([total])])

# Display
print("Stats on trips per PT line:")
print(trips_by_line)

# Save to CSV
trips_by_line.to_csv(
    "%s/trips_by_line.csv" % OUTPUT_PATH,
    sep=";",
    index=False
)

# Export to LaTeX table
with open("%s/trips_by_line.tex" % OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(
        trips_by_line.to_latex(
            index=False,   # avoid row indices in the table
            float_format="%.2f",  # format floats with 2 decimals
            caption="Statistics on trips per selected line",
            label="tab:trips_by_line",
            escape=False   # allow LaTeX special chars in column names
        )
    )

print(f".csv table + .tex table saved into {OUTPUT_PATH}")