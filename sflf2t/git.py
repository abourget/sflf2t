# -=- encoding: utf-8 -=-

"""Implement the Git searchers, that will populate timesheets, or offer
suggestions based on committed work on different projects in the configured
Git trees.

It will basically run "git log --date today" in the configured repositories,
and present the result, allowing to cross-search the #ticket in other
searchers, to improve metadata.
"""

plugin_name = 'Git'

def searcher(config, timesheet_element):
    pass