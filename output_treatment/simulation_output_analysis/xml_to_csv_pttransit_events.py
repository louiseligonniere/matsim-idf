import os
import pandas as pd
import xml.etree.ElementTree as ET

"""
This module is used to convert the events file outputed by MATSim, from xml into csv (output_treatment/simulation_output_analysis/xml/output_events.xml).
It uses xml Element tree to convert .xml to .csv and creates one csv file :
- output_pttransit_events.csv : events of type pt_transit

Csv files are saved in output_treatment/simulation_output_analysis/csv
"""

#### EVENTS ANALYSIS ####

def xml_to_csv_events():
    """
    Reads xml events file (output_events.xml) and searchs for pt_transit events. 
    Returns df_events. 
    """
    print("Reading pt_transit events...")

    # Parse the XML file
    tree = ET.parse(r'C:\VSCodeProjects\matsim-idf-yvelines0.05\output_treatment\simulation_output_analysis\xml\output_events.xml')
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

os.makedirs("output_treatment/prepare_matsim_analysis/csv", exist_ok=True)

# Population
df_population = xml_to_csv_events()
df_population.to_csv("output_treatment/simulation_output_analysis/csv/converted_output_events.csv")