# A helper function to deserialize a GML file
from pathlib import Path
from yaml import safe_load

from .core.errors import InvalidGMLFile
from .gloomhaven.gloomhavenclass import GloomhavenClass

def create_haven_class_from_file(path_to_gml: Path):
    """
    Create the appropriate instance of a HavenClass based on the header in the GML file
    """
    with open(path_to_gml, "r") as file:
        python_gml = safe_load(file)

    try:
        format = python_gml["format"]
    except:
        format = "gloomhaven"

    if format == "gloomhaven":
        return GloomhavenClass(path_to_gml)