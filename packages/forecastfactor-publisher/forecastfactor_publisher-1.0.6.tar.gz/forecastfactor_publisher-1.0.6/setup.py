from setuptools import setup, find_packages

setup(
    name="forecastfactor_publisher",
    version="1.0.6",
    description="A library for publishing forecast data to an API",
    author="Ricardo Teixeira",
    author_email="ricardo.teixeira@obiio.com",
    packages=find_packages(include=["forecastfactor_publisher*"]),
    install_requires=[
        "requests",
        "pandas",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)