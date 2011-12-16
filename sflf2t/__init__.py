# -=- encoding: utf-8 -=-
import vobject
import yaml
import json
import re
import requests
from itertools import groupby
from getpass import getpass
import calendar
from datetime import *
import sys
import os

#
# Configuration
#

CONFIG_FILE="~/.sflf2t"

if 'SFLF2T' in os.environ:
    CONFIG_FILE=os.environ['SFLF2T']


#
# Program
#


config_file = os.path.realpath(os.path.expanduser(CONFIG_FILE))
config = yaml.load(open(config_file).read())
issues_cache = {}


def get_zimbra_passwd():
    global config
    if 'zimbra_passwd' in config['settings']:
        return config['settings']['zimbra_passwd']
    passwd = getpass('Zimbra password: ')
    config['settings']['zimbra_passwd'] = passwd
    return passwd

def get_ldap_passwd():
    global config
    if 'ldap_passwd' in config['settings']:
        return config['settings']['ldap_passwd']
    passwd = getpass("Enter your 'private' (LDAP) password: ")
    config['settings']['ldap_passwd'] = passwd
    return passwd



class Entry(object):
    def __init__(self, date, hours, cie, type, bh=None, ticket=None,
                 details=None):
        self.date = date
        self.hours = float(hours)
        self.cie = cie
        self.type = unicode(type, 'utf-8')
        self.bh = bh
        self.ticket = ticket
        self._details = details
    
    def __unicode__(self):
        return u"date=%s, hours=%s, details=%s, cie=%s, type=%s, bh=%s, ticket=%s" % (self.date.strftime("%Y-%m-%d").decode('utf-8'), self.hours, self.details, self.cie, self.type, self.bh, self.ticket)

    def __repr__(self):
        return self.__unicode__().encode('utf-8')

    @property
    def no_ticket_details(self):
        return self._details

    @property
    def details(self):
        global issues_cache

        det = self._details
        if self.ticket:
            # Load the project name, cache it
            txt_ticket = str(self.ticket)
            if txt_ticket not in issues_cache:
                r = requests.get('https://projects.savoirfairelinux.com/issues/'+ txt_ticket + '.json', auth=(config['settings']['private_login'], get_ldap_passwd()))
                if r.status_code != 200:
                    raise ValueError("Problem with request fetching Issue, does Issue %s exist? %r" % (txt_ticket, r))
                cnt = json.loads(r.content)
                issues_cache[txt_ticket] = cnt
            project_name = issues_cache[txt_ticket]['issue']['project']['name']
            return project_name + u": RM" + unicode(self.ticket) + ' - ' + det
        return det

class CalFailed(Exception):
    pass

class Cal(object):
    request = None
    status_code = None
    ics = None
    chosen_week = None  # tuple of the dates to check for

    def __init__(self):
        self.events = []
        self.f2t = F2T()
        
    def get_ics(self):
        global config
        passwd = get_zimbra_passwd()
        settings = config['settings']
        if 'ics' not in settings or 'zimbra_login' not in settings:
            raise CalFailed("'zimbra_login' and 'ics' required under 'settings' in config file: %s" % self.f2t.filename)

        self.request = requests.get(settings['ics'],
                                    auth=(settings['zimbra_login'], passwd))
        if self.request.status_code != 200:
            raise CalFailed("Error downloading your ICS file: %s" % r)

        self.ics = vobject.readOne(self.request.content)


    def choose_week_span(self):
        cal = calendar.Calendar()
        today = date.today()
        month_cal = cal.monthdatescalendar(today.year, today.month)
        this_week = [x for x in month_cal if today in x][0][0]
        last_week = this_week - timedelta(7)
        last_last_week = last_week - timedelta(7)
        sel = {'1': this_week,
               '2': last_week,
               '3': last_last_week,
               }
        lab = {1: 'cette semaine',
               2: u'semaine dernière',
               3: 'il y a deux semaines'}

        while True:
            print "Choisir une date:"
            for x in range(1,4):
                print "  %s. Lundi %s (%s)" % (x, sel[str(x)].strftime('%Y-%m-%d'),
                                               lab[x])
            choice = raw_input(">>> ")
            if choice in sel:
                break
            print "Bad choice :)"

        monday = sel[choice]
        monday_time = datetime(monday.year, monday.month, monday.day, 0, 0, 0)
        self.chosen_week = (monday_time, monday_time + timedelta(7, -1))

    def get_chosen_week_events(self):
        week_start, week_end = self.chosen_week
        events = []
        for vevent in self.ics.vevent_list:
            starttz = vevent.dtstart.value
            if type(starttz) is date:
                continue         # Full-day event
            start = starttz.replace(tzinfo=None)
            print start
            if week_start < start and week_end > start:
                events.append(vevent)

        out = []
        for ev in events:
            summary = ev.summary.value
            summary = summary.replace(', f2t', '') \
                             .replace(' f2t', '') \
                             .replace('f2t', '')
            evdate = ev.dtstart.value.date()
            #print "Event: %s" % evdate.strftime("%Y-%m-%d")
            #print "  Summary:", summary
            delta = ev.dtend.value - ev.dtstart.value
            hours = delta.seconds / 3600.0
            #print "  Time:", hours, "hours"
            out.append(Event(summary, evdate, hours))

        self.events = out


    def output_events(self):
        events = self.events
        out = []
        out.append("heures:\n")
        dt = lambda x: x.dtstart
        for day, events in groupby(sorted(events, key=dt), dt):
            out.append("  %s:\n" % (day.strftime("%Y-%m-%d")))
            for ev in events:
                line = "   - %s, %s\n" % (ev.hours, ev.summary)
                out.append(line.encode('utf-8'))
        return ''.join(out)

    def replace_events(self):
        out = self.output_events()
        old_config = open(self.f2t.filename).readlines()

        rewrite = old_config
        for i, line in enumerate(old_config):
            if 'REWRITE POINT' in line:
                rewrite = old_config[:i+1]
                break
        if rewrite == old_config:
            rewrite.append(u'# --- REWRITE POINT --- Anything after this line can be rewritten\n')

        new_config = ''.join(rewrite) + "#\n" + out
        open(self.f2t.filename, 'w').write(new_config)

        return


class Event(object):
    def __init__(self, summary, dtstart, hours):
        self.summary = summary
        self.dtstart = dtstart
        self.hours = hours








types = {
    'achat': "Achats",
    'affectation': "Affectation",
    'consultation': "Affectation",
    'aff': "Affectation",
    'affect': "Affectation",
    'cons': "Affectation",
    'bh': "Banque d'heures",
    'banque': "Banque d'heures",
    'comm': "Communication",
    'com': "Communication",
    'conge': "Congés",
    'ferie': "Férié",
    'finance': "Finances",
    'cours': "Formation",
    'cour': "Formation",
    'formation': "Formation",
    'malade': "Maladie",
    'maladie': "Maladie",
    'p': "Projets",
    'proj': "Projets",
    'projet': "Projets",
    'qual': "Qualité",
    'qualite': "Qualité",
    'retd': "R et D",
    'r&d': "R et D",
    'rd': "R et D",
    'rh': "RH",
    'sup': "Support",
    'support': "Support",
    's': "Support",
    'vente': "Ventes",
    'v': "Ventes",
    }


yaml_line_re = re.compile(r"([\d\.]+)[, ]+([a-zA-Z_-]+)(\#(\d*))?[, ]*(.*)")
def parse_yaml_line(line, defs):
    """Return a tuple in the form: (hours, settings, details)"""

    m = yaml_line_re.search(line)
    if not m:
        raise ValueError("Line '%s' doesn't match our line pattern!\n"
                         "Should look like: '5.0, vente, Some random comments'"%
                         line)
    hours = m.group(1)
    mytype = m.group(2).lower()
    ticket = m.group(4)
    details = m.group(5)

    if not details.strip():
        raise ValueError("No details for line: '%s'" % line)

    if mytype not in defs:
        raise ValueError("Type specified is not in 'defs' section: %s" % mytype)
    mydef = defs[mytype]

    if not ticket:
        ticket = mydef.get('ticket', None)
    if ticket in ("none", "None", "0", "-"):
        ticket = None

    return (hours,
            mydef['cie'],
            types[mydef['type']],
            mydef.get('bh', None),
            ticket,
            details)

class F2T(object):
    def __init__(self):
        global config
        self.data = config
        if 'settings' not in self.data:
            raise CalFailed("'settings' section doesn't exist in '%s'\n"
                            "settings.ics and settings.zimbra_login required" %
                            (config_file))

    def parse(self):
        data = self.data
        sections = ['heures', 'defs', 'settings']
        for sec in sections:
            if sec not in data:
                print "Section '%s' manquante du fichier .yaml" % sec
                sys.exit(1)

        # Get mes types
        defs = data['defs']
        for d in defs:
            val = defs[d]
            if val['type'] not in types:
                raise ValueError("In section 'defs', type=%s is an unknown type" %
                                 val['type'])

        # Check settings
        settings = self.settings = data['settings']
        sections = ['private_id', 'zimbra_login', 'private_login', 'ics']
        for sec in sections:
            if sec not in settings:
                raise ValueError("Missing key: %s in 'settings' section of yaml file." % sec)

        output = []

        # On assume une structure correcte
        heures = data['heures']
        for dt in sorted(heures):
            els = heures[dt]
            for el in els:
                hours, cie, typ, bh, ticket, details = parse_yaml_line(el, defs)
                output.append(Entry(dt, hours, cie, typ, bh, ticket, details))

        self.entries = output
    
    def post_f2t(self):
        global config
        import requests
        passwd = get_ldap_passwd()
        url = "https://private.savoirfairelinux.com/f2t-ym.php"
        print "Using URL:", url
        rmurl =  "https://projects.savoirfairelinux.com/time_entries.json"
        print "Using Redmine URL:", rmurl
        for entry in self.entries:
            
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
            self.req_private = r
            if entry.ticket: # if ticket
                data = {'time_entry': {'comments': entry.no_ticket_details,
                                       'hours': entry.hours,
                                       'issue_id': entry.ticket,
                                       'spent_on': entry.date.strftime("%Y/%m/%d")}}
                print "Posting to REDMINE...", json.dumps(data)
                r2 = requests.post(rmurl, data=json.dumps(data),
                                   headers={"content-type": "application/json"},
                                   auth=(self.settings['private_login'], passwd))
                self.req_redmine = r2

        print "Done"




def main():
    import argparse

    parser = argparse.ArgumentParser(description='SFL-F2T')
    parser.add_argument('--import-ics', action="store_true",
                        default=False,
                        help="Import F2T from your Zimbra Calendar")
    parser.add_argument('--read', action="store_true",
                        default=False,
                        help="Read the f2t.yaml file, to test syntax and "
                             "consistency")
    parser.add_argument('--post', action="store_true",
                        default=False,
                        help="Post your f2t.yaml to Private")

    args = parser.parse_args()

    if args.import_ics:
        try:
            cal = Cal()
            cal.choose_week_span()
            cal.get_ics()
            cal.get_chosen_week_events()
        except CalFailed, e:
            print "ERROR: %s" % e
            sys.exit(1)

        cal.replace_events()

        print "Done"
        sys.exit(0)

    if args.post or args.read:
        f2t = F2T()
        try:
            f2t.parse()
        except ValueError, e:
            print "ERROR:", e
            sys.exit(1)

        print "Entries:"
        for x in f2t.entries:
            print x
        print "Hours:", sum(x.hours for x in f2t.entries)
        print "WARNING: make sure to tweak the DESCRIPTION to private with the PROJECT NAME when adding a ticket"
        print "Reading done."

        if args.post:
            print "Posting to private..."
            f2t.post_f2t()

if __name__ == '__main__':
    main()
