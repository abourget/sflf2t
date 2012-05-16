# -=- encoding: utf-8 -=-

"""Implement the glue to tie the plugins together."""

# TODO: use argparse to parse the command line

# TODO: implement the shell-like thing that will allow us to
#       call the different modules.

import os

def execute_add(config, args):
    pass

def execute_submit(config, args):
    use_plugins = _plugins_with_support('submitter', limit=args.plugins)

def execute_preview(config, args):
    use_plugins = _plugins_with_support('submitter', limit=args.plugins)
    for plugin in use_plugins:
        plugin.execute_preview(args)

def execute_fetch(config, args):
    use_plugins = _plugins_with_support('fetcher', limit=args.plugins)

def execute_search(config, args):
    use_plugins = _plugins_with_support('searcher', limit=args.plugins)

def execute_edit(config, args):
    from sflf2t.config import get_config_filename
    editor = os.environ.get('EDITOR', 'vi')
    config_filename = get_config_filename()
    os.system("%s %s" % (editor, config_filename))


def _plugins_with_support(config, feature, limit=None):
    """Get plugins with specific features or specific plugin

    :param feature: some or 'searcher', 'fetcher', 'submitter'
    """
    plugins = config.plugins
    if limit:
        plugins = [plugin for plugin in plugins
                   if plugin.short_name in limit]

    res = [plugin for plugin in plugins
           if plugin.has_feature(feature)]
    
    return res
    