import gzip
import shutil
import os

"""
This module is used to decompress .xml.gz files (prepare MATSim, config files). 
Extracted .xml files are saved in output_treatment/prepare_matsim_analysis/xml.
"""

# Create output extract folder
os.makedirs("output_treatment/prepare_matsim_analysis/xml", exist_ok=True)

# Iterate on files .xml.gz
for filename in os.listdir("output"):
    if filename.endswith(".xml.gz"):
        input_path = os.path.join("output", filename)
        
        # New filename with extension .xml
        output_filename = filename[:-3]
        output_path = os.path.join("output_treatment/prepare_matsim_analysis/xml", output_filename)

        # Decompress the file
        with gzip.open(input_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        print(f"Decompressed : {filename} → {output_filename}")
