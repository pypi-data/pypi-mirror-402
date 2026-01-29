#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os

from setuptools import find_packages, setup

# Package meta-data - CUSTOMIZE THESE VALUES
NAME = "poridhiweb"  # Make this unique!
DESCRIPTION = "PoridhiFrame Python Web Framework built for learning purposes."
EMAIL = "dipanjalmaitra@gmail.com"  # Your email
AUTHOR = "Dipanjal Maitra"  # Your name
REQUIRES_PYTHON = ">=3.6.0"
VERSION = "0.0.5"

# Framework dependencies
REQUIRED = [
    "Jinja2==3.1.6",
    "parse==1.20.2",
    "WebOb==1.8.9",
    "whitenoise==6.11.0",
]

# Advanced setup configuration - Don't modify unless you understand it
here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description
try:
    with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = "\n" + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# Load version information
about = {}
if not VERSION:
    project_slug = NAME.lower().replace("-", "_").replace(" ", "_")
    with open(os.path.join(here, project_slug, "__version__.py")) as f:
        exec(f.read(), about)
else:
    about["__version__"] = VERSION

# Main setup configuration
setup(
    name=NAME,
    version=about["__version__"],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    packages=find_packages(exclude=["tests", "demo_app"]),
    install_requires=REQUIRED,
    include_package_data=True,
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    setup_requires=["wheel"],
)
