from setuptools import setup, find_packages
import codecs
import os

with open("README.md", encoding="utf-8") as f:
  LONG_DESCRIPTION = f.read()

VERSION = '0.0.2'
DESCRIPTION = 'Python project on TOPSIS'

setup(
  name = "topsis-ritwik-102303905",
  version = VERSION,
  author = "Ritwik Bhandari",
  author_email = "rbhandari_be23@thapar.edu",
  description = DESCRIPTION,
  long_description = LONG_DESCRIPTION,
  long_description_content_type="text/markdown",
  packages = find_packages(),
  install_requires = [],
  keywords = ['python', 'topsis', 'data ranking', 'numpy']
)
