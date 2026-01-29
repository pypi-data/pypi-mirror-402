from setuptools import setup, find_packages

setup(
    name="casemaster-py", # PyPI-da tapılacaq ad
    version="0.1.0",
    packages=find_packages(),
    author="Eldar",
    description="Professional string case conversion library",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)