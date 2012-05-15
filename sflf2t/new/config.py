# -=- encoding: utf-8 -=-

"""Configuration handler for SFL-F2T files.

Sample file:

config:
  zimbra:
    login: alexandre.bourget
    ics: https://mail.savoirfairelinux.com/home/alexandre.bourget@savoirfairelinux.com/Calendar
  private:
    login: abourget
    url: https://private.savoirfairelinux.com
  redmine:
    login: abourget
    url: https://projects.savoirfairelinux.com

tags:
  vente:
    private:
      push: true
      type: Vente
      client_id: 57
      bh: 768
  udem:
    private:
      push: true
    redmine:
      push: true
      project: udem-futursetudiants
#
# --- REWRITE POINT ---  Anything after this line will be re-written
#
timesheet:
  2012-05-05:
    - h: 3
      tag: vente
      desc: MyEvent et autres choses
    - h: 5
      tag: udem
      unit: #10834 or 10824 or RM10824
      desc: Ticket qu'il y avait à faire

"""

def read_config(filename):
    """Read the config file"""
    
    pass

def write_timesheet(filename, timesheet):
    """Write only the timesheet section, while preserving the
    config and tag sections.
    """
    pass