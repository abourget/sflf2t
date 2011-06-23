import vobject
import requests
from getpass import getpass
import calendar
from datetime import *
import sys

def get_ics():
    passwd = getpass()
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

    while True:
        print "Choisir une date:"
        for x in range(1,4):
            print "  %s. Lundi %s" % (x, sel[str(x)].strftime('%Y-%m-%d'))
        choice = raw_input(">>> ")
        if choice in sel:
            break
        print "Bad choice :)"
    monday = sel[choice]
    monday_time = datetime(monday.year, monday.month, monday.day, 0, 0, 0)
    return (monday_time, monday_time + timedelta(7, -1))


week_start, week_end = get_week_span()
ics = get_ics()


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
