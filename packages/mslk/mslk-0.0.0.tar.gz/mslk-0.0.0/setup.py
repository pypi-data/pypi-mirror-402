from setuptools import setup, find_packages

setup(
    name="mslk", # Make sure this name is unique on PyPI
    version="0.0.0",
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    # Add other required metadata like author, description, etc.
)
