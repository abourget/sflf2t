# -=- encoding: utf-8 -=-

import dbus
from datetime import datetime, timedelta, date
import pytz

session_bus = dbus.SessionBus()
proxy = session_bus.get_object('org.gnome.Hamster', '/org/gnome/Hamster')

current_timezone = pytz.timezone(open('/etc/timezone').readline().strip())


sections = {
    'vente': "Vente",
    'qualite': "Qualité",
    'bh': "Banque d'heures",
    'banque': "Banque d'heures",
    }
categs = {
  "vente": {cie: 57, type: "vente", bh: False, ticket: False},
  "bep": {cie: 875, type: "bh", bh: 151, ticket: True}
  "qualite": {cie: 57, type: "qualite", bh: False, ticket: False}
  }



class HamsterEntry(object):
    """Model access to the Hamster data and functions to tweak them."""
    def __init__(self, fact):
        self._fact = fact
        self.id = fact[0]
        self.start_time = datetime.utcfromtimestamp(fact[1])
        self.end_time = None
        if fact[2]:
            self.end_time = datetime.utcfromtimestamp(fact[2])
        self.description = fact[3]
        self.activity = fact[4]
        self.activity_id = fact[5]
        self.category = fact[6]
        self.tags = fact[7]
        self.date = datetime.utcfromtimestamp(fact[8]).date()
        self.length = timedelta(0, fact[9])
        
    def __repr__(self):
        return repr(self.__dict__)


class PrivateEntry(object):
    """Model access to the private submission, takes some HamsterEntries"""
    def __init__(self, hamster_entry):
        self._hamster_entry = hamster_entry
        

class RedmineEntry(object):
    """Model access to the Redmine submission, takes some HamsterEntries,
    also does the lookup and resolving of Hamster Entries linked to ticket
    numbers
    """
    def __init__(self, hamster_entry):
        self._hamster_entry = hamster_entry



if __name__ == '__main__':
    cats = proxy.GetCategories()
    todays = proxy.GetTodaysFacts()
        
    entries = [HamsterEntry(f) for f in todays]




#proxy.UpdateFact(5, "bep: +comm allo encore le monde", '', 1327105777, 1327017600, '', '', False)
#proxy.Toggle()

#session_bus.close() 
