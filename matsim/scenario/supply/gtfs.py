import os.path

import matsim.runtime.pt2matsim as pt2matsim

"""
This stage calls pt2matsim to create the transit schedule and the transit vehicles files from the GTFS. 
It also writes the configuration used for the schedule into config_template.xml.
Returns: file names "transit_schedule.xml.gz" and "transit_vehicles.xml.gz".
"""

def configure(context):
    context.stage("matsim.runtime.java")
    context.stage("matsim.runtime.pt2matsim")
    context.stage("data.gtfs.cleaned")
    context.stage("synthesis.population.spatial.home.locations")

    context.config("gtfs_date", "dayWithMostServices")

def execute(context):
    gtfs_path = "%s/output" % context.path("data.gtfs.cleaned")
    crs = context.stage("synthesis.population.spatial.home.locations").crs

    pt2matsim.run(context, "org.matsim.pt2matsim.run.Gtfs2TransitSchedule", [
        gtfs_path,
        context.config("gtfs_date"), crs,
        "%s/transit_schedule.xml.gz" % context.path(),
        "%s/transit_vehicles.xml.gz" % context.path()
    ])

    assert(os.path.exists("%s/transit_schedule.xml.gz" % context.path()))
    assert(os.path.exists("%s/transit_vehicles.xml.gz" % context.path()))

    return dict(
        schedule_path = "transit_schedule.xml.gz",
        vehicles_path = "transit_vehicles.xml.gz"
    )
