import os
import sys

from setuptools import setup

if sys.version_info < (3, 5):
    sys.exit("Only Python 3.5 and greater is supported")

setup(
    name='ib_async',
    version="0.0.1",
    packages=['ib_async'],
    url='https://github.com/ondergetekende/ib_async',
    license='Apache License, Version 2.0',
    author='Koert van der Veer',
    author_email='ib_async@ondergetekende.nl',
    description='A asynchronous third party implementation of the Interactive Brokers API',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: AsyncIO",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent,"
        "Topic :: Office/Business :: Financial :: Investment",
    ],
)
