SFL-F2T
=======

This is a project to streamline time sheet entries, it is modular, supports fetchers (to pull
time sheet infos from a iCal calendar, from Hamster (eventually), from your work in Git
repositories, from your sent mails on your IMAP server), submitters to post your time sheets
to our own (Savoir-faire Linux's) time tracking software, to push your time sheets to Redmine,
and eventually some other time trackers.

For now, this is mainly an internal tool, but was designed to be extended through entry
points and module spread into different packages, so you don't need to install what you don't
need to use.

The simplest use goes like this:

* Copy the provided sample.conf to your disk as: ~/.sflf2t
  (take it here: https://raw.github.com/abourget/sflf2t/master/sample.conf )

Install from PyPI:

  pip install sflf2t

or from up here:

  pip install https://github.com/abourget/sflf2t/zipball/master

and run it:

  sflf2t --help


Main functions
--------------

  sflf2t edit: allows you to edit the source file

  sflf2t add: gives you a pseudo-interactive shell right now.. this will certainly change :)

  sflf2t fetch: fetches from your different sources (zimbra for now, more to come)

  sflf2t preview: previews the submissions (to private, redmine)

  sflf2t submit: previews and submits your timesheet

