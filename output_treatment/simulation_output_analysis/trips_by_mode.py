import pandas as pd

"""
This module is used to analyse trips outputed by simulation MATSim
Using the csv files (saved in output_treatment/simulation_output_analysis/csv), it produces some 
stats on the share of trips (absolute, distance, travel time) made using each mode.
"""

#### USEFUL STATS ####

# Read files
df_trips = pd.read_csv("output_treatment/simulation_output_analysis/csv/output_trips.csv", sep=";")

### Trips by mode

# Number of trips
trips_by_mode = df_trips["main_mode"].value_counts().reset_index()
trips_by_mode.columns = ["mode", "count"]

# Add nb of trips shares
total_trips = trips_by_mode["count"].sum()
trips_by_mode["share (%)"] = (trips_by_mode["count"] / total_trips).round(4) * 100

# Convert trav_time to timedelta
df_trips["trav_time"] = pd.to_timedelta(df_trips["trav_time"])

# Compute travel time share per mode
travel_time_by_mode = df_trips.groupby("main_mode")["trav_time"].sum().dt.total_seconds()
total_travel_time = df_trips["trav_time"].sum().total_seconds()
travel_time_share = (travel_time_by_mode / total_travel_time).round(4) * 100
travel_time_share = travel_time_share.rename_axis("mode")

# Compute distance share per mode
distance_by_mode = (df_trips.groupby("main_mode")["traveled_distance"].sum() / 1000).round().astype(int)
total_distance = df_trips["traveled_distance"].sum() / 1000
distance_share = (distance_by_mode / total_distance).round(4) * 100
distance_by_mode = distance_by_mode.rename_axis("mode")
distance_share = distance_share.rename_axis("mode")

# Add to the stats df
trips_by_mode = pd.merge(trips_by_mode, travel_time_share, on="mode", how="left").rename(columns={"trav_time": "travel time share (%)"})
trips_by_mode = pd.merge(trips_by_mode, distance_by_mode, on="mode", how="left").rename(columns={"traveled_distance": "distance (km)"})
trips_by_mode = pd.merge(trips_by_mode, distance_share, on="mode", how="left").rename(columns={"traveled_distance": "distance share (%)"})

# Add a row for car total
car_total = trips_by_mode[trips_by_mode["mode"].isin(["car", "car_passenger"])].drop(columns="mode").sum()
car_total["mode"] = "car_total"

trips_by_mode = pd.concat([trips_by_mode, pd.DataFrame([car_total])]).sort_values(by="mode")

# Add a row for total
total = trips_by_mode[-trips_by_mode["mode"].isin(["car_total"])].drop(columns="mode").sum()
total["mode"] = "total"

trips_by_mode = pd.concat([trips_by_mode, pd.DataFrame([total])])

# Display
print("Stats on trips per mode (principal):")
print(trips_by_mode)
