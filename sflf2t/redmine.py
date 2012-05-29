# -=- encoding: utf-8 -=-

"""Implement the Redmine searcher methods, as well as the Redmine timesheet
submitter.
"""

plugin_name = 'Redmine'

import requests

def submitter_prepare(config, args):
    pass

def submitter_preview(config, args, content):
    print "REDMINE entries to be Submitted:"
    for entry in config.timesheet:
        rmticket = _get_redmine_unit(entry)
        if rmticket:
            print " - %r" % entry

def _get_redmine_unit(entry):
    if 'unit' not in entry:
        return None
    raw_unit = entry['unit']
    if not raw_unit.startswith(('RM', 'rm')):
        return None
    unit = raw_unit[2:]
    if not unit.isdigit():
        print "WARNING: Redmine unit number isn't numeric: RM%s" % raw_unit
        return None
    return unit
    
def submitter_post(config, args, content):
    passwd = get_ldap_passwd()
    rmurl =  "https://projects.savoirfairelinux.com/time_entries.json"
    print "Using Redmine URL:", rmurl

    for entry in config.timesheet:
        rmticket = _get_redmine_unit(entry)
        if rmticket:
            print "Posting to REDMINERedmine entry", entry
            data = {'time_entry': {'comments': entry['desc'],
                                   'hours': entry['hours'],
                                   'issue_id': rmticket,
                                   'spent_on': entry.date.strftime("%Y/%m/%d")}}
            print "Posting to REDMINE...", json.dumps(data)
            r2 = requests.post(rmurl, data=json.dumps(data),
                               headers={"content-type": "application/json"},
                               auth=(config.get('private.login'), passwd))


def searcher(config, args):
    pass