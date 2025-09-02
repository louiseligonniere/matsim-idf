import os
import matsim.runtime.eqasim as eqasim
from synpp import ConfigurationContext, ExecuteContext

"""
This stage runs the full MATSim simulation (using the eqasim.run function). 
Outputs (including experienced plans) are written in the output folder.
Returns: none.
"""

def configure(context: ConfigurationContext):
    context.config("output_path")
    context.config("output_prefix", "ile_de_france_")
    context.config("force_full_rerun", False)

    context.stage("matsim.runtime.java")
    context.stage("matsim.runtime.eqasim")

    context.stage("matsim.output")


def execute(context: ExecuteContext):

    config_path = "%s\%s\%sconfig.xml" % (
        context.path("matsim.runtime.eqasim").split("\cache")[0],
        context.config("output_path"),
        context.config("output_prefix")
    )

    force_full_rerun = context.config("force_full_rerun")
    if (
        os.path.exists("%s/simulation_output/output_events.xml.gz" % context.config("output_path"))
        and force_full_rerun is False
    ):
        return

    eqasim.run(
        context,
        "org.eqasim.ile_de_france.RunSimulation",
        [
            "--config-path",
            config_path,
            "--config:planCalcScore.writeExperiencedPlans",
            "true",
        ],
        cwd=context.config("output_path"),
    )

    assert os.path.exists(
        "%s/simulation_output/output_events.xml.gz" % context.config("output_path")
    )
