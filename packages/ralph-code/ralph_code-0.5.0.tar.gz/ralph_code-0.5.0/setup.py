"""Setup script for ralph-code.

Note: This file is kept for backwards compatibility.
The primary configuration is in pyproject.toml.
"""

from setuptools import setup, find_packages  # type: ignore[import-untyped]

setup(
    name="ralph-code",
    version="0.1.0",
    description="Automated task implementation with Claude Code and Codex",
    author="Ralph Coding",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "ralph": ["schemas/*.json"],
    },
    install_requires=[
        "rich",
        "click",
        "jsonschema",
        "platformdirs",
        "questionary",
    ],
    entry_points={
        "console_scripts": [
            "ralph=ralph.__main__:cli",
        ],
    },
    python_requires=">=3.10",
)
