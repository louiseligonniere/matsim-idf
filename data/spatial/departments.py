import numpy as np
import pandas as pd
import geopandas as gpd
import os

"""
Returns: table of departements + geometry (for departements under study)
"""

def configure(context):
    context.stage("data.spatial.municipalities")

def execute(context):
    df_departements = context.stage("data.spatial.municipalities").dissolve(
        by = "departement_id").drop(columns = ["commune_id", "has_iris"]).reset_index()

    return df_departements
