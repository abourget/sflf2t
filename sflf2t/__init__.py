# -=- encoding: utf-8 -=-
import vobject
import re
import requests
from itertools import groupby
from getpass import getpass
import calendar
from datetime import *
import sys

def get_ics():
    passwd = getpass('Zimbra password: ')
    r = requests.get('https://mail.savoirfairelinux.com/home/alexandre.bourget@savoirfairelinux.com/Calendar',
                     auth=('alexandre.bourget', passwd))
    if r.status_code != 200:
        print "ERROR downloading your ICS file", r
        sys.exit(1)
    print "Reply: ", r
    ics = vobject.readOne(r.content)
    return ics

def get_week_span():
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
    return (monday_time, monday_time + timedelta(7, -1))

class Event(object):
    def __init__(self, summary, dtstart, hours):
        self.summary = summary
        self.dtstart = dtstart
        self.hours = hours


def get_this_week_events(ics, week_start, week_end):
    events = []
    for vevent in ics.vevent_list:
        starttz = vevent.dtstart.value
        if type(starttz) is date:
            continue         # Full-day event
        start = starttz.replace(tzinfo=None)
        print start
        if week_start < start and week_end > start:
            events.append(vevent)

    out = []
    print "Events:"
    for ev in events:
        summary = ev.summary.value
        summary = summary.replace(', f2t', '') \
                         .replace(' f2t', '') \
                         .replace('f2t', '')
        evdate = ev.dtstart.value.date()
        print "Event: %s" % evdate.strftime("%Y-%m-%d")
        print "  Summary:", summary
        delta = ev.dtend.value - ev.dtstart.value
        hours = delta.seconds / 3600.0
        print "  Time:", hours, "hours"
        out.append(Event(summary, evdate, hours))

    return out







types = {
    'achat': "Achats",
    'affectation': "Affectation",
    'consultation': "Affectation",
    'aff': "Affectation",
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


yaml_line_re = re.compile(r"([\d\.]+)[, ]*([a-z]+)[, ]*(.*)")
def parse_yaml_line(line, defs):
    """Return a tuple in the form: (hours, settings, details)"""

    m = yaml_line_re.search(line)
    if not m:
        raise ValueError("Line '%s' doesn't match our line pattern!\n"
                         "Should look like: '5.0, vente, Some random comments'"%
                         line)
    hours = m.group(1)
    mytype = m.group(2).lower()
    details = m.group(3)
    if mytype not in defs:
        raise ValueError("Type specified is not in 'defs' section: %s" % mytype)
    mydef = defs[mytype]
    return (hours,
            mydef['cie'],
            types[mydef['type']],
            mydef.get('bh', None),
            details)

class F2T(object):
    def __init__(self, filename='f2t.yaml'):
        import yaml
        data = self.data = yaml.load(open(filename).read())
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
                print "Missing key: %s in 'settings' section of yaml file." % sec
                sys.exit(1)

        output = []

        # On assume une structure correcte
        heures = data['heures']
        for dt in sorted(heures):
            els = heures[dt]
            for el in els:
                hours, cie, typ, bh, details = parse_yaml_line(el, defs)
                output.append((dt, hours, cie, typ, bh, details))

        self.entries = output
    
    def post_f2t(self):
        import requests
        passwd = getpass("Enter your 'private' (LDAP) password: ")
        url = "https://private.savoirfairelinux.com/f2t-ym.php"
        print "Using URL:", url
        for entry in self.entries:
            
            print "Posting entry", entry
            data = {'action': 'ajouter',
                    'date': entry[0].strftime("%Y/%m/%d"),
                    'create_clientSelect': entry[2],
                    'create_typeSelect': entry[3],
                    'details': entry[5],
                    'create_banqueSelect': entry[4] or '',
                    'nbheures': entry[1],
                    'dimanche': '9999/99/99',
                    }
            r = requests.post(url,
                              data=data,
                              params={'idagent': self.settings['private_id'],
                                      'action': 'ajouter'},
                              auth=(self.settings['private_login'], passwd))
            self.req = r
        print "Done"

#try:
#    f2t = F2T()
#except ValueError, e:
#    print "ERROR:", e
#    sys.exit(1)
#f2t.post_f2t()


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
        week_start, week_end = get_week_span()
        ics = get_ics()
        events = get_this_week_events(ics, week_start, week_end)

        print "#"
        print "heures:"
        dt = lambda x: x.dtstart
        for day, events in groupby(sorted(events, key=dt), dt):
            print "  %s:" % (day.strftime("%Y-%m-%d"))
            for ev in events:
                print "   - %s, %s" % (ev.hours, ev.summary)

        sys.exit(0)

    if args.post or args.read:
        try:
            f2t = F2T()
        except ValueError, e:
            print "ERROR:", e
            sys.exit(1)

        print "Reading done."

        if args.post:
            print "Posting to private..."
            f2t.post_f2t()

if __name__ == '__main__':
    main()
