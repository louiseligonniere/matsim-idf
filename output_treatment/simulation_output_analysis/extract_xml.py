import gzip
import shutil
import os

"""
This module is used to decompress .xml.gz files in simulation output. 
Extracted .xml files are saved in output_treatment/simulation_output_analysis/xml.
"""

# Create output extract folder
os.makedirs("output_treatment/simulation_output_analysis/xml", exist_ok=True)

# Iterate on files .xml.gz
for filename in os.listdir("output/simulation_output"):
    if filename.endswith(".xml.gz"):
        input_path = os.path.join("output", "simulation_output", filename)
        
        # New filename with extension .xml
        output_filename = filename[:-3]
        output_path = os.path.join("output_treatment/simulation_output_analysis/xml", output_filename)

        # Decompress the file
        with gzip.open(input_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        print(f"Decompressed : {filename} → {output_filename}")
