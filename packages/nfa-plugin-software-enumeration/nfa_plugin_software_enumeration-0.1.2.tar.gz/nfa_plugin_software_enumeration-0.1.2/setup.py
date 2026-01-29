import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nfa-plugin-software-enumeration",
    version="0.1.2",
    author="Damian Krawczyk",
    author_email="damian.krawczyk@limberduck.org",
    description="Software Enumeration report plugin for LimberDuck NFA (nessus file analyzer)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://limberduck.org/en/latest/tools/nessus-file-analyzer/advanced-reports/software-enumeration/",
    packages=setuptools.find_packages(),
    install_requires=[
        "nessus-file-analyzer>=0.12.0",
    ],
    entry_points={
        "nfa.plugins": [
            "software_enumeration = nfa_plugin_software_enumeration.software_enumeration:SoftwareEnumerationPlugin",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
    ],
    python_requires=">=3.10",
)
