#!/usr/bin/python
# encoding: utf-8

"""
Project parameters handling : read & load configuration
"""

import yaml
from pwbscripts.project_parameters import ProjectParameters

"""
tasks :
    * HyuBot : maintain of a list of pages in a project (pages in one of its subportal)
    * announces : maintains a list of project announces with
                  the properties for deletion and fusion of this project talk page.
"""

# Configuration file structure validation


class ConfigFilePattern(object):

    """Class defined to validate config file"""

    def __init__(self, pattern):
        "pattern : a dic of ke"


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
    with open(conffilepath, 'r') as stream:
        content = yaml.load(stream)

        projects = [
            load_parameters(name, content[name])
            for name in content.projects
        ]

        return projects


class ConfigError(Exception):

    """Class related to non correct config path"""

    def __init__(self):
        pass

from Schema import ObjectFragment, ListFragment, StringParamUnit


def get_project_schema():
    project_conf = ObjectFragment("Project",
                                  "configuration for a WikiProject",
                                  {StringParamUnit("name", "the name of the project (without Projet:)"),
                                   StringParamUnit("tasks", "the tasks ")
                                   })
    return project_conf


class Config(object):

    '''config object, used to store configuration'''

    def __init__(self, filepath):
        self.projects = read_conffile
