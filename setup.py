from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Read __version__
with open(path.join(here, "ukrainian_word_stress", "version.py")) as f:
    exec(f.read())

setup(
    name="ukrainian_word_stress",
    # Versions should comply with PEP440. For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=__version__,
    description="Find word stress for texts in Ukrainian",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lang-uk/ukrainian-word-stress",
    author='Oleksiy Syvokon',
    author_email='oleksiy.syvokon@gmail.com',
    license="MIT",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="ukrainian nlp word stress accents dictionary linguistics",
    packages=find_packages(exclude=["docs", "tests"]),
    package_data={
        "ukrainian_word_stress": [
            "data/stress.trie",
        ]
    },
    include_package_data=True,
    install_requires=[
        "stanza",
        "marisa-trie",
    ],
    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={"test": ["pytest", "coverage"],
                    "dev": ["tqdm", "ua-gec"]},
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={"console_scripts": ["ukrainian-word-stress=ukrainian_word_stress.cli:main"]},

)
