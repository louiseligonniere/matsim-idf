import pandas as pd

"""
This module is used to analyse trips outputed by simulation MATSim
Using the csv files (saved in output_treatment/simulation_output_analysis/csv), it produces three stats table :
- 1. On the share of trips (absolute, distance, travel time) made using each mode
- 2. On the share of legs (absolute, distance, travel time) made using each mode
- 3. On the share of legs for detailed modes for PT legs (bus / metro / train / tram)
"""


def analysis_by_mode(df_trips, car_total):
    # Number of trips
    trips_by_mode = df_trips["mode"].value_counts().reset_index()
    trips_by_mode.columns = ["mode", "count"]

    # Add nb of trips shares
    total_trips = trips_by_mode["count"].sum()
    trips_by_mode["share (%)"] = (trips_by_mode["count"] / total_trips).round(4) * 100

    # Convert trav_time to timedelta
    df_trips["trav_time"] = pd.to_timedelta(df_trips["trav_time"])

    # Compute travel time share per mode
    travel_time_by_mode = df_trips.groupby("mode")["trav_time"].sum().dt.total_seconds()
    total_travel_time = df_trips["trav_time"].sum().total_seconds()
    travel_time_share = (travel_time_by_mode / total_travel_time).round(4) * 100

    # Compute distance share per mode
    distance_by_mode = (df_trips.groupby("mode")["distance"].sum() / 1000).round().astype(int)
    total_distance = df_trips["distance"].sum() / 1000
    distance_share = (distance_by_mode / total_distance).round(4) * 100

    # Add to the stats df
    trips_by_mode = pd.merge(trips_by_mode, travel_time_share, on="mode", how="left").rename(columns={"trav_time": "travel time share (%)"})
    trips_by_mode = pd.merge(trips_by_mode, distance_by_mode, on="mode", how="left").rename(columns={"distance": "distance (km)"})
    trips_by_mode = pd.merge(trips_by_mode, distance_share, on="mode", how="left").rename(columns={"distance": "distance share (%)"})

    if car_total == True:
        # Add a row for car total
        car_total = trips_by_mode[trips_by_mode["mode"].isin(["car", "car_passenger"])].drop(columns="mode").sum()
        car_total["mode"] = "car_total"

        trips_by_mode = pd.concat([trips_by_mode, pd.DataFrame([car_total])]).sort_values(by="mode")

    # Add a row for total
    total = trips_by_mode[-trips_by_mode["mode"].isin(["car_total"])].drop(columns="mode").sum()
    total["mode"] = "total"

    trips_by_mode = pd.concat([trips_by_mode.sort_values(by="mode"), pd.DataFrame([total])])

    return trips_by_mode


### Trips by mode

# Read files
df_trips = pd.read_csv("output_treatment/simulation_output_analysis/csv/output_trips.csv", sep=";")

df_trips = df_trips.rename(columns={"main_mode": "mode", "traveled_distance": "distance"})

trips_by_mode = analysis_by_mode(df_trips=df_trips, car_total=True)

# Display
print("Stats on trips per mode (principal):")
print(trips_by_mode)


### Legs by mode

# Read files
df_legs = pd.read_csv("output_treatment/simulation_output_analysis/csv/output_legs.csv", sep=";")

legs_by_mode = analysis_by_mode(df_trips=df_legs, car_total=True)

# Display
print("Stats on legs per mode:")
print(legs_by_mode)


### Detailed mode (bus/metro/train/tram) for PT legs

# Read files
df_links = pd.read_csv("output_treatment\simulation_output_analysis\csv\output_links.csv", sep=";", dtype=str)

# Filter PT legs
df_pt = df_legs[df_legs["mode"] == "pt"]

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

pt_legs_by_mode = analysis_by_mode(df_trips=df_pt, car_total=False)

# Display
print("Stats on PT legs per mode (detailed):")
print(pt_legs_by_mode)
