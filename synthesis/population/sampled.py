import numpy as np
import pandas as pd
import itertools

"""
This stage has the census data as input and samples households according to the
household weights given by INSEE. The resulting sample size can be controlled
through the 'sampling_rate' configuration option.
Sample done by replicating each household by its household weight (stochastically rounded) and 
then uniform sample with defined sampling_rate
Returns: SAMPLED census extract. 
"""

def configure(context):
    if context.config("projection_year", None) is None:
        context.stage("data.census.filtered", alias = "source")
    else:
        context.stage("synthesis.population.projection.reweighted", alias = "source")

    context.config("random_seed")
    context.config("sampling_rate")

def execute(context):
    df_census = context.stage("source").sort_values(by = "household_id").copy()

    sampling_rate = context.config("sampling_rate")
    random = np.random.RandomState(context.config("random_seed"))

    # Perform stochastic rounding for the population (and scale weights)
    # Stochastic rounding = we round to the closest smaller or larger number, with probability in inverse proportion 
    # to the distance to the closest rounded number (eg: 2.3 is rounded to 2 with prob 0.3 and to 3 with prob 0.7)
    # Here : stochastic rounding on weight => multiplicator
    df_rounding = df_census[["household_id", "weight", "household_size"]].drop_duplicates("household_id")
    df_rounding["multiplicator"] = np.floor(df_rounding["weight"])
    df_rounding["multiplicator"] += random.random_sample(len(df_rounding)) <= (df_rounding["weight"] - df_rounding["multiplicator"])
    df_rounding["multiplicator"] = df_rounding["multiplicator"].astype(int)

    # Multiply households (use same multiplicator for all household members)
    household_multiplicators = df_rounding["multiplicator"].values
    household_sizes = df_rounding["household_size"].values

    # create index to replicate all households members by their household weight
    # the order ([0, 1, 0, 1, 2, 2, ...]) is important here as they will be reassigned to new households later with that assumption
    expandor = np.split(np.arange(len(df_census)), np.cumsum(household_sizes)) # liste de listes des membres de chaque ménage
    expandor = np.asarray([x for x in expandor if x.size > 0], dtype="object") # supprime ménages vides
    expandor = np.repeat(expandor, household_multiplicators, axis=0) # répète chaque ménage autant de fois que le household_multiplicator correspondant
    expandor = list(itertools.chain(*expandor)) # sépare les individus = chaque individu a été répété autant de fois que le household_multiplicator de son ménage

    df_census = df_census.iloc[expandor]

    # Old household and person IDs
    df_census["census_person_id"] = df_census["person_id"]
    df_census["census_household_id"] = df_census["household_id"]

    # Create new person IDs
    df_census["person_id"] = np.arange(len(df_census))

    # Create new household IDs
    household_sizes = np.repeat(household_sizes, household_multiplicators)
    household_count = np.sum(household_multiplicators)
    df_census.loc[:, "household_id"] = np.repeat(np.arange(household_count), household_sizes)

    # Select sample from 100% population
    selector = random.random_sample(household_count) < sampling_rate # tirage au niveau des ménages
    selector = np.repeat(selector, household_sizes)
    df_census = df_census[selector]

    del df_census["weight"]
    return df_census
