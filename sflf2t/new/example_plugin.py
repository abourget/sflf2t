# -=- encoding: utf-8 -=-

"""Implement an Example plugin with the different methods
"""

plugin_name = 'Example'

def submitter_prepare(config):
    pass

def submitter_review(content):
    pass

def submitter_post(content):
    pass

def fetcher(config):
    pass
    
def searcher(config, timesheet_entry):
    pass

def add_subcommand_fetch(parser):
    pass

def add_subcommand_preview(parser):
    pass

def add_subcommand_submit(parser):
    pass
    