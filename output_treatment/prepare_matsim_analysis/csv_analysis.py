import pandas as pd

"""
This module is used to analyse trips outputed by prepare MATSim pipeline (output_treatment/results/extracted_files/simulated_population.xml).
Using the csv files (saved in output_treatment/results/extracted_files), it produces some 
stats on the share of trips (absolute, distance, travel time) made using each mode.
"""

OUTPUT_PATH = "output_treatment/results"

#### USEFUL STATS ####

# Read files
df_population = pd.read_csv("%s/extracted_files/converted_population.csv" % OUTPUT_PATH)
df_activities = pd.read_csv("%s/extracted_files/converted_activities.csv" % OUTPUT_PATH)
df_trips = pd.read_csv("%s/extracted_files/converted_trips.csv" % OUTPUT_PATH)

### Trips by detailled mode

# Number of trips
trips_by_mode = df_trips["mode"].value_counts().reset_index()
trips_by_mode.columns = ["mode", "count"]

# Add nb of trips shares
total_trips = trips_by_mode["count"].sum()
trips_by_mode["share"] = (trips_by_mode["count"] / total_trips).round(4)

# Convert trav_time to timedelta
df_trips["trav_time"] = pd.to_timedelta(df_trips["trav_time"])

# Compute travel time share per mode
travel_time_by_mode = df_trips.groupby("mode")["trav_time"].sum().dt.total_seconds()
total_travel_time = df_trips["trav_time"].sum().total_seconds()
travel_time_share = (travel_time_by_mode / total_travel_time).round(4)

# Compute distance share per mode
distance_by_mode = df_trips.groupby("mode")["route_distance"].sum()
total_distance = df_trips["route_distance"].sum()
distance_share = (distance_by_mode / total_distance).round(4)

# Add to the stats df
trips_by_mode = pd.merge(trips_by_mode, travel_time_share, on="mode", how="left").rename(columns={"trav_time": "travel time share"})
trips_by_mode = pd.merge(trips_by_mode, distance_share, on="mode", how="left").rename(columns={"route_distance": "distance share"})

# Display
print("Stats on trips per mode (detailled):")
print(trips_by_mode)

### Trips by principal mode

# Number of trips
trips_by_mode = df_trips["routingMode"].value_counts().reset_index()
trips_by_mode.columns = ["routingMode", "count"]

# Add nb of trips shares
total_trips = trips_by_mode["count"].sum()
trips_by_mode["share"] = (trips_by_mode["count"] / total_trips).round(4)

# Convert trav_time to timedelta
df_trips["trav_time"] = pd.to_timedelta(df_trips["trav_time"])

# Compute travel time share per mode
travel_time_by_mode = df_trips.groupby("routingMode")["trav_time"].sum().dt.total_seconds()
total_travel_time = df_trips["trav_time"].sum().total_seconds()
travel_time_share = (travel_time_by_mode / total_travel_time).round(4)

# Compute distance share per mode
distance_by_mode = (df_trips.groupby("routingMode")["route_distance"].sum() / 1000).round().astype(int)
total_distance = df_trips["route_distance"].sum() / 1000
distance_share = (distance_by_mode / total_distance).round(4)

# Add to the stats df
trips_by_mode = pd.merge(trips_by_mode, travel_time_share, on="routingMode", how="left").rename(columns={"trav_time": "travel time share"})
trips_by_mode = pd.merge(trips_by_mode, distance_by_mode, on="routingMode", how="left").rename(columns={"route_distance": "distance (km)"})
trips_by_mode = pd.merge(trips_by_mode, distance_share, on="routingMode", how="left").rename(columns={"route_distance": "distance share"})

# Display
print("Stats on trips per mode (principal):")
print(trips_by_mode)