# -=- encoding: utf-8 -=-

"""Implement the Git searchers, that will populate timesheets, or offer
suggestions based on committed work on different projects in the configured
Git trees.

It will basically run "git log --date today" in the configured repositories,
and present the result, allowing to cross-search the #ticket in other
searchers, to improve metadata.
"""

plugin_name = 'Git'

import os
import subprocess

def searcher(config, args):
    repos = config.get('git.repositories')
    for repo in repos:
        print "=== Checking repo %s" % repo
        path = os.path.expanduser(repo)
        emailproc = subprocess.Popen("cd %s; git config user.email" % path, shell=True, stdout=subprocess.PIPE)
        stdout, stderr = emailproc.communicate()
        email = stdout.strip()
        
        gitlog = subprocess.Popen('cd {0}; git log --pretty=format:"%ae %ai %s" --no-merges --since=2012-05-01 --until=2012-05-14'.format(path), shell=True, stdout=subprocess.PIPE)
        stdout, stderr = gitlog.communicate()
        for line in stdout.split("\n"):
            if line.startswith(email):
                print ' '.join(line.split()[1:])



"""

git config user.email

git log --pretty=format:"%ae  %ai  %s" --no-merges --since=2011-05-01 --until=2012-05-18 | cat


git log --pretty=format:"%ae  %ai  %s" --no-merges --since=2012-05-13 --until=2012-05-14|cat


on enlève ce qui n'est pas de mon e-mail dans ça...

"""