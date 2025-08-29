import os
import pandas as pd
import xml.etree.ElementTree as ET

"""
This module is used to convert the population file outputed by prepare MATSim pipeline, from xml into csv (output_treatment/prepare_matsim_analysis/xml/simulated_population.xml).
It uses xml Element tree to convert .xml to .csv and creates three csv files :
- simulated_population.csv : persons in the population
- simulated_activities.csv : activities made by the population (plans before matsim simu)
- simulated_trips.csv : trips made by the population (plans before matsim simu)

Csv files are saved in output_treatment/prepare_matsim_analysis/csv
"""

#### POPULATION ####

def xml_to_csv_pop():
    """
    Reads xml population file (simulated_population.xml) and searchs for persons. 
    Returns df_population. 
    """
    print("Reading population...")

    # Parse the XML file
    tree = ET.parse(r'C:\VSCodeProjects\matsim-idf0.001\output_treatment\prepare_matsim_analysis\xml\simulated_population.xml')
    root = tree.getroot()
        
    # Available variables
    rows = []

    for person in root.iter("person"):
        row = {}
        row["person_id"] = person.get("id")
        attributes = person.find("attributes")

        for attr in attributes.findall(".//attribute"):
            name = attr.get("name")
            value = attr.text
            row[name] = value

        rows.append(row)

    df_population = pd.DataFrame(rows)

    print("Reading population: done!")

    return df_population


#### ACTIVITIES ####

def xml_to_csv_activities():
    """
    Reads xml population file (simulated_population.xml) and searchs for activities. 
    Returns df_activities. 
    """

    # Parse the XML file
    tree = ET.parse(r'C:\VSCodeProjects\matsim-idf0.001\output_treatment\prepare_matsim_analysis\xml\simulated_population.xml')
    root = tree.getroot()
        
    # Empty df for activities
    df_activities = pd.DataFrame(columns=["person_id", "activity_id", "type", "link", "facility", "x", "y", "end_time", "max_dur"])

    progress = 0
    total = len(df_population)

    for person in root.iter("person"):
        person_id = person.get("id")

        # Find the selected plan
        plan = person.find("plan")

        for activity in plan.findall("activity"):
            # Activity main attributes
            attrib = activity.attrib.copy()

            # Add person id
            attrib["person_id"] = person_id

            # Append in the activities df
            df_activities.loc[len(df_activities)] = attrib

        # Progress status
        if progress%500 == 0:
            print(f"Reading activities... Progress: {progress}/{total}")
        progress+=1

    # Add a unique activity id
    df_activities["activity_id"] = range(len(df_activities))

    print("Reading activities: done!")

    return df_activities


#### TRIPS ####

def xml_to_csv_trips():
    """
    Reads xml population file (simulated_population.xml) and searchs for trips. 
    Returns df_trips. 
    """

    # Parse the XML file
    tree = ET.parse(r'C:\VSCodeProjects\matsim-idf0.001\output_treatment\prepare_matsim_analysis\xml\simulated_population.xml')
    root = tree.getroot()
    
    # Empty df for trips
    df_trips = pd.DataFrame(columns=["person_id", "trip_id", "mode", "dep_time", "trav_time", "routingMode",
                                    "route_type", "route_start_link", "route_end_link", "route_trav_time", "route_distance", "route_vehicleRefId",
                                    "route_pt_transitRouteId", "route_pt_boardingTime", "route_pt_transitLineId", "route_pt_accessFacilityId", "route_pt_egressFacilityId",
                                    "route_links"])

    progress = 0
    total = len(df_population)

    for person in root.iter("person"):
        person_id = person.get("id")

        # Find the selected plan
        plan = person.find("plan")

        for leg in plan.findall("leg"):
            # Leg main attributes
            leg_attrib = leg.attrib.copy()

            # Leg additionnal attributes
            attributes = leg.find("attributes")
            routingMode = attributes.find(".//*[@name='routingMode']").text
            leg_attrib["routingMode"] = routingMode

            # Route for the given leg
            route = leg.find("route") 
            route_attrib = route.attrib
            route_attrib = {f"route_{k}": v for k, v in route_attrib.items()} # add prefix to route variables
            leg_attrib |= route_attrib # add route variables to leg attributes

            # Route details
            if route.text is not None:
                # For pt legs, we get additionnal variables
                if route_attrib["route_type"] == "default_pt":
                    route_pt_descr = {}
                    route_text = route.text.strip().strip("{}") # additionnal variables are not read properly (read as one single str), we need to manually recreate a dictionnary of those variables
                    for item in route_text.split(","):
                        if ":" in item:
                            key, val = item.split(":", 1)
                            key = key.strip().strip('"')
                            val = val.strip().strip('"')
                            route_pt_descr[key] = val
                    route_pt_descr = {f"route_pt_{k}": v for k, v in route_pt_descr.items()} # add prefix to pt route variables
                    leg_attrib |= route_pt_descr # add pt route variables to leg attributes

                # For some legs, we get details on links
                if route_attrib["route_type"] == "links":
                    route_links_descr = {"route_links": route.text}
                    leg_attrib |= route_links_descr # add links variable to leg attributes

            # Add person id
            leg_attrib["person_id"] = person_id

            # Append in the trips df
            df_trips.loc[len(df_trips)] = leg_attrib

        # Progress status
        if progress%500 == 0:
            print(f"Reading trips... Progress: {progress}/{total}")
        progress+=1

    # Add a unique trip id
    df_trips["trip_id"] = range(len(df_trips))

    print("Reading trips: done!")

    return df_trips


#### CREATE CSV ####

os.makedirs("output_treatment/prepare_matsim_analysis/csv", exist_ok=True)

# Population
df_population = xml_to_csv_pop()
df_population.to_csv("output_treatment/prepare_matsim_analysis/csv/simulated_population.csv")

# Activities
df_activities = xml_to_csv_activities()
df_activities.to_csv("output_treatment/prepare_matsim_analysis/csv/simulated_activities.csv")

# Trips
df_trips = xml_to_csv_trips()
df_trips.to_csv("output_treatment/prepare_matsim_analysis/csv/simulated_trips.csv")

