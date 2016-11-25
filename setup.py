import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name = "cit",
    version = "0.0.1",
    author = "Oguz Albayrak",
    author_email = "oguzalba@gmail.com",
    description = ("A demonstration of how git can be implemented with python"),
    license = "BSD",
    scripts=['bin/cit'],
    keywords = "example documentation tutorial",
    url = "",
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 1 - Alpha",
        "Topic :: Software Development :: Version Control",
        "License :: OSI Approved :: BSD License",
    ],
    packages=['citlib', 'citlib.commands']
)
