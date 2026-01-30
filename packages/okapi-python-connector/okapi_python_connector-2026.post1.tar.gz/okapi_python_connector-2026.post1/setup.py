from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="okapi-python-connector",
    version="2026-01",
    author="OKAPI Orbits",
    author_email="devops@okapiorbits.com",
    description="Package to connect to OKAPI API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/OKAPIOrbits/OkapiPythonConnector",
    packages=find_packages(),
    install_requires=[
        'requests'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)


