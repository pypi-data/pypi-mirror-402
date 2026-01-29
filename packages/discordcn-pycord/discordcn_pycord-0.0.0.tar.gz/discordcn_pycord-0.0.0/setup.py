
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# invalid email
# download url
# url
# project urls

setup(
    name ="discordcn-pycord",
    packages=[".",],
    version='0.0.0',
    description="Reserved for future use by nicebots.xyz. Please contact me@paillat.dev for more information.",
    long_description="""
## Overview
discordcn-pycord is a Python library for doing awesome things.
This name has been reserved using [Reserver](https://github.com/openscilab/reserver).
""",
    long_description_content_type='text/markdown',
    author="Paillat-dev",
    author_email="me@paillat.dev",
    url="https://url.com",
    download_url="https://download_url.com",
    keywords="python3 python reserve reserver reserved",
    project_urls={
            'Source':"https://github.com/nicebots-xyz/discordcn-pycord",
    },
    install_requires="",
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    license="MIT",
)

