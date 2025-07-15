import shutil
import os.path

import matsim.runtime.eqasim as eqasim

"""
This stage calls the eqasim.run function (defined in matsim.runtime.eqasim), which is used to execute the MATSim simulation.
The configuration is given in "cache/matsim.simulation.prepare". Outputs are only written in cache folder.
Returns: none.
"""

def configure(context):
    context.stage("matsim.simulation.prepare")

    context.stage("matsim.runtime.java")
    context.stage("matsim.runtime.eqasim")

def execute(context):
    config_path = "%s/%s" % (
        context.path("matsim.simulation.prepare"),
        context.stage("matsim.simulation.prepare")
    )

    # Run routing
    eqasim.run(context, "org.eqasim.ile_de_france.RunSimulation", [
        "--config-path", config_path,
        "--config:controler.lastIteration", str(1), # to limit number of iterations
        "--config:controler.writeEventsInterval", str(1),
        "--config:controler.writePlansInterval", str(1),
    ])
    assert os.path.exists("%s/simulation_output/output_events.xml.gz" % context.path())
