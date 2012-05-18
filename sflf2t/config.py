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
import datetime
import yaml
from collections import OrderedDict
from itertools import groupby
import argparse

from sflf2t.core import (execute_add, execute_submit, execute_preview,
                         execute_edit, execute_fetch, execute_search,
                         execute_merge, execute_split)

def load_plugins():
    # Loop entry points, create Plugin objects, and return the list
    from pkg_resources import iter_entry_points
    plugins = []
    for ep in iter_entry_points('sflf2t.plugins'):
        module = ep.load()
        new_plugin = Plugin(ep.name, module)
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

def load_configuration(filename, plugins):
    """Read the config file"""
    # Use the os.environ to use the SFLF2T env var, fall back to ~/sfl.f2t
    config = Config(filename, plugins)
    return config

def get_command_line_parser(config, plugins):
    """Load argparser from each plugins if required"""
    parser = argparse.ArgumentParser(description='SFL-F2T')
    parser.set_defaults(command=None)
    subparsers = parser.add_subparsers(dest='command')

    sub_commands = (('add', "Add a new time entry", execute_add),
                    ('fetch', "Fetch time entries", execute_fetch),
                    ('edit', "Edit time sheet file and settings", execute_edit),
                    ('preview', "Preview time sheet", execute_preview),
                    ('submit', "Submit time sheet (previews first)",
                     execute_submit),
                    ('search', "Search metadata, resolve units/ambiguities",
                     execute_search),
                    ('merge', "Merge time entries", execute_merge),
                    ('split', "Split time entries", execute_split),
                    )
    
    cmdparsers = {}
    for cmd, help_msg, execute_func in sub_commands:
        subparser = subparsers.add_parser(cmd, help=help_msg)
        subparser.set_defaults(cmd_func=execute_func)
        cmdparsers[cmd] = subparser

    # Add specific arguments:
    cmdparsers['preview'].add_argument('plugins', nargs="*",
                                       help="Preview plugins only")
    cmdparsers['preview'].epilog = _plugins_parser_description(plugins,
                                                               'submitter')
    cmdparsers['submit'].add_argument('plugins', nargs="*",
                                      help="Submit plugins only")
    cmdparsers['submit'].epilog = _plugins_parser_description(plugins,
                                                              'submitter')
    cmdparsers['fetch'].add_argument('plugins', nargs="*",
                                      help="Submit plugins only")
    cmdparsers['fetch'].epilog = _plugins_parser_description(plugins,
                                                             'fetcher')

    for plugin in plugins:
        plugin.add_subcommand('fetch', cmdparsers['fetch'])
        plugin.add_subcommand('preview', cmdparsers['preview'])
        plugin.add_subcommand('submit', cmdparsers['submit'])
        plugin.add_subcommand('search', cmdparsers['search'])        

    return parser

def _plugins_parser_description(plugins, operation):
    desc = []
    for plugin in plugins:
        if plugin.has_feature(operation):
            desc.append(plugin.short_name)
    return ("%s plugins loaded: " % (operation)).title() + ", ".join(desc)
    
    
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
                new_entry = TimeEntry((('date', date),) +
                                      tuple(time_entry.iteritems()))
                self.timesheet.append(new_entry)

    def get_grouped_timesheet(self):
        self.timesheet.sort(key=lambda x: x['date'])
        res = []
        for key, vals in groupby(self.timesheet, key=lambda x: x['date']):
            res.append((key, list(vals)))
        return res
                
    def write_back(self):
        """Write only the timesheet section back to the file, while preserving
        the config and tag sections.
        """
        res = self.get_grouped_timesheet()
        from pprint import pprint
        pprint(res)
        # dump in YAML,
        # rewrite in filename at REWRITE POINT
        # yaml.dump({may: [{'h': 3, 'tag': 'vente', 'desc': u"Hey c'est cool ça", "unit": "Bob"}, {'h': 4, 'tag': 'udem', 'desc': "Stuff", 'unit': '10834'}]}, default_flow_style=False)
        # see  old sflf2t __init__.py at 49% (search REWRITE POINT)


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
        new_pass = getpass.getpass(prompt.strip() + " ")
        
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

    def plugins_with_support(self, feature, limit=None):
        """Get plugins with specific features or specific plugin

        :param feature: some or 'searcher', 'fetcher', 'submitter'
        """
        plugins = self.plugins
        if limit:
            plugins = [plugin for plugin in plugins
                       if plugin.short_name in limit]

        res = [plugin for plugin in plugins
               if plugin.has_feature(feature)]
    
        return res
    
    def show_timesheet(self):
        self.timesheet.sort(key=lambda x: x['date'])

        count = 0
        grouped_timesheet = self.get_grouped_timesheet()
        total_hours = 0
        for key, items in grouped_timesheet:
            sum_hours = sum(x['hours'] for x in items)
            total_hours += sum_hours
            print "     ====== {0} ======".format(items[0].format_date())
            for item in items:
                count += 1
                print " {0: >2}. {1}".format(count,
                                             item.show().encode('utf-8'))
                if item.metadata:
                    print "             `-> %s" % item.metadata
            if len(items) > 1:
                print "     = %.2fh" % sum_hours
        print "     ======"
        print "     %.2f hours total" % total_hours
        

class TimeEntry(OrderedDict):
    """Default object for TimeEntry

    Known keys:
    - date, hours, tag, unit, desc

    and from plugins you can have overrides for global config, like:

      private:
        bh: 123
    """
    def get(self, dotted_key, default=None):
        """Return a key for an element specified as:

           private.key

        which should return:

          self['private']['key']

        if it exists, otherwise the 'default' value.
        """
        subtree = self
        for key in dotted_key.split('.'):
            if key not in subtree:
                return default
            else:
                subtree = subtree[key]
        return subtree

    def __repr__(self):
        out = []
        for k, val in self.iteritems():
            if isinstance(val, unicode):
                val = val.encode('utf-8')
            out.append("%s=%s" % (k, val))
        return "<TimeEntry " + ', '.join(out) + ">"

    metadata = None
        
    def show(self):
        out = []

        dt = self.copy()
        dt.pop('date')
        hours = dt.pop('hours')
        tag = dt.pop('tag')
        desc = dt.pop('desc')
        unit = dt.pop('unit', None)

        out.append("%.2fh " % hours)
        if hours < 10:
            out.append(" ")  # align hours and tags
        out.append(tag)
        if unit:
            out.append(":%s" % unit)
        out.append(", ")
        out.append(desc)
        if dt:
            out.append(" (")
            out.append(", ".join("%s=%s" % (k, v) for k, v in dt.iteritems()))
            out.append(")")
        return ''.join(out)
        

    def format_date(self):
        date = self['date']
        today = datetime.date.today()
        delta = today - date
        if delta.days:
            delta_text = "%s days ago" % delta.days
        else:
            delta_text = "today"
        return ("%s, %s" % (date.strftime("%d %b, %a"), delta_text)).lstrip('0')


        
class Plugin(object):
    def __init__(self, short_name, module):
        self.short_name = short_name  # from the Entry point def.
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
        self.config = config
        if hasattr(self.module, 'initialize'):
            return self.module.initialize(config, parser)

    def add_subcommand(self, operation, parser):
        """Call things like 'add_subcommand_fetch' on plugins."""
        method = 'add_subcommand_%s' % operation
        if hasattr(self.module, method):
            getattr(self.module, method)(parser)

    def has_feature(self, feature):
        if feature == 'searcher':
            return self.is_searcher
        elif feature == 'submitter':
            return self.is_submitter
        elif feature == 'fetcher':
            return self.is_fetcher
        else:
            raise ValueError("feature should be 'searcher', 'submitter', "
                             "or 'fetcher'")

    def execute_preview(self, args):
        print "Previewing", args.plugins, self.module
        struct = self.module.submitter_prepare(self.config, args)
        return self.module.submitter_preview(struct)

    def execute_submit(self, args):
        struct = self.module.submitter_prepare(self.config, args)
        return self.module.submitter_preview(struct)

    def execute_fetch(self, args):
        return self.module.fetcher(self.config, args)