from pathlib import Path

from setuptools import setup
import os

with open(os.path.join(Path(__file__).resolve().parent, 'simple_alto_parser/VERSION')) as version_file:
    version = version_file.read().strip()

setup(version=version)
