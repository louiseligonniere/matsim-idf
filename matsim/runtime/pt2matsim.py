import subprocess as sp
import os, os.path

import matsim.runtime.git as git
import matsim.runtime.java as java
import matsim.runtime.maven as maven

"""
This stage does two things:
    - 1. It clones the matsim-org/pt2matsim.git repo and builds the pt2matsim .jar using Maven (jar path: 
    pt2matsim/target/pt2matsim-%s-shaded.jar)
    - 2. It defines the pt2matsim.run function, which in turns calls the java.run function to execute 
    pt2matsim (through the .jar created as specified in point 1).
Returns: none. 
"""

def configure(context):
    context.stage("matsim.runtime.git")
    context.stage("matsim.runtime.java")
    context.stage("matsim.runtime.maven")

    context.config("pt2matsim_version", "22.3")
    context.config("pt2matsim_branch", "v22.3")

def run(context, command, arguments, vm_arguments=[]):
    version = context.config("pt2matsim_version")

    # Make sure there is a dependency
    context.stage("matsim.runtime.pt2matsim")

    jar_path = "%s/pt2matsim/target/pt2matsim-%s-shaded.jar" % (
        context.path("matsim.runtime.pt2matsim"), version
    )
    java.run(context, command, arguments, jar_path, vm_arguments)

def execute(context):
    version = context.config("pt2matsim_version")
    branch = context.config("pt2matsim_branch")

    # Clone repository and checkout version
    git.run(context, [
        "clone", "https://github.com/matsim-org/pt2matsim.git",
        "--branch", branch,
        "--single-branch", "pt2matsim",
        "--depth", "1"
    ])

    # Build pt2matsim
    maven.run(context, ["package", "-DskipTests=true"], cwd = "%s/pt2matsim" % context.path())
    jar_path = "%s/pt2matsim/target/pt2matsim-%s-shaded.jar" % (context.path(), version)

    # Test pt2matsim
    java.run(context, "org.matsim.pt2matsim.run.CreateDefaultOsmConfig", [
        "test_config.xml"
    ], jar_path)

    assert os.path.exists("%s/test_config.xml" % context.path())
