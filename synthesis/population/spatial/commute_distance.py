import pandas as pd

"""
This stage adds commute distance for work (resp. education) (computed from the HTS) to persons 
in the synthetic population (following the matching HTS-census).
Returns: dict of df of persons in the synth pop + their respective hts_id and commute distance 
for 1. work and 2. education
"""

def configure(context):
    context.stage("synthesis.population.enriched")
    context.stage("data.hts.commute_distance")

def execute(context):
    df_matching = context.stage("synthesis.population.enriched")
    df_commute_distance = context.stage("data.hts.commute_distance")

    df_work = pd.merge(
        df_matching[["person_id", "hts_id"]],
        df_commute_distance["work"][["person_id", "commute_distance"]].rename(columns = dict(person_id = "hts_id")),
        how = "left"
    )

    df_education = pd.merge(
        df_matching[["person_id", "hts_id"]],
        df_commute_distance["education"][["person_id", "commute_distance"]].rename(columns = dict(person_id = "hts_id")),
        how = "left"
    )

    assert len(df_work) == len(df_matching)
    assert len(df_education) == len(df_matching)

    return dict(
        work = df_work, education = df_education
    )
