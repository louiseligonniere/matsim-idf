from tqdm import tqdm
import pandas as pd
import numpy as np

"""
This stage filters out census observations which live or work outside of
Île-de-France.
Returns: extract of the census with selected and cleaned variables variables AND FILTERED for departements under study
"""

def configure(context):
    context.stage("data.census.cleaned")
    context.stage("data.spatial.codes")

def execute(context):
    df = context.stage("data.census.cleaned")

    # Filter requested codes
    df_codes = context.stage("data.spatial.codes")

    requested_departements = df_codes["departement_id"].unique()
    df = df[df["departement_id"].isin(requested_departements)] # ce filtre est normalement inutile (car on a déjà filtré avec la même condition en chargeant le census)

    excess_communes = set(df["commune_id"].unique()) - set(df_codes["commune_id"].unique())
    if not excess_communes == {"undefined"}:
        raise RuntimeError("Found additional communes: %s" % excess_communes)

    excess_iris = set(df["iris_id"].unique()) - set(df_codes["iris_id"].unique())
    if not excess_iris == {"undefined"}:
        raise RuntimeError("Found additional IRIS: %s" % excess_iris)

    return df
