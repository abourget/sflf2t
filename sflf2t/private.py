# -=- encoding: utf-8 -=-

"""Implements the private APIs, for writing timesheets,
searching for client numbers and whatnot.
"""

plugin_name = 'Private'

import sys
from pprint import pprint
import requests

types = {
    'achat': "Achats",
    'affectation': "Affectation",
    'bh': "Banque d'heures",
    'comm': "Communication",
    'conge': "Congés",
    'ferie': "Férié",
    'finances': "Finances",
    'formation': "Formation",
    'maladie': "Maladie",
    'projet': "Projets",
    'qualite': "Qualité",
    'retd': "R et D",
    'rh': "RH",
    'support': "Support",
    'vente': "Ventes",
    }



def submitter_prepare(config, args):
    entries = []
    total_hours = 0
    for entry in config.timesheet:
        print "Populating entries entry", entry
        private_type = config.get_cascade('private.type', entry)
        if not private_type:
            raise ValueError("Couldn't get the type of private submission. Missing or invalid tag ? %r" % entry)
        private_type = private_type.lower()
        corresp_type = types.get(private_type)
        if not corresp_type:
            raise ValueError("Le type '%s' n'est pas un type Private valide (%r) " % (private_type, entry))

        banque_heure = config.get_cascade('private.bh', entry)
        if banque_heure and not private_type == 'bh' or \
           private_type == 'bh' and not banque_heure:
            raise ValueError("Type 'bh' only valid with a specified 'private.bh' on tag: %r" % entry)
        data = {'action': 'ajouter',
                'date': entry['date'].strftime("%Y/%m/%d"),
                'create_clientSelect': config.get_cascade('private.client_id',
                                                          entry),
                'create_typeSelect': corresp_type,
                'details': entry.get('desc') or '',
                'create_banqueSelect': config.get_cascade('private.bh', entry) or '',
                'nbheures': entry['hours'],
                'dimanche': '9999/99/99',
                }
        total_hours += entry['hours']
        entries.append(data)
    return {'entries': entries,
            'total': total_hours}

def submitter_preview(config, args, content):
    print "Private entries:"
    pprint(content['entries'])
    print "Total hours", content['total']
    
def submitter_post(config, args, content):
    passwd = config.get_password('private', 'Enter private password:')
    url = config.get('private.f2t_url')
    agent_id = config.get('private.agent_id')
    login = config.get('private.login')
    print "Using Private URL, login and agent_id:", url, login, agent_id
    
    for data in content['entries']:
        print "Posting entry", data['details'],
        r = requests.post(url, data=data,
                          params={'idagent': agent_id,
                                  'action': 'ajouter'},
                          auth=(login, passwd))
        print r
        if '</html>' not in r.content:
            print r.content
            print "ERROR while submitting, see previous private error"
            sys.exit(1)
            

def fetcher(config, args):
    pass