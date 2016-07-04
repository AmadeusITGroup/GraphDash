# -*- coding: utf-8 -*-

from __future__ import with_statement, print_function

import sys
import os
import os.path as op
from operator import itemgetter

import yaml

from .struct.defaulttransformdict import DefaultTransformDict
from .struct.tree import Tree
from .nlp import Cleaner, StopWords
from .defaults import (DEFAULT_FAMILY, SINK, get_parser,
                       default_graph_data, default_family_data,
                       default_label_data)

if sys.version_info[0] >= 3:
    unicode = str


def is_hidden(filepath):
    return op.basename(filepath).startswith('.')


def check_ext(filepath, extensions):
    return any(filepath.lower().endswith(e) for e in extensions)


def iter_all_files(data_dir, extensions=None, hidden=False):
    """Scan all files with some extensions."""
    if extensions is not None:
        extensions = [e.lower() for e in extensions]

    for root, _, files in os.walk(data_dir, topdown=False, followlinks=True):
        if not hidden and is_hidden(root):
            continue
        for f in files:
            if not hidden and is_hidden(f):
                continue
            if extensions is None or check_ext(f, extensions):
                yield op.join(root, f)


def load_args():
    """Loading command line arguments."""
    if op.basename(sys.argv[0]) == 'gunicorn':
        # If imported through Gunicorn, argparse will receive gunicorn
        # arguments, like the name of the loaded Flask app, and this will
        # cause this parser to fail.
        # So we act like nothing was passed.
        args = {}
    else:
        args = vars(get_parser().parse_args())

    # If an option was not enforced, we do not want it to appear
    # in the dict at all, since this dict will be used to override
    # configuration from file
    enforced_args = {}

    for key, value in args.items():
        # None value is default, only other values are enforced
        if value is not None:
            enforced_args[key] = value

    return enforced_args


# These types can hold value types:
# (int, float, long, complex, bool, basestring, dict)
CONTAINER_TYPES = (set, list, tuple)


def sanitize(value, apply_=lambda e: e, filter_=lambda _: True):
    if not isinstance(value, CONTAINER_TYPES):
        value = [value]

    return [apply_(e) for e in value if filter_(e)]


def replace_char(name, old, new):
    if old not in name:
        return name
    else:
        new_name = name.replace(old, new)
        print(('(!) Illegal char "{0}" in "{1}", '
               'replacing with "{2}"').format(old, name, new_name))
        return new_name


# We force unicode on urls, index, label names
def handle_family(family):
    return replace_char(unicode(family), '/', '-')


def handle_index(index):
    return '#' + replace_char(unicode(index), ' ', '_')


def load_conf(conf_file):
    """Loading configuration file."""
    if not conf_file:
        print('( ) No configuration file provided')
        return {}

    print('( ) Loading {0}'.format(conf_file))
    if not op.isfile(conf_file):
        print('(!) File "{0}" does not exist'.format(conf_file))
        return {}

    try:
        with open(conf_file) as f:
            conf = yaml.load(f)

    except yaml.YAMLError:
        print('(!) {0} parsing failed (YAML dict expected)'.format(conf_file))
        conf = {}

    if not isinstance(conf, dict):
        print('(!) {0} did not contain a YAML dict'.format(conf_file))
        conf = {}

    return conf


def export_conf(conf, conf_file, exclude=None):
    """Export configuration file."""
    exclude = set() if exclude is None else set(exclude)

    if not conf_file:
        print('( ) No configuration file provided')
        return

    if op.isfile(conf_file):
        print('(!) File "{0}" exists, skipping export'.format(conf_file))
        return

    with open(conf_file, 'w') as f:
        # The dict() is also to get rid of the SemiFrozenDict
        dumped = dict(item for item in conf.items()
                      if item[0] not in exclude)

        f.write(yaml.safe_dump(dumped, default_flow_style=False, allow_unicode=True))

    print('( ) File "{0}" created with configuration'.format(conf_file))


def load_families(data, family_file):
    """Loading families file."""
    if not family_file:
        print('( ) No families file provided')
        return

    print('( ) Loading {0}'.format(family_file))
    if not op.isfile(family_file):
        print('(!) File "{0}" does not exist'.format(family_file))
        return

    try:
        with open(family_file) as f:
            families = yaml.load(f)

    except yaml.YAMLError:
        print('(!) {0} parsing failed (YAML dict expected)'.format(family_file))
        families = []

    if not isinstance(families, list):
        print('(!) {0} did not contain a YAML list'.format(family_file))
        families = []

    for loaded in families:
        if not isinstance(loaded, dict):
            print('(!) "{0}" did not contain a YAML dict'.format(loaded))
            continue

        if 'family' not in loaded:
            print(('(!) Missing "family" key in file {0}, dict "{1}", '
                   'skipping').format(family_file, loaded))
            continue

        family_tuple = tuple(sanitize(loaded['family'], apply_=handle_family))
        del loaded['family']  # we do not want to update node.data

        node = data.get_from_path(family_tuple)
        if node is None:
            print('(!) Family {0} was not found in data'.format(family_tuple))
            continue

        node.data.update(loaded)


def coercedict(e):
    """Forcing dict conversion of dict subclasses (for labels)"""
    return dict(e) if isinstance(e, dict) else e


def export_families(data, family_file):
    """Export families file."""
    if not family_file:
        print('( ) No families file provided')
        return

    if op.isfile(family_file):
        print('(!) File "{0}" exists, skipping export'.format(family_file))
        return

    families = []

    for node_path, node in sorted(data.iter_all_nodes()):
        dumped = {'family': list(node_path)}
        for k in node.data:
            if k == 'graphs':
                continue
            if not node.data[k]:  # We do not dump default values
                continue
            if isinstance(node.data[k], CONTAINER_TYPES):
                dumped[k] = [coercedict(e) for e in node.data[k]]
            else:
                dumped[k] = coercedict(node.data[k])

        families.append(dumped)

    # default_flow_style=None (default) will dump lists one one line
    # Root dict will be expanded since they will contain a list
    with open(family_file, 'w') as f:
        f.write(yaml.safe_dump(families, allow_unicode=True))

    print('( ) File "{0}" created with families data'.format(family_file))


def load_data_raw(data_dir):
    """Loading data, directly looking for any graph."""
    data, nb_graphs = Tree(factory=default_family_data), 0

    if not op.isdir(data_dir):
        print('(!) {0} is not a directory'.format(data_dir))
        return data

    extensions = '.png .jpg .jpeg .bmp .eps .ps .svg .gif'.split()
    group_size = 10

    for filepath in iter_all_files(data_dir, extensions):
        # Number rounded to the closest 10/20/30/...
        c = int(nb_graphs / group_size) * group_size
        family_tuple = ("Graphs {0:6d}-{1:6d}".format(c + 1, c + group_size),)

        def rel(f):
            """Adjusting graph path to relative root from data_dir"""
            return op.relpath(op.join(op.dirname(filepath), f), data_dir)

        graph_data = default_graph_data()
        graph_data.update({
            'name' : rel(filepath),
            'title': op.basename(filepath),
        })

        node = data.create_from_path(family_tuple)
        node.data['graphs'].append(graph_data)
        nb_graphs += 1

    print('( ) {0} graphs loaded from {1}'.format(nb_graphs, data_dir))
    return data


def load_data(data_dir):
    """Loading data parsing conf files."""
    data, nb_graphs = Tree(factory=default_family_data), 0

    if not op.isdir(data_dir):
        print('(!) {0} is not a directory'.format(data_dir))
        return data

    for filepath in iter_all_files(data_dir, ['.txt', '.yaml', '.yml']):
        try:
            with open(filepath) as f:
                loaded = yaml.load(f)

        except yaml.YAMLError:
            print('(!) {0} parsing failed (YAML dict expected), skipping'.format(filepath))
            continue

        if not isinstance(loaded, dict):
            print('(!) {0} did not contain a YAML dict'.format(filepath))
            continue

        if 'family' not in loaded:
            family_tuple = DEFAULT_FAMILY
        else:
            family_tuple = tuple(sanitize(loaded['family'], apply_=handle_family))
            del loaded['family']  # we do not want to update graph_data

        if 'name' not in loaded:
            print('( ) {0} had no "name" attribute, processing as text entry'.format(filepath))

        graph_data = default_graph_data()
        graph_data.update(loaded)

        def rel(f):
            """Adjusting graph path to relative root from data_dir"""
            return op.relpath(op.join(op.dirname(filepath), f), data_dir)

        for p in 'name', 'file', 'export':
            if graph_data[p]:
                graph_data[p] = rel(graph_data[p])

        node = data.create_from_path(family_tuple)
        node.data['graphs'].append(graph_data)
        nb_graphs += 1

    print('( ) {0} graphs loaded from {1}'.format(nb_graphs, data_dir))
    return data


def no_mix(data, sink=None):
    """Process of changing the tree to have either data of nodes, not both."""
    for node_path, node in data.iter_all_nodes():
        if node.sons and node.data['graphs']:
            # Moving graphs to the sink
            print(('(!) Family {0} had both sub-families and graphs, '
                   'moving graphs to sub-family "{1}"').format(node_path, sink))

            sink_node = node.create_from_path((sink,))
            sink_node.data['graphs'].extend(node.data['graphs'])
            node.data['graphs'] = []


def fill_missing_infos(data):
    """We fill missing alias/rank information."""
    for node_path, node in data.iter_all_nodes():
        if node.data['alias'] is None:
            node.data['alias'] = node_path[-1] if node_path else ''
        if node.data['rank'] is None:
            node.data['rank'] = node.data['alias'].lower()

        for graph_data in node.data['graphs']:
            if graph_data['rank'] is None:
                graph_data['rank'] = graph_data['title'].lower()


SOLARIZED = {
    'base03'  : '#002b36',
    'base02'  : '#073642',
    'base01'  : '#586e75',
    'base00'  : '#657b83',
    'base0'   : '#839496',
    'base1'   : '#93a1a1',
    'base2'   : '#eee8d5',
    'base3'   : '#fdf6e3',
    'yellow'  : '#b58900',
    'orange'  : '#cb4b16',
    'red'     : '#dc322f',
    'magenta' : '#d33682',
    'violet'  : '#6c71c4',
    'blue'    : '#268bd2',
    'cyan'    : '#2aa198',
    'green'   : '#859900',
}

KNOWN_LABELS = {
    'ongoing'  : ('ON-GOING',  'white', SOLARIZED['green']),
    'new'      : ('NEW',       'white', SOLARIZED['blue']),
    'update'   : ('UPDATE',    'white', SOLARIZED['blue']),
    'obsolete' : ('OBSOLETE',  'white', SOLARIZED['base01']),
    'bugfix'   : ('BUGFIX',    'white', SOLARIZED['orange']),
    'warning'  : ('WARNING',   'white', SOLARIZED['orange']),
    'error'    : ('ERROR',     'white', SOLARIZED['red']),
    'important': ('IMPORTANT', 'white', SOLARIZED['yellow']),
}


def handle_label(label):
    """Handle label input."""
    label_data = default_label_data()

    if isinstance(label, dict):
        label_data.update(label)

    elif label in KNOWN_LABELS:
        text, text_color, color = KNOWN_LABELS[label]
        label_data.update({
            'name'      : label,
            'text'      : text,
            'text_color': text_color,
            'color'     : color,
        })
    else:
        label_data.update({
            'name': label,
            'text': label,
        })
        print(('(!) Label {0!r} not in {1}, using default {2}'
               '').format(label, list(KNOWN_LABELS), label_data))

    # Label names are also used as index, hence must go through handle_index
    label_data['name'] = handle_index(label_data['name'])

    if label_data['tooltip'] is None:
        label_data['tooltip'] = u'Use {0} to search for this label.'.format(label_data['name'])

    return label_data


def enforce_types(data):
    """Convert lists to sets.
    """
    # We properly set 'title', 'text', 'pretext' and 'alias' as unicode
    for _, node in data.iter_all_nodes():
        # This avoid warnings about mix of types in 'rank' later
        if node.data['alias'] is not None:
            node.data['alias'] = unicode(node.data['alias'])

        for graph_data in node.data['graphs']:
            graph_data['title'] = unicode(graph_data['title'])
            graph_data['text'] = unicode(graph_data['text'])
            graph_data['pretext'] = unicode(graph_data['pretext'])

    # We properly set 'index' as a set
    for _, node in data.iter_all_nodes():
        for graph_data in node.data['graphs']:
            graph_data['index'] = set(sanitize(graph_data['index'], apply_=handle_index))

    # We properly set 'labels' as a set of dict
    for _, node in data.iter_all_nodes():
        node.data['labels'] = set(sanitize(node.data['labels'], apply_=handle_label))

        for graph_data in node.data['graphs']:
            graph_data['labels'] = set(sanitize(graph_data['labels'], apply_=handle_label))


def propagate_labels(data):
    """Labels propagation."""
    for _, node in data.iter_all_nodes():
        # Down
        for _, child in node.iter_all_nodes():
            child.data['labels'] |= node.data['labels']
            for graph_data in child.data['graphs']:
                graph_data['labels'] |= node.data['labels']
                for label in graph_data['labels']:
                    graph_data['index'].add(label['name'])

        # Up
        for parent in node.iter_all_parents():
            parent.data['labels'] |= node.data['labels']

        for graph_data in node.data['graphs']:
            node.data['labels'] |= graph_data['labels']
            for parent in node.iter_all_parents():
                parent.data['labels'] |= graph_data['labels']
            # We add labels to indexes for search
            for label in graph_data['labels']:
                graph_data['index'].add(label['name'])


def sort_graphs(data):
    """Sort graphs and set graph ids."""
    for node_path, node in data.iter_all_nodes():
        # We warn about type mixing in graph ranks
        ranks = [graph_data['rank'] for graph_data in node.data['graphs']]

        if len(set(type(r) for r in ranks)) > 1:
            print(('(!) Mix of types found in graphs ranks for {0}: {1}, '
                   'skipping sort').format(node_path, ranks))
        else:
            # We sort the graphs based on their ranks
            node.data['graphs'].sort(key=itemgetter('rank'))

        # We attribute the ids of graphs based on their ranks
        for i, graph_data in enumerate(node.data['graphs'], start=1):
            graph_data['id'] = i

        # We warn about type mixing in family ranks
        ranks = [node.sons[s].data['rank'] for s in node.sons]

        if len(set(type(r) for r in ranks)) > 1:
            print(('(!) Mix of types found in families ranks for {0}: {1}, '
                   'using ranks as strings').format(node_path, ranks))

            for s in node.sons:
                node.sons[s].data['rank'] = unicode(node.sons[s].data['rank'])


def post_load(data):
    """Here are all operations on the tree that must be done after loading.
    """
    no_mix(data, sink=SINK)
    enforce_types(data)
    fill_missing_infos(data)
    propagate_labels(data)
    sort_graphs(data)


# Almost all punctuation except -+/%_
REMOVED_CHARS = ' \t\n\r\v\f!"\'#$&()*,.:;<=>?@[\\]^`{|}~'
PUNCTUATION_LEFT = set('-+/%_')  # these were not removed

CLEANER = Cleaner(REMOVED_CHARS)
STOP_WORDS = StopWords('english')


def yield_clean_words(string):
    for word in string.split():
        word = CLEANER.clean(word)
        if not word or word.isdigit() or set(word).issubset(PUNCTUATION_LEFT):
            continue
        if word.lower() in STOP_WORDS:
            continue
        yield word


def load_tags(data, keep):
    """For autocomplete."""
    keywords = set()
    words = DefaultTransformDict(int, lambda s: s.lower())

    for family_tuple, node in data.iter_all_nodes():
        for word in yield_clean_words(' '.join(family_tuple)):
            words[word] += 1
        for word in yield_clean_words(node.data['alias']):
            words[word] += 1

        for graph_data in node.data['graphs']:
            for word in yield_clean_words(graph_data['title']):
                words[word] += 1
            for kw in graph_data['index']:
                keywords.add(kw)

    # We only keep the words who appeared the most in graph names and families
    nb_kept_words = int(keep * len(words))
    kept_words = sorted(words, key=lambda k: words[k])[-nb_kept_words:]
    return sorted(list(keywords) + kept_words,
                  key=lambda k: k.lstrip('#').lower())


def load_themes(themes_dir):
    """Loading possible themes."""
    themes = set()

    for filepath in iter_all_files(themes_dir, ['.css']):
        # We get rid of all suffixes like .min.css and .css
        basename = op.basename(filepath).split('.')[0]

        # Only files prepended with theme_ are considered themes
        if basename.startswith('theme_'):
            themes.add(basename.lstrip('theme_'))

    return sorted(themes)


def check_theme(theme, themes):
    """Check if theme is legit.
    """
    if theme in themes:
        return theme

    print(('(!) Theme "{0}" not in {1}, '
           'using "{2}"').format(theme, themes, themes[0]))
    return themes[0]


def show_conf(conf):
    print('\n* Configuration loaded:')
    for k in sorted(conf):
        print('{0!r:20s} : {1!r}'.format(k, conf[k]))


def show_tags(tags, keep):
    print('\n* {0} tags (keep {1:.1f}%):'.format(len(tags), 100 * keep))
    print('\n'.join(tags))


def show_themes(themes):
    print('\n* {0} themes found:'.format(len(themes)))
    print('\n'.join(themes))


# These functions are used to build custom sort filters
#
def sort_sons(items):
    """Sort sons from node.sons.items()"""
    return sorted(items, key=lambda it: it[1].data['rank'])


def sort_labels(labels):
    return sorted(labels, key=lambda l: (l['color'], l['name']))


def sort_indexes(indexes):
    return sorted(indexes, key=lambda i: (len(i), i))


def decorate(node_item):
    node_name, node = node_item
    return u'{0} [{1},{2}]'.format(node_name, len(node.data['graphs']), len(node.sons))


def dump_data(data, details=False):
    if details:
        def with_data(d):
            return [g['title'] for g in d['graphs']]
    else:
        with_data = None

    return '\n'.join([
        "\n* Tree [{0}]:".format('detailed' if details else 'simple'),
        data.prettify(decorate=decorate, with_data=with_data, sort_sons=sort_sons),
    ])
