import os
import sys

from setuptools import setup, find_packages

#here = os.path.abspath(os.path.dirname(__file__))
#README = open(os.path.join(here, 'README.txt')).read()
#CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    #  install with pip install -r requirements.freeze
    ]

setup(name='SFLF2T',
      version='0.1',
      description='SFL - Outil de gestion des feuilles de temps - Private',
      #long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        ],
      author='Alexandre Bourget',
      author_email='alexandre.bourget@savoirfairelinux.com',
      url='',
      keywords='web sfl private',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='sflf2t',
      install_requires = requires,
      entry_points = """\
      """,
      )

