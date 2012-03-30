# -=- encoding: utf-8 -=-
import requests
import re
import json
import sys
from getpass import getpass

config = {}

def main():
    global config

    ops = {'1': op_tickets_and_sort,
           '2': sys.exit}

    while True:
        print '-' * 32
        print "Operations:"
        print " 1. Show ticket names and sort"
        print " 2. Exit"
        print ""
        op = raw_input(">>> ")
        ops[op]()


def op_tickets_and_sort():
    print "Enter tickets stuff from private (in RM123123 formats) and enter END"
    lines = []
    while True:
        line = raw_input()
        if 'END' in line:
            break
        lines.append(line)

    ticket_reg = re.compile(r"RM(\d*)")
    tickets = ticket_reg.findall("\n".join(lines))
    unique_tickets = sorted(set(tickets))
    tickets_list = []
    for ticket in unique_tickets:
        r = requests.get('https://projects.savoirfairelinux.com/issues/'+ ticket + '.json', auth=(get_ldap_user(), get_ldap_passwd()))
        cnt = json.loads(r.content)
        tickets_list.append(cnt)
    format_ticket_list_1(tickets_list)
    format_ticket_list_2(tickets_list)
    format_ticket_list_3(tickets_list)

def format_ticket_list_1(tickets_list):
    print "Format 1"
    print '-' * 32
    for cnt in tickets_list:
        print "#%s %s (%s)" % (cnt['issue']['id'],
                               cnt['issue']['subject'],
                               cnt['issue']['status']['name'])
    print ""

def format_ticket_list_2(tickets_list):
    print "Format 2"
    print '-' * 32
    for cnt in tickets_list:
        print "#%s %s" % (cnt['issue']['id'],
                          cnt['issue']['subject'])
    print ""

def format_ticket_list_3(tickets_list):
    print "Format 3"
    print '-' * 32
    for cnt in tickets_list:
        print cnt
    print ""

def get_ldap_passwd():
    global config
    if 'ldap_passwd' not in config:
        config['ldap_passwd'] = getpass("Enter 'private' (LDAP) password: ")
    return config['ldap_passwd']

def get_ldap_user():
    global config
    if 'ldap_user' not in config:
        config['ldap_user'] = raw_input("Enter 'private' (LDAP) username: ")
    return config['ldap_user']



if __name__ == '__main__':
    main()
