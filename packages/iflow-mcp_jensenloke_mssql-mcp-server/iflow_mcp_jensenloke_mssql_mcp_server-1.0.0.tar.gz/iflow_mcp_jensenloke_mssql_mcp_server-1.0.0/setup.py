#!/usr/bin/env python3
"""
Setup script for MSSQL MCP Server
"""

import os
from setuptools import setup, find_packages

# Get the directory where this setup.py is located
here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open(os.path.join(here, "requirements.txt"), "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="iflow-mcp_jensenloke_mssql-mcp-server",
    version="1.0.0",
    author="MSSQL MCP Server",
    author_email="",
    description="A Model Context Protocol server for Microsoft SQL Server databases",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/mssql-mcp-server",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mssql-mcp-server=src.server:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)