# -=- encoding: utf-8 -=-
# Author: Alexandre Bourget <alexandre.bourget@savoirfairelinux.com>
# Copyright 2012 (c) Savoir-faire Linux inc.

import mechanize
import getpass
import lxml.html
import sys
import os
import re

def get_lxml(b):
    """Return the root node, using LXML of the current browser response."""
    return lxml.html.fromstring(b.response().read())

def browserview(b):
    open('/tmp/boo.html', 'w').write(b.response().read())
    os.system("google-chrome /tmp/boo.html")

def select_by_regexp(b, fieldname, exp):
    """Select, in a select box, with just a regexp instead of the full
    string.  Also, do that on the label."""
    regexp = re.compile(exp)
    elements = b.form.possible_items(fieldname, by_label=True)
    for element in elements:
        if regexp.match(element):
            b.form.set_value([element], fieldname, by_label=True)
            
b = mechanize.Browser()
b.add_password('private.savoirfairelinux.com', 'abourget',
               getpass.getpass('Password:'))

b.open("https://private.savoirfairelinux.com/interventions.php")
b.select_form('listing')
b.form.toggle_single('facturer')
select_by_regexp(b, 'choix', 'ASEQ')
b.submit()
table = get_lxml(b).cssselect('table')[0]
for tr in table.cssselect('tr'):
    desc = tr.getchildren()[4].text_content()
    print desc
browserview(b)


sys.exit()






b.open('https://private.savoirfairelinux.com/f2t-recherche.php')
#b.follow_link(text_regex=r"Recherche f2t", nr=0)

# Select default form.
b.select_form(nr=0)
#b['interval_debut'] = '2012/03/01'
#b['interval_debut'] = '2012/03/01'
b.form.set_value(['ASEQ'] ,'compagnie', by_label=True)
b.submit()
table = get_lxml(b).cssselect('table')[0]
for tr in table.cssselect('tr'):
    desc = tr.getchildren()[4].text_content()
    print desc
