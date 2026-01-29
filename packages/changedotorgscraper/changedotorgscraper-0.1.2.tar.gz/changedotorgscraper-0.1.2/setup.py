from setuptools import setup, find_packages
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(here, "README.md")
with codecs.open(readme_path, encoding="utf-8") as fh:
    long_description = fh.read()

VERSION = "0.1.2"
DESCRIPTION = 'Scrapes online petition data from change.org'
LONG_DESCRIPTION = 'A package that scrapes online petition data from change.org, including the title, description, target audience, signature count, creator name, date created, location created, and victory status. Works by simply providing the url of the change.org petition search.'

setup(
    name="changedotorgscraper",
    version=VERSION,
    author="Charles Alba",
    author_email="alba@wustl.edu",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    install_requires=[
        "requests",
        "beautifulsoup4",
        "lxml",
        "tqdm",
        "pandas",
        "selenium",
        "webdriver-manager",
    ],
    license="MIT",
    keywords=["change.org", "petitions", "web scraping", "selenium", "beautifulsoup"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.8",
)











