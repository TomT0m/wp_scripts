#!/usr/bin/python
#encoding: utf-8

import yaml
from project_parameters import ProjectParameters

"""
tasks : 
    * HyuBot : maintain of a list of pages in a project (pages in one of its subportal)
    * announces : maintains a list of project announces with the properties for deletion and fusion of this project talk page.
"""


def load_parameters(name, project_obj):
    return ProjectParameters(name,
                             project_obj.page,
                             portal_names= 
    )

def read_conffile(conffilepath):
    """
    returns the 
    """
    
    content = yaml.load(conffilepath)

    projects = [load_parameters(name, params)
                for name, params in content
    ]

