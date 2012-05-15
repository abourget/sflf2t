# -=- encoding: utf-8 -=-

"""Implement the Zimbra fetcher, for ICS and transform into a timesheet."""

from sflf2t.new.config import TimeEntry

plugin_name = 'Zimbra Calendar'

def fetcher(config):
    cal = Cal()
    cal.choose_week_span()
    cal.get_ics()
    cal.get_chosen_week_events()

    pass





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
            raise CalFailed("'zimbra_login' and 'ics' required under 'settings' in config file: %s" % config_file)

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
            tag_desc = [el.strip() for el in summary.split(',', 1)]
            tag = tag_desc[0]
            desc = None if len(tag_desc) == 1 else tag_desc[1]
            out.append(TimeEntry(date=evdate, hours=hours, tag=tag, desc=desc))

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
        old_config = open(config_file).readlines()

        rewrite = old_config
        for i, line in enumerate(old_config):
            if 'REWRITE POINT' in line:
                rewrite = old_config[:i+1]
                break
        if rewrite == old_config:
            rewrite.append(u'# --- REWRITE POINT --- Anything after this line can be rewritten\n')

        new_config = ''.join(rewrite) + "#\n" + out
        open(config_file, 'w').write(new_config)

        return