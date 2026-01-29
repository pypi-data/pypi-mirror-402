from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "pypi.md").read_text()

setup(
    name = "runtime_lang",
    version = "0.1.6",
    description = "Interpreter for the RUNTIME programming language",
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    packages = find_packages(),
    install_requires = ["colorama", "platformdirs", "requests"],
    entry_points = {
        'console_scripts': ['runtime=runtime.cli:main'],
    },
    include_package_data = True
)