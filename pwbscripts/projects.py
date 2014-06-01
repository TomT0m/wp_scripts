#!/usr/bin/python
#encoding: utf-8

"""
Project parameters handling : read & load configuration
"""

import yaml
from project_parameters import ProjectParameters

"""
tasks :
    * HyuBot : maintain of a list of pages in a project (pages in one of its subportal)
    * announces : maintains a list of project announces with
                  the properties for deletion and fusion of this project talk page.
"""


def load_parameters(name, project_obj):
    """
    translate a yaml parsed project object in the file into a ProjectParameters object
    """
    return ProjectParameters(name,
                             project_obj
                            )

def read_conffile(conffilepath):
    """
    returns the parsed yaml conffile
    """

    content = yaml.load(conffilepath)

    projects = [
        load_parameters(name, content[name])
        for name in content
    ]

    return projects

