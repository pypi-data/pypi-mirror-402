# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

_requirements = {
    "base": ["marshmallow_dataclass==8.3.2", "marshmallow-enum==1.5.1"],
    "datastore": ["google-cloud-firestore==2.4.0"],
    "faasjob": ["psutil>=5.8.0"],  # Memory tracking for telemetric reporter
}


def _join_arrays(*args):
    out = []
    for arg in args[0]:
        out += arg
    return out


setup(
    name="faaspectre",
    version="0.0.1",
    description="FaaS Telemetric Reporter - Job Execution Metrics Library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Iván Huerta",
    author_email="ivan.huerta.h@gmail.com",
    license="Unlicense",
    url="https://github.com/yourusername/faaspectre",  # Update with your actual repo URL
    packages=find_packages(exclude=["tests", "tests.*", "docs", "docs.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: Public Domain",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
    ],
    extras_require={
        "all": _join_arrays(_requirements.values()),
        "faasjob": _requirements["base"]
        + _requirements["datastore"]
        + _requirements["faasjob"],
        "datastore": _requirements["base"] + _requirements["datastore"],
    },
    zip_safe=False,
    python_requires=">=3.8",
    keywords="faas serverless metrics telemetry firestore google-cloud monitoring",
)
