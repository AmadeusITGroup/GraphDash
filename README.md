GraphDash
=========

![](docs/example.gif)

Introduction
------------

`GraphDash` is a web-based dashboard built on graphs and their metadata.
For example, if you have in a directory:

```bash
$ ls example_graph_dir
graph.svg
graph.txt
```

The svg file is the graph, and must have metadata with YAML format:

```bash
$ cat example_graph_dir/graph.txt
name: graph.svg
title: "A nice graph"
family: Weather
text: This is the text under the graph.
```

You can put as many graphs as you want in the directory, then start the
graph dashboard. You will get a web interface with search box,
autocompletion and easy navigation.

```bash
GraphDash -r example_graph_dir
```

Installation
------------

Clone and install (in user space):

```bash
git clone https://github.com/AmadeusITGroup/graphdash.git
cd graphdash
pip install --user .
```

Or install in a `virtualenv`:

```bash
virtualenv --clear --no-site-packages .env
source .env/bin/activate
pip install .
```

Launch the webapp
-----------------

Just do (`$PATH` should include `~/.local/bin` if installation in user
space):

```bash
GraphDash -r example_graph_dir
```

The dashboard can be configured with a configuration file like this
(also YAML):

```bash
$ cat example.conf
root: example_graph_dir
title: "Default title"
subtitle: "Default subtitle"
```

Then use `-c` to use it:

```bash
GraphDash -c example.conf
```

You can generate a template of configuration file like this:

```bash
GraphDash -C template.conf
```

Serve with Gunicorn
-------------------

If not already installed on your machine, install `Gunicorn`:

```bash
# On Fedora you may need to do beforehand as root: yum install libffi-devel
pip install --user gunicorn
```

You can import the webapp through `graphdash:app`, so using `Gunicorn`:

```bash
gunicorn -b 0.0.0.0:8888 --pid server.pid graphdash:app &
```

The configuration file of the webapp can be searched using the `CONF`
environment variable. With `Gunicorn`, you can pass environment variables
to the workers with `--env`, so you can do:

```bash
gunicorn -b 0.0.0.0:8888 --pid server.pid --env CONF=example.conf graphdash:app &
```

With `Gunicorn`, you can restart the server by sending a `HUP` signal:

```bash
kill -HUP `cat server.pid` # restart !
```

Webapp configuration file
-------------------------

Possible entries (everything is optional):

-   root: the root directory of the graphs
-   families: path to the families metadata file (optional)
-   title: the title of the webapp
-   subtitle: the subtitle of the webapp
-   placeholder: the default text in the search field
-   header: an optional message at the top (markdown syntax)
-   footer: an optional message at the bottom (markdown syntax)
-   showfamilynumbers: a boolean to toggle family numbering (default is true)
-   showgraphnumbers: a boolean to toggle graph numbering (default is true)
-   theme: change css theme (default is dark)
-   keep: the proportion of common words kept for autocompletion
-   logfile: change default log file of the webapp
-   raw: when loading, look for all graphs and ignore txt metadata
-   verbose: a boolean indicating verbosity when loading application
-   debug: debug mode (enable Grunt livereload, enable Flask debug mode)
-   headless: headless mode (only search is available, no page is rendered)
-   port: when launched with Flask development server only, port

Graph metadata
--------------

Several attributes are supported:

-   name: the path to the graph
-   title: title of the graph, recommended for display purposes (markdown syntax)
-   family: the subsection in which the graph is
-   index: an optional list of keywords describing the graph (useful for search feature)
-   text: an optional description of the graph (markdown syntax)
-   pretext: an optional message appearing before the graph (markdown syntax)
-   file: optional path to the raw data
-   export: optional path to the exportable graph (for example, a PNG file)
-   rank: integer, optional value used to change graphs order (default uses titles)
-   showtitle: a boolean to toggle title display for the graph (default is false)
-   labels: a list of labels (like 'new') which will be rendered in the UI as colored circles
-   other: other metadata not used by GraphDash, but may be needed by other things reading the txt files

Note that if the `name` attribute is missing, the graph will not be
shown and the text will be displayed anyway, like a blog entry.

Family metadata
---------------

You may put a `.FAMILIES.txt` file at the root of the graph directory.
This file may contain metadata for families. It should be a YAML list
like this:

```yaml
- family: Chairs
  rank : 1
- family: Tables
  rank : 0
  text: This is a description
  alias: This text will appear instead of other_family
  labels: new
```

Each element of the list should be a dict containing:

-   family: the family considered
-   rank: integer, optional value used to change families order (default
    uses family name)
-   text: an optional description of the family (markdown syntax)
-   alias: an optional name who may be longer than the one in the url
    (useful to build nice urls)
-   labels: a list of labels (like 'new') which will be rendered in the
    UI as colored circles

Available labels are "new", "update", "bugfix", "warning", "error",
"ongoing", "obsolete". You may give other labels which will be rendered
with defaults colors. For customization, you may specify your own labels
with a dict syntax:

```yaml
labels:
- name: newlabel
  color: white
  text_color: black
  text: "NEW LABEL"
  tooltip: null
```

CLI
---

You can override almost any parameter from the CLI, make sure to check
`GraphDash --help`.

Manager script
--------------

The manager script `GraphDashManage` is used to start|stop|restart the
instances of `Gunicorn` serving `graphdash:app`. It needs a
configuration file like this in the current directory:

```bash
$ cat settings.sh
ALL_MODES=(
   ['prod']="example.conf"
   ['test']="example.conf"
)

ALL_PORTS=(
   ['prod']=1234
   ['test']=5678
)
```

You can generate a template of such file with:

```bash
$ GraphDashManage template > template.sh # to be moved to settings.sh
```

Then you can use the script to manage multiple instances of `GraphDash`
(with `Gunicorn`):

```bash
$ GraphDashManage start prod
$ GraphDashManage start test
$ GraphDashManage reload test
$ GraphDashManage
Usage: GraphDashManage (start|stop|restart|forcestop|reload|status|fullstatus|template) [mode1 [mode2...]]

Use Gunicorn to serve GraphDash instances described in settings.sh.

start       : start servers
stop        : gracefully stop servers (QUIT signal)
restart     : gracefully stop servers (QUIT signal), wait for processes to finish, then start servers
forcestop   : force stop servers (KILL signal)
reload      : reload servers (HUP signal)
increment   : increment number of workers (TTIN signal)
decrement   : decrement number of workers (TTOU signal)
status      : display status of servers
fullstatus  : display status of all servers
template    : display a template of settings.sh file
```

Development
-----------

If you wish to contribute, you need `Grunt` to generate new css/js files
from sass/coffee source files.

```bash
npm install --no-bin-links # may need to repeat
grunt
```

Debugging can be made with source map files for browser supporting them
in their debugging tools. If not, the `Gruntfile.js` enables an option
to generate non-minified assets.

```bash
grunt --dev
```

With the `debug` mode enabled, Grunt will use the livereload mechanism
to reload the browser if any file has changed (and Flask debug mode will
reload the server as well).

```bash
GraphDash --debug & # or python -m graphdash
grunt watch
```

If you used `Gunicorn` with a PID file, Grunt will automatically reload it
if any Python files change.

```bash
gunicorn -b 0.0.0.0:8888 --pid server.pid graphdash:app &
grunt watch
```

You can use `tox` build packages and run tests.

```bash
tox
```
