# -*- coding: utf-8 -*-

from __future__ import with_statement, print_function

import os
import os.path as op
try:
    import ushlex as shlex
except ImportError:
    import shlex
from collections import defaultdict, namedtuple
from glob import glob

import logging
from flask import (Flask, render_template, abort, jsonify,
                   request, send_from_directory, redirect,
                   url_for, Response, flash)

from .flask_utils import cache, after_request_log
from .markdown_filter import md_convert, md_iconvert
from .defaults import default_conf, DEFAULT_FAMILIES_GLOB
from .load import (load_args, load_conf, load_data, load_data_raw,
                   load_tags, load_themes, load_families,
                   post_load, export_conf, export_families,
                   sort_sons, sort_labels, sort_indexes,
                   dump_data, show_conf, show_tags, show_themes, check_theme)


# CONFIGURATION
#
DIRNAME = op.realpath(op.dirname(__file__))
ASSETS = op.join(DIRNAME, 'assets')

# CLI overrides env variables
ARGS = load_args()
CONF_FILE = os.getenv('CONF')
if 'conf' in ARGS:
    CONF_FILE = ARGS['conf']
    del ARGS['conf']  # we do not want to update CONF with 'conf' attribute

# We convert to abspath here because if given through
# CLI, these are supposed to be relative to the working dir,
# not the configuration file
if 'root' in ARGS:
    ARGS['root'] = op.realpath(ARGS['root'])
if 'families' in ARGS:
    ARGS['families'] = op.realpath(ARGS['families'])

# Actual configuration parsing
# conf file overrides, then CLI overrides
CONF = default_conf()
CONF.update(load_conf(CONF_FILE))
CONF.update(ARGS)

# Unless the path is absolute, root directory is supposed to be
# a relative path from the configuration file
CONF_DIR = op.dirname(CONF_FILE) if CONF_FILE else ''
if not op.isabs(CONF['root']):
    CONF['root'] = op.join(CONF_DIR, CONF['root'])

# Expand symlinks
CONF['root'] = op.realpath(CONF['root'])

if CONF['raw']:
    DATA = load_data_raw(CONF['root'])
else:
    DATA = load_data(CONF['root'])

    # Try to read the families file, describing families metadata
    if CONF['families'] is not None:
        if not op.isabs(CONF['families']):
            CONF['families'] = op.join(CONF_DIR, CONF['families'])
        CONF['families'] = op.realpath(CONF['families'])
        load_families(DATA, CONF['families'])
    else:
        # If families is not set we try a default file
        # We only load if it is here to avoid triggering a warning
        FAMILIES_FILES = glob(op.join(CONF['root'], DEFAULT_FAMILIES_GLOB))
        if FAMILIES_FILES:
            # File is here, we add it to the conf and load it
            CONF['families'] = FAMILIES_FILES[0]
            load_families(DATA, FAMILIES_FILES[0])

# Exporting configuration file, except the 'export_*' attributes
if CONF['export_conf'] is not None:
    export_conf(CONF, CONF['export_conf'],
                exclude=('export_conf', 'export_families'))

# Exporting families file
if CONF['export_families'] is not None:
    export_families(DATA, CONF['export_families'])

# All operations on the tree who must be done after loading
post_load(DATA)

# CSS themes
THEMES = load_themes(ASSETS)
CONF['theme'] = check_theme(CONF['theme'], THEMES)

# Caching for autocomplete
TAGS = load_tags(DATA, CONF['keep'])

if CONF['verbose']:
    show_conf(CONF)
    show_themes(THEMES)
    print(dump_data(DATA))
    show_tags(TAGS, CONF['keep'])

# Caching total number of graphs
NB_GRAPHS = sum(len(n.data['graphs']) for _, n in DATA.iter_all_nodes())


# PREPARING APP
#
format_ = '[%(asctime)s] [%(levelname)s] %(message)s'
handler = logging.FileHandler(CONF['logfile'])
handler.setFormatter(logging.Formatter(format_))
handler.setLevel(logging.INFO)

app = Flask(__name__)
app.secret_key = 'jlrgh(*&)(&$)(#*$&'
app.logger.addHandler(handler)
app.after_request(after_request_log)
app.jinja_env.add_extension('jinja2.ext.do')


# CUSTOM Markdown Jinja filter
#
app.template_filter('md')(md_convert)
app.template_filter('mdi')(md_iconvert)  # inline version, no surrounding <p>


# CUSTOM Sort filters
#
app.template_filter('sortsons')(sort_sons)
app.template_filter('sortlabels')(sort_labels)
app.template_filter('sortindexes')(sort_indexes)

# CUSTOM functions for urls in templates
#
up_paths = DATA.iter_upper_paths


def get(p):
    return DATA.get_from_path(p).data


# ROUTES
#
@app.route('/')
def index():
    return redirect(url_for('family_index'))


@app.route('/family/')
@app.route('/family/<path:family>')
def family_index(family=None):
    if family is None:
        family_tuple = ()
    else:
        family_tuple = tuple(family.rstrip('/').split('/'))

    node = DATA.get_from_path(family_tuple)
    if node is None:
        abort(404)

    kw = {
        'conf'    : CONF,
        'family'  : family_tuple,
        'text'    : node.data['text'],
        'get'     : get,       # global function
        'up_paths': up_paths,  # global function
    }

    if CONF['headless']:
        return render_template('index.html', sons={}, **kw)

    if node.data['graphs']:
        return render_template('family.html', graphs=node.data['graphs'], **kw)

    if not node.sons:
        flash('Nothing could be loaded from {0}'.format(CONF['root']))
    return render_template('index.html', sons=node.sons, **kw)


@app.route('/tags')
def get_tags():
    return jsonify({
        'tags': TAGS,
    })


@app.route('/map')
def get_map():
    return Response(dump_data(DATA, True) + '\n' + dump_data(DATA, False),
                    mimetype='text/plain')


@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.html', conf=CONF), 404


# STATIC FILES
#
MIMETYPES = {
    '.yaml': 'text/plain',
    '.yml': 'text/plain',
}


@app.route('/data/<path:filename>')
def get_data(filename):
    ext = op.splitext(filename)[1].lower()
    return send_from_directory(CONF['root'], filename, mimetype=MIMETYPES.get(ext))


@app.route('/assets/<path:filename>')
@cache(60)  # 1 min cache cache to avoid problems on assets update
def get_asset(filename):
    return send_from_directory(ASSETS, filename)


# SEARCH
#
@app.route('/search')
def search():
    value = request.args.get('value', '')

    # If words are after a pipe (|), we isolate them for another query
    inner_value = value.partition('|')[0].strip()
    outer_value = value.partition('|')[2].replace('|', ' ').strip()

    results = search_results(build_query(inner_value + ' ' + outer_value))
    if outer_value:
        nb_total = search_results(build_query(outer_value))['nb_matches']
    else:
        nb_total = NB_GRAPHS

    ratio = 100 * results['nb_matches'] / float(nb_total) if nb_total != 0 else 0

    results.update({
        'inner_value' : inner_value,
        'outer_value' : outer_value,
        'nb_total'    : nb_total,
        'ratio'       : '{0:.2f}'.format(ratio),
    })
    return jsonify(results)


def memoize(function):
    memo = {}

    def wrapper(*args):
        if args not in memo:
            memo[args] = function(*args)
        return memo[args]
    return wrapper


def quote_aware_split(value):
    try:
        # shlex.split preserves quoting when splitting, and removes quotes
        res = shlex.split(value)
    except ValueError:
        # May happen when unbalanced quoting
        res = value.split()
    return res


Query = namedtuple('Query', ['keywords', 'freetext'])
Words = namedtuple('Words', ['include', 'exclude'])


@memoize
def build_query(value):
    # Building mutable version of query
    q = {
        'keywords': {'exclude': set(), 'include': set()},
        'freetext': {'exclude': set(), 'include': set()},
    }

    for w in quote_aware_split(value.lower()):
        # Deciding positive or negative group
        sign = 'exclude' if w.startswith('-') else 'include'
        group = 'keywords' if w.lstrip('-').startswith('#') else 'freetext'
        q[group][sign].add(w.lstrip('-'))

    # Make immutable
    for group in q:
        for sign in q[group]:
            q[group][sign] = frozenset(q[group][sign])
        q[group] = Words(**q[group])
    return Query(**q)


def is_in_any(w, args):
    return any(w in arg for arg in args)


def is_not_in(w, args):
    return all(w not in arg for arg in args)


@memoize
def search_results(query):
    # Storing results here
    matches = defaultdict(list)
    aliases = {}
    nb_matches = 0

    for family_tuple, node in DATA.iter_all_nodes():
        family_path_low = '/'.join(family_tuple).lower()
        family_alias_low = '/'.join(
            get(p)['alias'] for p in up_paths(family_tuple, include_root=False)
        ).lower()

        for graph_data in node.data['graphs']:
            graph_title_low = graph_data['title'].lower()
            graph_keywords = set(w.lower() for w in graph_data['index'])
            # Tuple where the freetext is looked for
            t = family_path_low, family_alias_low, graph_title_low, graph_keywords

            if (graph_keywords.issuperset(query.keywords.include) and
                    graph_keywords.isdisjoint(query.keywords.exclude) and
                    all(is_in_any(w, t) for w in query.freetext.include) and
                    all(is_not_in(w, t) for w in query.freetext.exclude)):

                nb_matches += 1
                if CONF['headless']:
                    continue

                if family_tuple not in matches:
                    # We want to keep aliases for all parent nodes
                    # This is needed for links, client-side
                    for p in up_paths(family_tuple, include_root=False):
                        aliases['/'.join(p)] = get(p)['alias']

                # matches will be jsonified and tuple keys are not allowed
                # So we use the path as key
                family_path = '/'.join(family_tuple)

                matches[family_path].append({
                    'title' : md_iconvert(graph_data['title']),
                    'text'  : graph_data['text'],
                    'labels': sort_labels(graph_data['labels']),
                    'id'    : graph_data['id'],
                })

    return {
        'matches'   : matches,
        'families'  : sorted(matches, key=lambda s: s.lower()),
        'aliases'   : aliases,
        'nb_matches': nb_matches,
    }
