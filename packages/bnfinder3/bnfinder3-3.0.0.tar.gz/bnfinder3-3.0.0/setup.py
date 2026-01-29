#!/usr/bin/env python3

#from distutils.core import setup
from setuptools import setup

setup(name='BNfinder',
      version='3.0.0',
      author='Bartek Wilczynski, Norbert Dojer, Alina Frolova',
      author_email='bartek@mimuw.edu.pl',
      url='http://bioputer.mimuw.edu.pl/software/bnf',
      download_url='https://github.com/sysbio-vo/bnfinder',
      packages=['BNfinder'],
      scripts=['bnf','bnc','bnf-cv'],
      license='GNU GPL v.2',
      description='Bayes Net Finder: an efficient and exact method for learning bayesian networks',
      python_requires='>=3.6',
      install_requires=[
        "scipy",
        "numpy",
   ]
     )
