from setuptools import setup, find_packages

setup(
    name="magnato-calc",
    version="0.1.0",
    author= "Neeraj Kr",
    author_email= "magnato1997@gmail.com",
    description="a simple calculator have multi options",
    long_description=open("README.md","r", encoding ="utf-8").read(),
    long_description_content_type="text/markdown",
    packages = find_packages(),
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "magnato = magnato.calculator:main",],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)