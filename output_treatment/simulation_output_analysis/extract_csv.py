import gzip
import shutil
import os

"""
This module is used to decompress .csv.gz files in simulation output. 
Extracted .csv files are saved in output_treatment/simulation_output_analysis/csv.
"""

# Create output extract folder
os.makedirs("output_treatment/simulation_output_analysis/csv", exist_ok=True)

# Iterate on files .csv.gz
for filename in os.listdir("output/simulation_output"):
    if filename.endswith(".csv.gz"):
        input_path = os.path.join("output", "simulation_output", filename)
        
        # New filename with extension .csv
        output_filename = filename[:-3]
        output_path = os.path.join("output_treatment/simulation_output_analysis/csv", output_filename)

        # Decompress the file
        with gzip.open(input_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        print(f"Decompressed : {filename} → {output_filename}")
