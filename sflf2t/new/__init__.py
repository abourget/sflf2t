# -=- encoding: utf-8 -=-

"""Functionalities to the core Timesheet manager.

- Add (a new timesheet entry)
- Fetch (from fetcher plugins, like Zimbra, Hamster, etc..)
- Edit (launch a text editor on configuration)
  - Reload our config upon return
- Split
- Merge
- Search (metadata from searcher plugins)
- Preview (with pusher plugins)
- Submit
  - Mark the timesheet entries as submitted, to each plugin
    After submission, write back to the timesheet file

Boot sequence:
 - Load plugins
 - Load configuration

"""

import sys
from sflf2t.new.config import (load_configuration, get_config_filename,
                               load_plugins, get_command_line_parser)

def main():
    # Load everything
    plugins = load_plugins()
    config_filename = get_config_filename()
    config = load_configuration(config_filename, plugins)
    config.read_data()

    # Init all plugins
    for plugin in plugins:
        plugin.initialize(config)
        
    # parse command line
    parser = get_command_line_parser(config, plugins)
    args = parser.parse_args()

    functions = ('add', 'resolve', 'edit', 'split', 'merge', 'fetch',
                 'preview', 'submit')
    if args[0] not in functions:
        print "Commands:", functions
        sys.exit(1)

    # Add: do it directly
    # Fetch: all ? if no subcommand ?
    # Edit: do it directly
    # Merge: do it locally
    # Split: do it locally
    # Search: all ?
    # Preview: all ?
    # Submit all ?
