import os
import pandas as pd
import xml.etree.ElementTree as ET
import zipfile

SELECTED_LINES = ["A", "B", "C", "D", "E",
                  "H", "J", "K", "L", "N", "P", "R", "U", "V"]

GTFS_ZIP = "data_sources\gtfs_idf\IDFM-gtfs.zip"

# Read routes.txt to get route_id corresponding to selected lines
with zipfile.ZipFile(GTFS_ZIP, "r") as archive:
    with archive.open("routes.txt") as routes_file:
        routes_df = pd.read_csv(routes_file, dtype=str)[["route_id", "route_short_name"]]
        selected_routes = routes_df[routes_df["route_short_name"].isin(SELECTED_LINES)]
        selected_routes = selected_routes.rename(columns={"route_id": "line"})
        selected_routes_id = set(selected_routes["line"])

df_events = pd.read_csv("output_treatment\simulation_output_analysis\csv\converted_output_events.csv")

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
