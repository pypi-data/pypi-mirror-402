"""
Setup configuration for Advanced Speedtest CLI
Enables installation via pip and publication to PyPI
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements from requirements.txt
requirements = (this_directory / "requirements.txt").read_text(encoding="utf-8").strip().split('\n')
requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="adv-speedtest-cli",
    version="1.0.0",
    author="Shakil Ahmed",
    author_email="shakilofficial0@gmail.com",
    description="A sophisticated cross-platform command-line utility for measuring internet speed with precision",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shakilofficial0/adv-speedtest-cli",
    project_urls={
        "Bug Tracker": "https://github.com/shakilofficial0/adv-speedtest-cli/issues",
        "Documentation": "https://github.com/shakilofficial0/adv-speedtest-cli#readme",
        "Source Code": "https://github.com/shakilofficial0/adv-speedtest-cli",
    },
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*"]),
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: System :: Networking",
        "Topic :: Utilities",
        "Development Status :: 5 - Production/Stable",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "adv-speedtest-cli=advanced_speedtest_cli.__main__:main",
            "advanced-speedtest=advanced_speedtest_cli.__main__:main",
            "speedtest-cli=advanced_speedtest_cli.__main__:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "speedtest",
        "internet speed",
        "bandwidth",
        "network",
        "cli",
        "command-line",
        "utility",
        "speed measurement",
        "download upload ping",
        "network diagnostics"
    ],
)
