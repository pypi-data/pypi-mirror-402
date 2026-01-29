# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="landing_cloner",
    version="1.1.0",
    author="OneManArmy",
    author_email="mister228orange@gmail.com",
    description="Create Flask apps from web pages or local HTML files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mister228orange/landing_cloner",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "click>=8.0.0",
        # Add other dependencies from your utils/url2file modules
    ],
    entry_points={
        "console_scripts": [
            "landing_cloner=landing_cloner.cli:cli",
        ],
    },
)
