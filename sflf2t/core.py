# -=- encoding: utf-8 -=-

"""Implement the glue to tie the plugins together."""

# TODO: use argparse to parse the command line

# TODO: implement the shell-like thing that will allow us to
#       call the different modules.

import os

### Taken from fabric's color.py file, tweaked a little
has_term = os.environ.get('COLORTERM')
def _wrap_with(code):
    def inner(text, bold=False):
        c = code
        if bold:
            c = "1;%s" % c
        return "\033[%sm%s\033[0m" % (c, text)
    if has_term:
        return inner
    else:
        return lambda x: x
red = _wrap_with('31')
green = _wrap_with('32')
yellow = _wrap_with('33')
blue = _wrap_with('34')
magenta = _wrap_with('35')
cyan = _wrap_with('36')
white = _wrap_with('37')



#
# Main command line functions executers
#

def execute_add(config, args):
    menu_runner(config)
        

def execute_submit(config, args):
    use_plugins = config.plugins_with_support('submitter', limit=args.plugins)
    for plugin in use_plugins:
        plugin.execute_submit(args)

def execute_preview(config, args):
    use_plugins = config.plugins_with_support('submitter', limit=args.plugins)
    for plugin in use_plugins:
        plugin.execute_preview(args)

def execute_fetch(config, args):
    use_plugins = config.plugins_with_support('fetcher', limit=args.plugins)
    for plugin in use_plugins:
        print "Executing fetch for plugin %s" % plugin.short_name
        plugin.execute_fetch(args)

def execute_search(config, args):
    use_plugins = config.plugins_with_support('searcher', limit=args.plugins)
    for plugin in use_plugins:
        print "-> Searching with plugin %s" % plugin.short_name
        plugin.execute_search(args)

def execute_edit(config, args):
    from sflf2t.config import get_config_filename
    editor = os.environ.get('EDITOR', 'vi')
    config_filename = get_config_filename()
    os.system("%s %s" % (editor, config_filename))

def execute_merge(config, args):
    pass

def execute_split(config, args):
    pass
    






#
# Interactive menu
#

class BadArguments(Exception):
    """When bad arguments are passed as a menu answer."""
    pass
    
def menu_title(title):
    print title
    print '-' * len(title)
    
def menu(config, state, conf):
    """Run an interactive menu.

    :param config: The initial Config object
    :param state: A dict that holds state for the interactive session
    
    """
    mapping = dict((k, f) for k, d, f in conf)
    print
    for key, desc, func in conf:
        print "  %s. %s" % (key, desc)
    while True:
        ans = raw_input(">>> ").split()
        func = ans[0]
        if func not in mapping:
            print "### Invalid input, use one of:", mapping.keys()
            continue
        print_line()
        state['args'] = ans
        return mapping[func]


def menu_runner(config):
    state = {}

    next_callable = initial_menu
    while True:
        try:
            res = next_callable(config, state)
        except BadArguments as e:
            print "### Bad arguments:", e
            print_line()
            next_callable = initial_menu
            continue
        if res:
            next_callable = res
        else:
            break


def initial_menu(config, state):
    conf = [('a', 'Add an item', menu_add_item),
            ('e', 'Edit an item', menu_edit_item),
            ('f', 'Fetch new items', menu_fetch_items),
            ('r', 'Remove items', menu_remove_items),
            ('c', 'Clear timesheet', menu_clear_items),
            ('m', 'Merge items', menu_merge_items),
            ('q', 'Save and quit', menu_save_quit),
            ('x', 'Exit without saving', None),
            ]
    menu_title("Welcome!")
    config.show_timesheet()
    return menu(config, state, conf)

    
def get_entries_from_timesheet(config, state):
    res = get_indexes_from_timesheet(config, state)
    return [config.timesheet[idx] for idx in res]

def get_indexes_from_timesheet(config, state):
    args = state.get('args')
    if not args:
        raise BadArguments("No answer provided")
    if len(args) == 1:
        raise BadArguments("No entry specified. Please enter one or more numbers from the time sheet listing.")
    res = []
    for arg in args[1:]:
        if not arg.isdigit():
            raise BadArguments("Argument %s is invalid, is not a number" % arg)
        idx = int(arg)
        if len(config.timesheet) < idx:
            raise BadArguments("Entry %s doesn't exist" % idx)
        res.append(idx - 1)
    return res

def menu_save_quit(config, state):
    config.write_back()
    return None

def menu_fetch_items(config, state):
    args = state.get('args')
    plugins = config.plugins_with_support('fetcher')
    if not args:
        print "Use 'fetch' with one of these options:"
        print "  all - All plugins"
        for plugin in plugins:
            print "  %s - %s" % (plugin.short_name, plugin.name)
        return initial_menu
    
    for plugin in plugins:
        print "-> Executing 'fetch' for %s" % plugin.name
        plugin.execute_fetch([])

    return initial_menu

def menu_add_item(config, state):
    date = raw_input("Date: ")
    desc = raw_input("Description: ")
    tag = raw_input("Tag: ")
    unit = raw_input("Unit: ")
    hours = raw_input("Hours: ")
    print_line()
    return initial_menu

def print_line():
    print '-' * 80
    
def menu_edit_item(config, state):
    print "Ok, edited"
    config.timesheet[3].metadata = 'boo, this is a good ticket'
    config.timesheet[7].metadata = 'boo, this is a good ticket'
    print_line()
    return initial_menu

def menu_clear_items(config, state):
    ans = raw_input("You are about to clear all time entries. Confirm [y/n] ")
    if ans in ('y', 'Y', 'yes', 'YES', 'Yes'):
        print "Cleared"
        config.timesheet = []
    else:
        print "Aborted"
    print_line()
    return initial_menu
    
def menu_remove_items(config, state):
    indexes = get_indexes_from_timesheet(config, state)
    indexes.sort()
    remove_count = 0
    for idx in indexes:
        next_idx = idx - remove_count
        print "Removing: %s" % config.timesheet[next_idx].show()
        del config.timesheet[next_idx]
        remove_count += 1
    print_line()
    return initial_menu

def menu_merge_items(config, state):
    indexes = get_indexes_from_timesheet(config, state)
    indexes.sort()
    if len(indexes) != 2:
        raise BadArguments("You can only merge two at a time")
    print "Ok, just merged"
    print_line()
    return initial_menu
    
def menu_2(config, state):
    conf = [('2', "Quit", initial_menu)]
    menu_title("This is menu 2")
    return menu(config, state, conf)
    