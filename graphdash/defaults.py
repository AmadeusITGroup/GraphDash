# -*- coding: utf-8 -*-

import argparse

from .struct.semifrozendict import SemiFrozenDict


# GRAPH METADATA
#
# Sub-family where graphs are put if family has sub-families *and* graphs
SINK = 'Default'

# Graphs are put at root if no family is provided
DEFAULT_FAMILY = ()


def default_graph_data():
    """Default graph data.
    """
    return SemiFrozenDict({
        'name'      : None,
        'title'     : 'No *title* provided',
        'index'     : set(),
        'pretext'   : '',
        'text'      : '',
        'file'      : None,
        'export'    : None,
        'rank'      : None,
        'showtitle' : False,
        'labels'    : set(),
        'other'     : None,
        'id'        : None,
    })


# FAMILY METADATA
#
def default_family_data():
    """Default family data.
    """
    return SemiFrozenDict({
        'text'   : '',
        'rank'   : None,
        'alias'  : None,
        'labels' : set(),
        'graphs' : [],
    })


# LABEL METADATA
#
class HashableSemiFrozenDict(SemiFrozenDict):
    """Ad hoc label structure, to allow set of dicts."""
    def __hash__(self):
        return hash(frozenset(self.items()))


def default_label_data():
    """Default label data.
    """
    return HashableSemiFrozenDict({
        'name'       : 'no_name_provided',
        'text'       : 'No text provided',
        'color'      : '#268bd2',
        'text_color' : 'white',
        'tooltip'    : None,
    })


# WEBAPP METADATA
#
def default_conf():
    """Default configuration.
    """
    return SemiFrozenDict({
        'root'              : 'default_graph_dir',
        'families'          : None,
        'title'             : 'Default title',
        'subtitle'          : 'Default subtitle',
        'placeholder'       : 'Free text and #keywords',
        'header'            : '',
        'footer'            : '',
        'showfamilynumbers' : True,
        'showgraphnumbers'  : True,
        'theme'             : 'dark',
        'keep'              : 0.20,
        'logfile'           : 'webapp.log',
        'raw'               : False,
        'verbose'           : False,
        'debug'             : False,
        'headless'          : False,
        # Config just for the launcher, not the app
        'port'              : 5555,
        # Will not be exported if --export-conf is given
        'export_conf'       : None,
        'export_families'   : None,
    })

DEFAULT_FAMILIES_GLOB = '.FAMILIES.*'


# ARGUMENT PARSER
#
def add_boolean(parser, short_opt_on, long_opt_on, **kwargs):
    """Automatically add --stuff, --no-stuff and default for boolean option.
    """
    dest = long_opt_on.lstrip('-')
    long_opt_off = '--no-' + dest

    parser.add_argument(long_opt_on, short_opt_on,
                        dest=dest,
                        action='store_true',
                        help=kwargs.get('help', ''))

    parser.add_argument(long_opt_off,
                        dest=dest,
                        action='store_false')

    parser.set_defaults(dest=kwargs.get('default', None))


def get_parser():
    """Argument parser.
    """
    parser = argparse.ArgumentParser(description="GraphDash, a dashboard for graphs.")
    parser.add_argument('-c', '--conf', help="""
    Path to configuration file.
    """)
    parser.add_argument('-r', '--root', help="""
    Root directory of the graphs.
    """)
    parser.add_argument('-t', '--theme', help="""
    Change css theme.
    """)
    parser.add_argument('-k', '--keep', type=float, help="""
    Proportion of common words kept for autocompletion.
    """)
    parser.add_argument('-l', '--logfile', help="""
    Change default log file of the webapp.
    """)
    parser.add_argument('-f', '--families', help="""
    Path to families file.
    """)
    parser.add_argument('-F', '--export-families', help="""
    Export families file from loaded data, eventually
    to be filled later by user.
    """)
    parser.add_argument('-C', '--export-conf', help="""
    Export configuration file from defaults, eventually
    to be filled later by user.
    """)
    add_boolean(parser, '-a', '--raw', help="""
    Toggle raw mode: when loading, look for all graphs and ignore metadata.
    """)
    add_boolean(parser, '-v', '--verbose', help="""
    Toggle verbosity when loading application.
    """)
    add_boolean(parser, '-d', '--debug', help="""
    Toggle debug mode: enable Grunt livereload, enable Flask debug mode.
    """)
    add_boolean(parser, '-H', '--headless', help="""
    Toggle headless mode: do not render pages, just search results.
    This may be useful on large data sets.
    """)
    parser.add_argument('-p', '--port', type=int, help="""
    When launched with Flask development server, port.
    """)

    return parser
