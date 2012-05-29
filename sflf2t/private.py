# -=- encoding: utf-8 -=-

"""Implements the private APIs, for writing timesheets,
searching for client numbers and whatnot.
"""

plugin_name = 'Private'

def submitter_prepare(config, args):
    pass

def submitter_preview(config, args, content):
    print "Private entries:"
    for entry in config.timesheet:
        print " - %r" % entry
    
def submitter_post(config, args, content):
    passwd = config.get_password('private', 'Enter private password:')
    url = config.get('private.f2t_url')
    print "Using Private URL:", url
    for entry in config.timesheet:
        print "Posting entry", entry
        data = {'action': 'ajouter',
                'date': entry.date.strftime("%Y/%m/%d"),
                'create_clientSelect': entry.cie,
                'create_typeSelect': entry.type,
                'details': entry.details,
                'create_banqueSelect': entry.bh or '',
                'nbheures': entry.hours,
                'dimanche': '9999/99/99',
                }
        r = requests.post(url,
                          data=data,
                          params={'idagent': self.settings['private_id'],
                                  'action': 'ajouter'},
                          auth=(self.settings['private_login'], passwd))

def fetcher(config, args):
    pass