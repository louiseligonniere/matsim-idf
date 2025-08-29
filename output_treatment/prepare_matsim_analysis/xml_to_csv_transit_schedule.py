import os
import pandas as pd
import xml.etree.ElementTree as ET

"""
This module is used to convert the transit schedule file outputed by prepare MATSim pipeline, from xml into csv (output_treatment/prepare_matsim_analysis/xml/simulated_transit_schedule.xml).
It uses xml Element tree to convert .xml to .csv and creates three csv files :
- simulated_transit_lines.csv
- simulated_transit_routes.csv
- simulated_departures.csv

Csv files are saved in output_treatment/prepare_matsim_analysis/csv
"""

#### TRANSIT LINES ####

def xml_to_csv_transit_lines():
    """
    Reads xml transit schedule file (simulated_transit_schedule.xml) and searchs for transit lines. 
    Returns df_transit_lines. 
    """
    print("Reading transit lines...")

    # Parse the XML file
    tree = ET.parse(r'C:\VSCodeProjects\matsim-idf0.001\output_treatment\prepare_matsim_analysis\xml\simulated_transit_schedule.xml')
    root = tree.getroot()
    
    # Empty df for transit lines
    df_transit_lines = pd.DataFrame(columns=["id", "name"])

    progress = 0
    total = 1991

    for line in root.iter("transitLine"):
        # Line attributes
        attrib = line.attrib.copy()
        
        # Append to the transit lines df
        df_transit_lines.loc[len(df_transit_lines)] = attrib

        # Progress status
        if progress%250 == 0:
            print(f"Reading transit lines... Progress: {progress}/{total}")
        progress+=1

    df_transit_lines = df_transit_lines.rename(columns={"id":"line_id"})

    print("Reading transit lines: done!")

    return df_transit_lines


#### TRANSIT ROUTES ####

def xml_to_csv_transit_routes():
    """
    Reads xml transit schedule file (simulated_transit_schedule.xml) and searchs for transit routes. 
    Returns df_transit_routes. 
    """
    print("Reading transit routes...")

    # Parse the XML file
    tree = ET.parse(r'C:\VSCodeProjects\matsim-idf0.001\output_treatment\prepare_matsim_analysis\xml\simulated_transit_schedule.xml')
    root = tree.getroot()

    # Empty df for transit routes
    df_transit_routes = pd.DataFrame(columns=["line_id", "id", "mode"])

    progress = 0
    total = 1991

    for line in root.iter("transitLine"):
        line_id = line.get("id")

        for route in line.findall("transitRoute"):
            # Route attributes
            attrib = route.attrib.copy()

            # Route transport mode
            attrib["mode"] = route.find("transportMode").text

            # Add line id
            attrib["line_id"] = line_id

            # Append in the activities df
            df_transit_routes.loc[len(df_transit_routes)] = attrib

        # Progress status
        if progress%250 == 0:
            print(f"Reading routes for transit lines... Progress: {progress}/{total} transit lines")
        progress+=1

    df_transit_routes = df_transit_routes.rename(columns={"id":"route_id"})

    print("Reading transit routes: done!")

    return df_transit_routes


#### DEPARTURES ####

def xml_to_csv_departures():
    """
    Reads xml transit schedule file (simulated_transit_schedule.xml) and searchs for departures of transit lines. 
    Returns df_departures. 
    """
    print("Reading departures...")

    # Parse the XML file
    tree = ET.parse(r'C:\VSCodeProjects\matsim-idf0.001\output_treatment\prepare_matsim_analysis\xml\simulated_transit_schedule.xml')
    root = tree.getroot()

    # Empty df for departures
    df_departures = pd.DataFrame(columns=["id", "line_id", "route_id", "departureTime", "vehicleRefId", "mode"])

    progress = 0
    total = 1991

    for line in root.iter("transitLine"):
        line_id = line.get("id")

        for route in line.findall("transitRoute"):
            # Route attributes
            route_id = route.get("id")

            # Route transport mode
            route_mode = route.find("transportMode").text

            departures = route.find("departures")

            for departure in departures.findall("departure"):
                attrib = departure.attrib.copy()

                # Add additional variables
                attrib["line_id"] = line_id
                attrib["route_id"] = route_id
                attrib["mode"] = route_mode

                # Append in the activities df
                df_departures.loc[len(df_departures)] = attrib

        # Progress status
        if progress%250 == 0:
            print(f"Reading departures for transit lines... Progress: {progress}/{total} transit lines")
        progress+=1

    df_departures = df_departures.rename(columns={"id":"departure_id"})

    print("Reading departures: done!")

    return df_departures


#### CREATE CSV ####

os.makedirs("output_treatment/prepare_matsim_analysis/csv", exist_ok=True)

# Transit lines
df_transit_lines = xml_to_csv_transit_lines()
df_transit_lines.to_csv("output_treatment/prepare_matsim_analysis/csv/simulated_transit_lines.csv", index=False)

# Transit routes
df_transit_routes = xml_to_csv_transit_routes()
df_transit_routes.to_csv("output_treatment/prepare_matsim_analysis/csv/simulated_transit_routes.csv", index=False)

# Departures
df_departures = xml_to_csv_departures()
df_departures.to_csv("output_treatment/prepare_matsim_analysis/csv/simulated_departures.csv", index=False)
