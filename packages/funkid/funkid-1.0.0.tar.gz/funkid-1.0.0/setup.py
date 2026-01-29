from setuptools import setup, find_packages

setup(
    name="funkid",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "funkid = funkid.app:main"
        ]
    },
    description="A fun command line app for kids",
    author="Your Name",
)
