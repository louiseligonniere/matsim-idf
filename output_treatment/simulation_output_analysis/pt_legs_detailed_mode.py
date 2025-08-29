import pandas as pd

"""
This module is used to retrieve the detailed mode of PT legs outputed by simulation MATSim.
"""

# Read files
df_pt = pd.read_csv("output_treatment\simulation_output_analysis\csv\output_legs.csv", sep=";")
df_links = pd.read_csv("output_treatment\simulation_output_analysis\csv\output_links.csv", sep=";", dtype=str)

# Filter PT legs
df_pt = df_pt[df_pt["mode"] == "pt"]

# Select relevant columns to prepare merge
df_pt = df_pt[["person", "trip_id", "trav_time", "distance", "start_link", "end_link"]]
df_links = df_links[["link", "modes"]].rename(columns={"link":"start_link", "modes":"mode"})

# Merge pt legs and links info 
df_pt = pd.merge(df_pt, df_links, how="left", on="start_link")

# Rename links modes
df_pt["mode"] = df_pt["mode"].map({"bus,car,car_passenger":"bus",
                                   "rail":"rail",
                                   "artificial,stopFacilityLink,subway":"subway",
                                   "artificial,stopFacilityLink,tram":"tram",
                                   "artificial,bus,stopFacilityLink":"bus",
                                   "artificial,rail,stopFacilityLink":"rail"})

### Stats on legs by detailed mode

# Number of legs
legs_by_mode = df_pt["mode"].value_counts().reset_index()
legs_by_mode.columns = ["mode", "count"]

# Add nb of trips shares
total_legs = legs_by_mode["count"].sum()
legs_by_mode["share (%)"] = (legs_by_mode["count"] / total_legs).round(4) * 100

# Convert trav_time to timedelta
df_pt["trav_time"] = pd.to_timedelta(df_pt["trav_time"])

# Compute travel time share per mode
travel_time_by_mode = df_pt.groupby("mode")["trav_time"].sum().dt.total_seconds()
total_travel_time = df_pt["trav_time"].sum().total_seconds()
travel_time_share = (travel_time_by_mode / total_travel_time).round(4) * 100
travel_time_share = travel_time_share.rename_axis("mode")

# Compute distance share per mode
distance_by_mode = (df_pt.groupby("mode")["distance"].sum() / 1000).round().astype(int)
total_distance = df_pt["distance"].sum() / 1000
distance_share = (distance_by_mode / total_distance).round(4) * 100
distance_by_mode = distance_by_mode.rename_axis("mode")
distance_share = distance_share.rename_axis("mode")

# Add to the stats df
legs_by_mode = pd.merge(legs_by_mode, travel_time_share, on="mode", how="left").rename(columns={"trav_time": "travel time share (%)"})
legs_by_mode = pd.merge(legs_by_mode, distance_by_mode, on="mode", how="left").rename(columns={"distance": "distance (km)"})
legs_by_mode = pd.merge(legs_by_mode, distance_share, on="mode", how="left").rename(columns={"distance": "distance share (%)"})

# Add a row for total
total = legs_by_mode.drop(columns="mode").sum()
total["mode"] = "total"

legs_by_mode = pd.concat([legs_by_mode.sort_values(by="mode"), pd.DataFrame([total])])

# Display
print("Stats on PT legs per mode (detailed):")
print(legs_by_mode)
