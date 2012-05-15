# -=- encoding: utf-8 -=-

"""Configuration handler for SFL-F2T files.

Sample file:

config:
  zimbra:
    login: alexandre.bourget
    ics: https://mail.savoirfairelinux.com/home/alexandre.bourget@savoirfairelinux.com/Calendar
  private:
    login: abourget
    url: https://private.savoirfairelinux.com
  redmine:
    login: abourget
    url: https://projects.savoirfairelinux.com

tags:
  vente:
    private:
      push: true
      type: Vente
      client_id: 57
      bh: 768
  udem:
    private:
      push: true
    redmine:
      push: true
      project: udem-futursetudiants
#
# --- REWRITE POINT ---  Anything after this line will be re-written
#
timesheet:
  2012-05-05:
    - h: 3
      tag: vente
      desc: MyEvent et autres choses
    - h: 5
      tag: udem
      unit: #10834 or 10824 or RM10824
      desc: Ticket qu'il y avait à faire

"""

import os
import yaml
from collections import OrderedDict
import argparse

def load_plugins():
    # Loop entry points, create Plugin objects, and return the list
    from pkg_resources import iter_entry_points
    plugins = []
    for ep in iter_entry_points('sflf2t.plugins'):
        module = ep.load()
        new_plugin = Plugin(module)
        if not hasattr(module, 'plugin_name'):
            print "WARNING, plugin %s at location %s doesn't have a `plugin_name` and is probably not a SFL-F2T plugin" % (ep.name, module.__file__)
            continue
        plugins.append(new_plugin)
    return plugins

def get_config_filename():
    """Return the configuration file name"""
    filename = os.environ.get('SFLF2T', '~/.sflf2t')
    realname = os.path.realpath(os.path.expanduser(filename))
    return realname

def load_configuration(filename):
    """Read the config file"""
    # Use the os.environ to use the SFLF2T env var, fall back to ~/sfl.f2t
    config = Config(filename)
    return config

def get_command_line_parser(config, plugins):
    """Load argparser from each plugins if required"""
    parser = argparse.ArgumentParser(description='SFL-F2T')
    subparser = parser.add_subparsers(help="subcommands")
    parser_add = subparser.add_parser('add', help="Add a new entry")
    parser_fetch = subparser.add_parser('fetch', help="Fetch time entries")
    parser_edit = subparser.add_parser('edit', help="Edit time sheet file and settings")
    parser_submit = subparser.add_parser('submit', help="Submit time entries")
    parser_merge = subparser.add_parser('merge', help="Merge time entries")
    parser_split = subparser.add_parser('split', help="Split time entries")
    parser_search = subparser.add_parser('search', help="Search metadata and resolve ambiguities")
    parser_preview = subparser.add_parser('preview', help="Preview time sheet")
    parser_submit = subparser.add_parser('submit', help="Submit time sheet (after preview)")

    for plugin in plugins:
        plugin.add_subcommand('fetch', parser_fetch)
        plugin.add_subcommand('preview', parser_preview)
        plugin.add_subcommand('submit', parser_submit)

    
def write_timesheet(filename, timesheet):
    """Write only the timesheet section, while preserving the
    config and tag sections.
    """
    # Sort out timesheet (taken from config.timesheet probably ?)
    # Group by date
    # dump in YAML,
    # rewrite in filename at REWRITE POINT
    # yaml.dump({may: [{'h': 3, 'tag': 'vente', 'desc': u"Hey c'est cool ça", "unit": "Bob"}, {'h': 4, 'tag': 'udem', 'desc': "Stuff", 'unit': '10834'}]}, default_flow_style=False)
    # see  old sflf2t __init__.py at 49% (search REWRITE POINT)
    pass

    
class Config(object):
    def __init__(self, filename, plugins):
        self.filename = filename
        self.plugins = plugins

    def read_data(self):
        """Do the actual reading"""
        self.data = yaml.load(open(self.filename).read())
        self.timesheet = []
        for date, entries in self.data['timesheet'].iteritems():
            for time_entry in entries:
                self.timesheet.append(TimeEntry(date, **time_entry))

    def get_password(self, realm, prompt):
        """Get the password for a particular service, ex.
        redmine, private, zimbra, etc.  Keeping the realm here
        allows us to cache, or eventually to offload to a
        Wallet/Keyring/Password manager
        """
        if not hasattr(self, 'passwords'):
            self.passwords = {}
        if realm in self.passwords:
            return self.passwords[realm]
            
        import getpass
        new_pass = getpass.getpass(prompt)
        
        self.passwords[realm] = new_pass
        return new_pass
        
    def get(self, dotted_key, default=None, prefix="config"):
        """Return a key for an element specified as:

           private.key

        which should return:

          self.data['config']['private']['key']

        if it exists, otherwise the 'default' value. This is
        assuming ``prefix`` == 'config'.
        """
        subtree = self.data
        if prefix:
            subtree = subtree[prefix]

        for key in dotted_key.split('.'):
            if key not in subtree:
                return default
            else:
                subtree = subtree[key]
        return subtree

    def get_override(self, dotted_key, timesheet, default=None):
        """Get a value from the configuration, that might
        be overridden by a timesheet."""
        out = timesheet.get(dotted_key)
        if out is None:
            out = self.get(dotted_key, prefix="config")
        return out
        

class TimeEntry(OrderedDict):
    """Default object for TimeEntry

    Known keys:
    - date, hours, tag, unit, desc

    and from plugins you can have overrides for global config, like:

      private:
        bh: 123
    """
    def __init__(self, date, **kwargs):
        self['date'] = date
        self.update(kwargs)

    def get(self, dotted_key, default=None):
        """Return a key for an element specified as:

           private.key

        which should return:

          self['private']['key']

        if it exists, otherwise the 'default' value.
        """
        subtree = self
        for key in dotted_key.split('.')
            if key not in subtree:
                return default
            else:
                subtree = subtree[key]
        return subtree

        
class Plugin(object):
    def __init__(self, module):
        self.name = module.plugin_name
        self.is_searcher = hasattr(module, 'searcher')
        self.is_fetcher = hasattr(module, 'fetcher')
        submitter_vals = (hasattr(module, 'submitter_prepare'),
                       hasattr(module, 'submitter_review'),
                       hasattr(module, 'submitter_post'))
        if any(submitter_vals) and not all(submitter_vals):
            print "WARNING: module %s doesn't implement all the submitter functions (_prepare, _review and _submit)" % self.name
        self.is_submitter = all(submitter_vals)
        self.module = module

    def initialize(self, config, parser):
        """Initialize the plugin if it has an initialize() method"""
        if hasattr(self.module, 'initialize'):
            return self.module.initialize(config)

    def add_subcommand(self, operation, parser):
        """Call things like 'add_subcommand_fetch' on plugins."""
        method = 'add_subcommand_%s' % operation
        if hasattr(self.module, method):
            getattr(self.module, method)(parser)