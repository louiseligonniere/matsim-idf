import pandas as pd

"""
This module is used to analyse legs outputed by simulation MATSim.
Using the csv files (saved in output_treatment/simulation_output_analysis/csv), it produces some 
stats on the share of legs (absolute, distance, travel time) made using each mode.
"""

# Read files
df_legs = pd.read_csv("output_treatment/simulation_output_analysis/csv/output_legs.csv", sep=";")

### Legs by mode

# Number of legs
legs_by_mode = df_legs["mode"].value_counts().reset_index()
legs_by_mode.columns = ["mode", "count"]

# Add nb of legs shares
total_legs = legs_by_mode["count"].sum()
legs_by_mode["share (%)"] = (legs_by_mode["count"] / total_legs).round(4) * 100

# Convert trav_time to timedelta
df_legs["trav_time"] = pd.to_timedelta(df_legs["trav_time"])

# Compute travel time share per mode
travel_time_by_mode = df_legs.groupby("mode")["trav_time"].sum().dt.total_seconds()
total_travel_time = df_legs["trav_time"].sum().total_seconds()
travel_time_share = (travel_time_by_mode / total_travel_time).round(4) * 100

# Compute distance share per mode
distance_by_mode = (df_legs.groupby("mode")["distance"].sum() / 1000).round().astype(int)
total_distance = df_legs["distance"].sum() / 1000
distance_share = (distance_by_mode / total_distance).round(4) * 100

# Add to the stats df
legs_by_mode = pd.merge(legs_by_mode, travel_time_share, on="mode", how="left").rename(columns={"trav_time": "travel time share (%)"})
legs_by_mode = pd.merge(legs_by_mode, distance_by_mode, on="mode", how="left").rename(columns={"distance": "distance (km)"})
legs_by_mode = pd.merge(legs_by_mode, distance_share, on="mode", how="left").rename(columns={"distance": "distance share (%)"})

# Add a row for car total
car_total = legs_by_mode[legs_by_mode["mode"].isin(["car", "car_passenger"])].drop(columns="mode").sum()
car_total["mode"] = "car_total"

legs_by_mode = pd.concat([legs_by_mode, pd.DataFrame([car_total])]).sort_values(by="mode")

# Add a row for total
total = legs_by_mode[-legs_by_mode["mode"].isin(["car_total"])].drop(columns="mode").sum()
total["mode"] = "total"

legs_by_mode = pd.concat([legs_by_mode, pd.DataFrame([total])])

# Display
print("Stats on legs per mode:")
print(legs_by_mode)
