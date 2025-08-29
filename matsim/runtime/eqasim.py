import subprocess as sp
import os, os.path, shutil

import matsim.runtime.git as git
import matsim.runtime.java as java
import matsim.runtime.maven as maven

"""
This stage does two things:
    - 1. It creates the .jar executable that is used to execute the MATSim simulation. This is done by cloning 
    the eqasim-org/eqasim-java.git repo and building the eqasim .jar using Maven.
    - 2. It defines the eqasim.run function, which in turns calls the java.run function to execute the MATSim 
    simulation (through the .jar created as specified in point 1).
Returns: path to the .jar executable ("eqasim-java/ile_de_france/target/ile_de_france-%s.jar" % version). 
"""

DEFAULT_EQASIM_VERSION = "1.5.0"
DEFAULT_EQASIM_BRANCH = "develop"
DEFAULT_EQASIM_COMMIT = "ece4932"

def configure(context):
    context.stage("matsim.runtime.git")
    context.stage("matsim.runtime.java")
    context.stage("matsim.runtime.maven")

    context.config("eqasim_version", DEFAULT_EQASIM_VERSION)
    context.config("eqasim_branch", DEFAULT_EQASIM_BRANCH)
    context.config("eqasim_commit", DEFAULT_EQASIM_COMMIT)
    context.config("eqasim_tag", None)
    context.config("eqasim_repository", "https://github.com/eqasim-org/eqasim-java.git")
    context.config("eqasim_path", "")

def run(context, command, arguments, cwd = None):
    version = context.config("eqasim_version")

    # Make sure there is a dependency
    context.stage("matsim.runtime.eqasim")

    jar_path = "%s/eqasim-java/ile_de_france/target/ile_de_france-%s.jar" % (
        context.path("matsim.runtime.eqasim"), version
    )

    java.run(context, command, arguments, jar_path, cwd=cwd)

def execute(context):
    version = context.config("eqasim_version")

    # Normal case: we clone eqasim
    if context.config("eqasim_path") == "":
        # Clone repository and checkout version
        branch = context.config("eqasim_branch")

        git.run(context, [
            "clone", "--single-branch", "-b", branch,
            context.config("eqasim_repository"), "eqasim-java"
        ])

        # Select the configured commit or tag
        commit = context.config("eqasim_commit")

        git.run(context, [
            "checkout", commit
        ], cwd = "{}/eqasim-java".format(context.path()))

        # Build eqasim
        maven.run(context, ["-Pstandalone", "--projects", "ile_de_france", "--also-make", "package", "-DskipTests=true"], cwd = "%s/eqasim-java" % context.path())

        if not os.path.exists("{}/eqasim-java/ile_de_france/target/ile_de_france-{}.jar".format(context.path(), version)):
            raise RuntimeError("The JAR was not created correctly. Wrong eqasim_version specified?")

    # Special case: we provide a local folder containing the Java code to use for MATSim directly. 
    else:
        # Build the jar 
        maven.run(context, ["-Pstandalone", "--projects", "ile_de_france", "--also-make", "package", "-DskipTests=true"],
                  cwd = context.config("eqasim_path"))

        os.makedirs("%s/eqasim-java/ile_de_france/target" % context.path())
        shutil.copy("%s/ile_de_france/target/ile_de_france-%s.jar" % (context.config("eqasim_path"), version),
            "%s/eqasim-java/ile_de_france/target/ile_de_france-%s.jar" % (context.path(), version))

    return "eqasim-java/ile_de_france/target/ile_de_france-%s.jar" % version

def validate(context):
    path = context.config("eqasim_path")

    if path == "":
        return True

    if not os.path.exists(path):
        raise RuntimeError("Cannot find eqasim at: %s" % path)
    
    if context.config("eqasim_tag") is None:
        if context.config("eqasim_commit") is None:
            raise RuntimeError("Either eqasim commit or tag must be defined")
        
    if (context.config("eqasim_tag") is None) == (context.config("eqasim_commit") is None):
        raise RuntimeError("Eqasim commit and tag must not be defined at the same time")

    return os.path.getmtime(path)
