import os
import pandas as pd
import xml.etree.ElementTree as ET
import numpy as np
import re 
from collections import defaultdict

"""
This module reads a .xml file, prints the tree structure, and creates a .tex file containing the Latex code 
to create a simple tree from that .xml.
"""

# File path to adapt
file_path = r'C:\VSCodeProjects\matsim-idf\output_treatment\prepare_matsim_analysis\xml\simulated_vehicles.xml'

# Parse the XML file
tree = ET.parse(file_path)
root = tree.getroot()
print(f"Root tag: {root.tag}")

# Get the maxdepth
maxdepth = 0

def depth(elem, level): 
    """function to get the maxdepth"""
    global maxdepth
    if (level == maxdepth):
        maxdepth += 1
    # recursive call to function to get the depth
    for child in elem:
        depth(child, level + 1)


depth(tree.getroot(), -1)
print(f"Max depth: {maxdepth}")

def inspect_elements_and_generate_latex(root, file_path):
    from collections import defaultdict
    import os
    import re

    name_values_by_path = defaultdict(list)
    tags_by_path = defaultdict(list)
    attribs_by_path = defaultdict(list)
    printed_paths = set()
    dirtree_lines = []

    def deduplicate_ordered(lst):
        return list(dict.fromkeys(lst))

    def format_tex_line(level, content, color="blue"):
        return f".{level} \\textcolor{{{color}}}{{{content}}}."

    # ---------- 1st Pass: Collect ----------
    def collect(element, path_so_far):
        for child in element.findall("./"):
            new_path = path_so_far + [child.tag]
            path_key = tuple(new_path)

            tags_by_path[path_key].extend([c.tag for c in child.findall("./")])
            attribs_by_path[path_key].extend(list(child.attrib.keys()))

            # Only collect 'name' values if this is an <attribute> element
            if child.tag == "attribute" and "name" in child.attrib:
                name_values_by_path[path_key].append(child.attrib["name"])

            collect(child, new_path)

    # ---------- 2nd Pass: Print + Tex ----------
    def print_in_order(element, path_so_far, level=2):
        for child in element.findall("./"):
            new_path = path_so_far + [child.tag]
            path_key = tuple(new_path)

            if path_key not in printed_paths:
                printed_paths.add(path_key)

                attribs = deduplicate_ordered(attribs_by_path[path_key])
                tags = deduplicate_ordered(tags_by_path[path_key])
                name_vals = deduplicate_ordered(name_values_by_path[path_key])

                print(f"Element: <{child.tag}> at level {len(new_path)}")
                print(f"  Path: {'/'.join(f'<{p}>' for p in new_path)}")
                print(f"  Attributes: {attribs}")
                print(f"  Child elements: {tags}")
                if name_vals:
                    print(f"  Distinct 'name' attribute values: {name_vals}")
                print()

                dirtree_lines.append(format_tex_line(level, child.tag))

                for attr in attribs:
                    if attr == "name" and name_vals:
                        quoted_names = ", ".join(f'"{val}"' for val in name_vals)
                        attr_str = f'\\textcolor{{red}}{{name}}={quoted_names}'
                        dirtree_lines.append(f".{level + 1} {attr_str}.")
                        dirtree_lines.append(f".{level + 1} \\textcolor{{green}}{{text}}.")
                    else:
                        dirtree_lines.append(format_tex_line(level + 1, attr, color="red"))

            print_in_order(child, new_path, level + 1)

    # ---------- Handle root separately ----------
    root_path = [root.tag]
    path_key = tuple(root_path)
    tags_by_path[path_key].extend([c.tag for c in root.findall("./")])
    attribs_by_path[path_key].extend(list(root.attrib.keys()))
    
    # Only collect root 'name' attribute if it's <attribute> (usually not the case)
    if root.tag == "attribute" and "name" in root.attrib:
        name_values_by_path[path_key].append(root.attrib["name"])

    printed_paths.add(path_key)
    attribs = deduplicate_ordered(attribs_by_path[path_key])
    tags = deduplicate_ordered(tags_by_path[path_key])
    name_vals = deduplicate_ordered(name_values_by_path[path_key])

    print(f"Element: <{root.tag}> at level 1")
    print(f"  Path: {'/'.join(f'<{p}>' for p in root_path)}")
    print(f"  Attributes: {attribs}")
    print(f"  Child elements: {tags}")
    if name_vals:
        print(f"  Distinct 'name' attribute values: {name_vals}")
    print()

    dirtree_lines.append(format_tex_line(1, root.tag))
    for attr in attribs:
        if attr == "name" and name_vals:
            attr_str = f'{attr}="{",".join(name_vals)}"'
        else:
            attr_str = attr
        dirtree_lines.append(format_tex_line(2, attr_str, color="red"))

    # ---------- Generate Output ----------
    collect(root, root_path)
    print_in_order(root, root_path)

    os.makedirs("output_treatment/prepare_matsim_analysis/tex", exist_ok=True)

    filename = re.search(r"simulated_(.*?)\.xml", file_path).group(1)
    tex_filename = f"tree_{filename}.tex"
    tex_path = os.path.join("output_treatment", "prepare_matsim_analysis", "tex", tex_filename)

    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("\\dirtree{%\n")
        for line in dirtree_lines:
            f.write(f"    {line}\n")
        f.write("}\n")
    print(f"LaTeX tree printed in: {tex_path}")


print("Tree structure: \n")
inspect_elements_and_generate_latex(root, file_path)