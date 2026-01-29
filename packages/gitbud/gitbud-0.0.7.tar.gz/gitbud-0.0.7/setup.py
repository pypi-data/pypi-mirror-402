from setuptools import setup, find_packages

setup(
    name="gitbud",
    version="0.0.7",
    packages=find_packages(),
    install_requires=[
        "GitPython",
    ],
    long_description="A toolkit of helper functions for git-driven development.",
)
