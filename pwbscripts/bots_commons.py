
# encoding:utf-8


from argparse import ArgumentParser
import dirspec.basedir  # multiformat config file getter
import os


def create_options():
    """ Script option parsing """
    options = ArgumentParser("Project talk page cleaner")

    options.add_argument('-C', '--config-file', metavar='FILE',
                         help="configuration file", dest="conffile")
    options.add_argument('-s', '--simulate', action='store_true',
                         help="don't save changes", dest="simulate")
    options.add_argument('-t', '--test', action='store_true',
                         help="run tests", dest="test")
    options.add_argument('-p', '--page',
                         help="run tests", metavar="PAGE", dest="page",
                         default="Projet:Informatique")
    options.add_argument('-v', '--verbose', action='store_true',
                         help="show debugging messages", dest="debug")

    return options


def get_default_configfile():
    """ returns the file path for the default configuration file """

    config_path = dirspec.basedir.get_xdg_config_home()
    basepath = os.path.join(config_path, 'pwb')

    conffile = os.path.join(basepath, 'projects.yaml')

    return conffile
