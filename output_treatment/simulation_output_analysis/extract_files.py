import gzip
import shutil
import os

"""
This module is used to decompress .csv.gz and .xml.gz files in simulation output. 
Extracted files are saved in OUTPUT_PATH/extracted_files.
"""

OUTPUT_PATH = "output_treatment/results"

# Create output extract folder
os.makedirs("%s/extracted_files" % OUTPUT_PATH, exist_ok=True)

# Iterate on files .csv.gz
for filename in os.listdir("output/simulation_output"):
    if filename.endswith(".csv.gz"):
        input_path = os.path.join("output", "simulation_output", filename)
        
        # New filename with extension .csv
        output_filename = filename[:-3]
        output_path = os.path.join(OUTPUT_PATH, "extracted_files", output_filename)

        # Decompress the file
        with gzip.open(input_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        print(f"Decompressed : {filename} → {output_filename}")


# Iterate on files .xml.gz
for filename in os.listdir("output/simulation_output"):
    if filename.endswith(".xml.gz"):
        input_path = os.path.join("output", "simulation_output", filename)
        
        # New filename with extension .xml
        output_filename = filename[:-3]
        output_path = os.path.join(OUTPUT_PATH, "extracted_files", output_filename)

        # Decompress the file
        with gzip.open(input_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        print(f"Decompressed : {filename} → {output_filename}")