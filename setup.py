#!/usr/bin/env python
import setuptools

setuptools.setup(
    name="sip_parser",
    version="0.1",
    package_dir={"": "src"},
    packages=setuptools.find_namespace_packages(where="src"),
)
